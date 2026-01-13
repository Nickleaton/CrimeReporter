from functools import wraps


def singleton(cls):
    """Decorator to make a class a singleton without reinitialization."""
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            # Create the instance and store it
            instance = cls.__new__(cls)
            # Explicitly call __init__ once
            cls.__init__(instance, *args, **kwargs)
            instances[cls] = instance
        return instances[cls]

    return get_instance
