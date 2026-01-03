# Handler modules for the modular Fusion 360 Add-In system
# This package contains all HTTP request handler modules organized by Fusion 360 workspace categories

from .system import lifecycle
from .design import geometry, sketching, modeling, features, utilities
from . import manufacture  # Import manufacture handlers to register with router

__all__ = [
    'lifecycle',
    'geometry', 'sketching', 'modeling', 'features', 'utilities',
    'manufacture'
]