# src/equeue/registry/registry.py

from typing import Callable, Dict

_TASK_REGISTRY: Dict[str, Callable] = {}

def task(*, name: str):
    """
    Decorator to register a task by explicit name.
    Registration happens at import time.
    
    :type name: str
    """

    if not name or not isinstance(name, str):
        raise ValueError("Task name must be a non-empty string")
    
    def decorator(fn: Callable) -> Callable:
        if name in _TASK_REGISTRY:
            raise ValueError(f"Task {name} is already registered")
        
        _TASK_REGISTRY[name] = fn
        return fn
    return decorator

def get_task(name: str) -> Callable:
    """
    Resolve a task by name.
    Raises KeyError if task is not registered.
    """
    try:
        return _TASK_REGISTRY[name]
    except KeyError:
        raise KeyError(f"Task '{name}' is not registered")
