def extract_effects(entity) -> set[str]:
    attr = getattr(entity, 'Effect', None)
    if isinstance(attr, str):
        return {e.strip() for e in attr.split(',')}
    elif isinstance(attr, list):
        return set(attr)
    elif attr:
        return {attr}
    return set()
