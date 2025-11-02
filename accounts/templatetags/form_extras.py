"""Template helpers for rendering form widgets with custom attributes."""
from __future__ import annotations

from django import template

register = template.Library()


@register.simple_tag
def render_field(field, **attrs):
    """Render a bound field while merging in widget attributes."""
    if not hasattr(field, "as_widget"):
        return field

    base_attrs = dict(getattr(field.field.widget, "attrs", {}))

    merged_attrs: dict[str, object] = {}
    merged_attrs.update(base_attrs)

    for key, value in attrs.items():
        if value is None:
            continue
        normalized_key = key.replace("_", "-")
        if normalized_key == "class" and normalized_key in merged_attrs:
            merged_attrs[normalized_key] = f"{merged_attrs[normalized_key]} {value}".strip()
        else:
            merged_attrs[normalized_key] = value

    return field.as_widget(attrs=merged_attrs)
