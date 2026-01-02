# Fusion 360 API Configuration
# 
# This file maintains backward compatibility by importing from the new
# centralized configuration manager in core.config

from core.config import (
    get_base_url,
    get_endpoints,
    get_headers,
    get_timeout,
    validate_configuration,
    get_categories
)

# Legacy compatibility - expose the old interface
BASE_URL = get_base_url()
ENDPOINTS = get_endpoints()  # All endpoints flattened
HEADERS = get_headers()
REQUEST_TIMEOUT = get_timeout()
