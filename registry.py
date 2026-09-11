SCREENER_REGISTRY = {}

def register_screener(name: str):
    """Decorator to register a screener into the engine."""
    def decorator(func):
        SCREENER_REGISTRY[name] = func
        return func
    return decorator

SCREENER_4H_REGISTRY = {}

def register_4h_screener(name: str):
    def decorator(func):
        SCREENER_4H_REGISTRY[name] = func
        return func
    return decorator