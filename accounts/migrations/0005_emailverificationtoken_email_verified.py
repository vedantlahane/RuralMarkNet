# Generated manually for email verification feature
import django.db.models.deletion
from django.db import migrations, models
import accounts.models


def mark_existing_users_verified(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(email_verified=False).update(email_verified=True)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_accepted_payment_methods"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(
                default=False,
                help_text="Indicates whether the user has confirmed their email address.",
            ),
        ),
        migrations.CreateModel(
            name="EmailVerificationToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(default=accounts.models._generate_verification_token, max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_tokens", to="accounts.user"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.RunPython(mark_existing_users_verified, migrations.RunPython.noop),
    ]
