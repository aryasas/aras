import pytest
from core.logic import discovery
import os
import re

# gemini-flash

def test_no_print_in_discovery_file():
    """
    Statically check discovery.py file content to ensure no print() calls exist.
    """
    file_path = discovery.__file__
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check for print( calls that are not in comments
    matches = re.findall(r"^\s*print\(", content, re.MULTILINE)
    assert not matches, f"Found print() calls in {file_path}: {matches}"

def test_discovery_functions_use_logging_not_print(capsys):
    """
    Verify that discovery functions do not output to stdout/stderr using capsys.
    """
    # Trigger an error in load_class that would have previously printed
    discovery.load_class("non_existent_module.NonExistentClass")
    
    captured = capsys.readouterr()
    assert captured.out == "", "Should not print to stdout"
    
    # Let's also check discover_apps with a non-existent path
    discovery.discover_apps("invalid_apps_path")
    captured = capsys.readouterr()
    assert captured.out == "", "discover_apps should not print to stdout"
