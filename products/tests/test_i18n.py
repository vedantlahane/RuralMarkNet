"""Tests covering language switching behaviour."""
from __future__ import annotations

from django.test import TestCase
from django.urls import reverse


class LanguageSwitchTests(TestCase):
    """Ensure the language switcher updates the session."""

    def test_set_language_endpoint(self) -> None:
        response = self.client.post(reverse("set_language"), data={"language": "hi", "next": "/"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("django_language"), "hi")
