"""
This module provides accessibility to all injectable JavaScript
defined in the package data.
"""
from seproxer import resources


console_error_detection = resources.get_javascript_resource(
    name="Console Error Detection",
    resource_path="injectables/error_detection.js",
)
