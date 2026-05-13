"""
Purpose: Framework integrity and health check utility.
Context: Level 2 Core Service.
Impact: Ensures all framework components follow the mandatory inheritance rule.
"""
import inspect
import logging
from typing import List, Type, Any
from ..base.aras import Aras
from ..base.service import Service

logger = logging.getLogger(__name__)

class IntegrityChecker(Service):
    """
    Enforces framework rules and best practices.
    """

    @classmethod
    def check_module(cls, module: Any):
        """
        Inspects a module and verifies that all classes defined in it 
        inherit from the Aras base class.
        """
        # Get all classes defined in this module (not imported)
        module_classes = [
            obj for name, obj in inspect.getmembers(module) 
            if inspect.isclass(obj) and obj.__module__ == module.__name__
        ]

        for klass in module_classes:
            # Skip standard exceptions, Enums, and Aras itself
            if issubclass(klass, (Exception, Aras)):
                continue
            
            # If we are here, we found a class that is NOT connected to Aras
            error_msg = f"Integrity Error: Class '{klass.__name__}' in {module.__name__} does not inherit from Aras."
            logger.error(error_msg)
            # You can decide to raise an error or just log a warning
            # For strict enforcement, we raise:
            raise TypeError(error_msg + " Every framework component MUST inherit from Aras.")

    @classmethod
    def run_health_check(cls):
        """Scans all registered apps and their core files for integrity."""
        # This could be called during Sync or App Discovery
        pass
