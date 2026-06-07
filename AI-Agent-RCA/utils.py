def to_dict(obj):
    """Convert Pydantic model to dict if needed"""
    if hasattr(obj, 'model_dump'): # Pydantic v2
        return obj.model_dump(exclude_none=True)
    elif hasattr(obj, 'dict'): # Pydantic v1
        return obj.dict(exclude_none=True)
    return obj
