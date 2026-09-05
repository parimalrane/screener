SCREENER_REGISTRY = {}

def register_screener(name: str):
    """Decorator to register a screener into the engine."""
    def decorator(func):
        SCREENER_REGISTRY[name] = func
        return func
    return decorator