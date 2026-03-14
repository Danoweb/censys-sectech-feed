from typing import Any, Callable, Union
from api.v1.models.alerts import Alert


def _resolve(obj: dict, path: str) -> Any:
    """Traverse a dot-notation path through a nested dict, returning None if any key is missing."""
    keys = path.split(".")
    current = obj
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def translate(obj: dict, mapping: dict[str, Union[str, Callable]]) -> Alert:
    """
    Build an Alert model from an arbitrary object using a field mapping.

    Each key in `mapping` must be a field name on the Alert model.
    Each value can be:
      - A dot-notation string path (e.g. "data.id") resolved against `obj`
      - A callable that receives a resolve(path) helper and returns the field value
        e.g. lambda resolve: resolve("data.severity") + " - " + resolve("data.hostname")
    """
    def resolve(path: str) -> Any:
        return _resolve(obj, path)

    field_values = {}
    for field, instruction in mapping.items():
        if callable(instruction):
            field_values[field] = instruction(resolve)
        else:
            field_values[field] = resolve(instruction)

    return Alert(**field_values)
