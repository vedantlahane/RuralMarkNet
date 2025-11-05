from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_auditlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="accepted_payment_methods",
            field=models.JSONField(
                blank=True,
                default=None,
                help_text="Payment method codes this farmer chooses to accept.",
                null=True,
            ),
        ),
    ]
