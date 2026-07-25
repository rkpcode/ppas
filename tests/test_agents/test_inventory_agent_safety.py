import inspect
from app.agents.inventory_agent import tools

def test_no_write_tools():
    """
    Ensures that no tool with write-semantics exists in the tools.py module.
    """
    blocklist = ["update", "add", "delete", "commit", "create", "write", "set", "remove"]
    
    # Get all functions defined in the tools module
    functions = [name for name, obj in inspect.getmembers(tools) if inspect.isfunction(obj) or hasattr(obj, "invoke")]
    
    for func_name in functions:
        func_name_lower = func_name.lower()
        for blocked_word in blocklist:
            assert blocked_word not in func_name_lower, f"Safety Violation: Function '{func_name}' contains blocked word '{blocked_word}'"
