"""
This module provides accessibility to all injectable JavaScript
defined in the package data.
"""
from seproxer import resources


console_error_detection = resources.Resource(
    name="Console Error Detection",
    content=resources.get_javascript_resource("injectables/error_detection.js")
)
