"""Account-related Django signals."""
from __future__ import annotations

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def ensure_user_group(sender, instance: User, created: bool, **_: object) -> None:
    """Ensure that each user belongs to a role-specific group."""
    if not created:
        return

    group_name = instance.get_role_display()
    group, _ = Group.objects.get_or_create(name=group_name)
    instance.groups.add(group)
