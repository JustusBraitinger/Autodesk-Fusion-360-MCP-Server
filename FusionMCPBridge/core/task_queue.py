# Centralized Task Queue System
# Thread-safe task queue and processor for Fusion 360 API calls respecting threading constraints

import queue
import threading
import json
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .error_handling import error_handler, ErrorCategory, ErrorSeverity, handle_task_error

# Set up module-specific logging
module_logger = error_handler.get_module_logger("core.task_queue")

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """Task model for queue processing"""
    task_type: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    priority: TaskPriority
    timestamp: float
    module_context: str
    callback: Optional[Callable] = None

class TaskQueue:
    """
    Centralized task queue system for thread-safe Fusion 360 API calls.
    Respects Fusion 360's threading constraints by processing all API calls on the main UI thread.
    """
    
    def __init__(self):
        """Initialize the task queue system"""
        self.task_queue = queue.PriorityQueue()
        self.task_handlers: Dict[str, Callable] = {}
        self.processing = False
        self.stats = {
            'tasks_queued': 0,
            'tasks_processed': 0,
            'tasks_failed': 0,
            'last_process_time': None
        }
        self._lock = threading.Lock()
    
    def register_task_handler(self, task_type: str, handler: Callable) -> None:
        """
        Register a task handler for a specific task type with error handling
        
        Args:
            task_type: Type of task (e.g., 'draw_box', 'extrude_sketch')
            handler: Function to handle the task
        """
        try:
            with self._lock:
                self.task_handlers[task_type] = handler
                module_logger.debug(f"Registered task handler for: {task_type}")
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.task_queue",
                function_name="register_task_handler",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.MEDIUM,
                additional_info={"task_type": task_type}
            )
            module_logger.error(f"Task handler registration failed: {error_response.message}")
    
    def queue_task(self, task_type: str, *args, priority: TaskPriority = TaskPriority.NORMAL, 
                   module_context: str = "unknown", callback: Optional[Callable] = None, **kwargs) -> None:
        """
        Queue a task for execution on the main thread with error handling
        
        Args:
            task_type: Type of task to execute
            *args: Positional arguments for the task
            priority: Task priority level
            module_context: Module that queued the task (for debugging)
            callback: Optional callback function to call after task completion
            **kwargs: Keyword arguments for the task
        """
        try:
            task = Task(
                task_type=task_type,
                args=args,
                kwargs=kwargs,
                priority=priority,
                timestamp=time.time(),
                module_context=module_context,
                callback=callback
            )
            
            # Use priority value for queue ordering (lower number = higher priority)
            priority_value = (4 - priority.value, task.timestamp)
            
            self.task_queue.put((priority_value, task))
            
            with self._lock:
                self.stats['tasks_queued'] += 1
            
            module_logger.debug(f"Queued task: {task_type} from {module_context} with priority {priority.name}")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.task_queue",
                function_name="queue_task",
                category=ErrorCategory.TASK_EXECUTION,
                severity=ErrorSeverity.MEDIUM,
                additional_info={"task_type": task_type, "module_context": module_context}
            )
            module_logger.error(f"Task queuing failed: {error_response.message}")
    
    def process_tasks(self) -> int:
        """
        Process all queued tasks on the main thread with comprehensive error handling.
        This method should be called from Fusion 360's main UI thread.
        
        Returns:
            Number of tasks processed
        """
        if self.processing:
            module_logger.warning("Task processing already in progress")
            return 0
        
        self.processing = True
        processed_count = 0
        failed_tasks = []
        
        try:
            with self._lock:
                self.stats['last_process_time'] = time.time()
            
            # Process all available tasks
            while not self.task_queue.empty():
                try:
                    # Get task with timeout to avoid blocking
                    priority_value, task = self.task_queue.get_nowait()
                    
                    # Execute the task with error isolation
                    success = self._execute_task(task)
                    
                    if success:
                        with self._lock:
                            self.stats['tasks_processed'] += 1
                        processed_count += 1
                    else:
                        with self._lock:
                            self.stats['tasks_failed'] += 1
                        failed_tasks.append(task)
                    
                    # Call callback if provided
                    if task.callback:
                        try:
                            task.callback(success, task)
                        except Exception as e:
                            error_response = error_handler.handle_error(
                                error=e,
                                module_name=task.module_context,
                                function_name="task_callback",
                                category=ErrorCategory.TASK_EXECUTION,
                                severity=ErrorSeverity.LOW,
                                additional_info={"task_type": task.task_type}
                            )
                            module_logger.error(f"Task callback failed: {error_response.message}")
                    
                except queue.Empty:
                    break
                except Exception as e:
                    error_response = error_handler.handle_error(
                        error=e,
                        module_name="core.task_queue",
                        function_name="process_tasks",
                        category=ErrorCategory.TASK_EXECUTION,
                        severity=ErrorSeverity.HIGH
                    )
                    module_logger.error(f"Error processing task: {error_response.message}")
                    with self._lock:
                        self.stats['tasks_failed'] += 1
        
        finally:
            self.processing = False
        
        if processed_count > 0:
            module_logger.debug(f"Processed {processed_count} tasks")
        
        if failed_tasks:
            module_logger.warning(f"{len(failed_tasks)} tasks failed during processing")
        
        return processed_count
    
    def _execute_task(self, task: Task) -> bool:
        """
        Execute a single task with comprehensive error handling and isolation
        
        Args:
            task: Task to execute
            
        Returns:
            True if task executed successfully, False otherwise
        """
        try:
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                error_response = error_handler.handle_error(
                    error=ValueError(f"No handler registered for task type: {task.task_type}"),
                    module_name=task.module_context,
                    function_name="execute_task",
                    category=ErrorCategory.TASK_EXECUTION,
                    severity=ErrorSeverity.HIGH,
                    additional_info={"task_type": task.task_type}
                )
                module_logger.error(f"No handler registered for task type: {task.task_type}")
                return False
            
            # Execute the handler with task arguments
            result = handler(*task.args, **task.kwargs)
            
            module_logger.debug(f"Successfully executed task: {task.task_type} from {task.module_context}")
            return True
            
        except Exception as e:
            error_response = handle_task_error(e, task.task_type, task.module_context)
            module_logger.error(f"Task execution failed: {task.task_type} from {task.module_context}: {error_response.message}")
            return False
    
    def get_queue_size(self) -> int:
        """
        Get current queue size
        
        Returns:
            Number of tasks in queue
        """
        return self.task_queue.qsize()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get task queue statistics
        
        Returns:
            Dictionary with queue statistics
        """
        with self._lock:
            return self.stats.copy()
    
    def clear_queue(self) -> int:
        """
        Clear all tasks from the queue with logging
        
        Returns:
            Number of tasks that were cleared
        """
        cleared_count = 0
        
        try:
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                    cleared_count += 1
                except queue.Empty:
                    break
            
            module_logger.info(f"Cleared {cleared_count} tasks from queue")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.task_queue",
                function_name="clear_queue",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM
            )
            module_logger.error(f"Queue clearing failed: {error_response.message}")
        
        return cleared_count
    
    def get_registered_handlers(self) -> List[str]:
        """
        Get list of registered task handler types
        
        Returns:
            List of task type names
        """
        with self._lock:
            return list(self.task_handlers.keys())
    
    def is_handler_registered(self, task_type: str) -> bool:
        """
        Check if a handler is registered for a task type
        
        Args:
            task_type: Task type to check
            
        Returns:
            True if handler is registered, False otherwise
        """
        return task_type in self.task_handlers

class TaskEventHandler:
    """
    Custom Event Handler for processing tasks from the queue.
    This integrates with Fusion 360's event system to process tasks on the main thread.
    """
    
    def __init__(self, task_queue: TaskQueue):
        """
        Initialize the task event handler
        
        Args:
            task_queue: TaskQueue instance to process
        """
        self.task_queue = task_queue
        self.last_process_time = 0
        self.process_interval = 0.2  # Process every 200ms
    
    def notify(self, args):
        """
        Handle custom event notification from Fusion 360 with error handling
        
        Args:
            args: Event arguments from Fusion 360
        """
        try:
            current_time = time.time()
            
            # Throttle processing to avoid overwhelming the system
            if current_time - self.last_process_time < self.process_interval:
                return
            
            self.last_process_time = current_time
            
            # Process queued tasks
            processed = self.task_queue.process_tasks()
            
            if processed > 0:
                module_logger.debug(f"Event handler processed {processed} tasks")
                
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.task_queue",
                function_name="notify",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH
            )
            module_logger.error(f"Task event handler error: {error_response.message}")

# Global task queue instance
task_queue = TaskQueue()