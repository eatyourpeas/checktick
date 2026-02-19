"""
Data migration to initialize platform key version v1 from existing Vault data.

This migration is safe to run on:
- Existing production systems (imports current vault component from Vault)
- New systems (skips if no Vault key exists yet)
- Development environments (skips if Vault unreachable)

The migration is idempotent and can be run multiple times safely.
"""

import logging

from django.db import migrations
from django.utils import timezone

logger = logging.getLogger(__name__)


def initialize_platform_key_v1(apps, schema_editor):
    """
    Create PlatformKeyVersion v1 from existing Vault platform key.

    If a platform key already exists in Vault at 'platform/master-key',
    this migration extracts the vault component and creates v1 in the database.

    This ensures existing escrowed KEKs can still be recovered after
    the versioning system is deployed.
    """
    PlatformKeyVersion = apps.get_model("surveys", "PlatformKeyVersion")

    # Check if v1 already exists (migration already ran or manual creation)
    if PlatformKeyVersion.objects.filter(version="v1").exists():
        logger.info("Platform key version v1 already exists. Skipping initialization.")
        return

    # Try to import vault component from existing Vault setup
    try:
        from checktick_app.surveys.vault_client import VaultClient

        vault_client = VaultClient()
        client = vault_client._get_client()

        # Read existing platform key vault component from Vault
        # Explicitly set raise_on_deleted_version=True to preserve behavior and silence hvac 3.0 warning
        secret = client.secrets.kv.v2.read_secret_version(
            path="platform/master-key", raise_on_deleted_version=True
        )

        vault_component_hex = secret["data"]["data"]["vault_component"]
        vault_component = bytes.fromhex(vault_component_hex)

        # Create v1 with the existing vault component
        PlatformKeyVersion.objects.create(
            version="v1",
            vault_component=vault_component,
            created_at=timezone.now(),
            activated_at=timezone.now(),  # Immediately active
            notes="Migrated from existing Vault platform key during versioning system deployment",
        )

        logger.info(
            "✓ Successfully created PlatformKeyVersion v1 from existing Vault data. "
            "Existing escrowed KEKs will continue to work."
        )

    except ImportError:
        # Vault client not available (shouldn't happen in normal deployment)
        logger.warning(
            "Could not import VaultClient. Skipping platform key v1 initialization. "
            "You must create it manually: python manage.py create_platform_key_version --version v1 --activate"
        )

    except Exception as e:
        # Vault unreachable, no platform key exists yet, or other error
        error_message = str(e)

        if "InvalidPath" in type(e).__name__ or "404" in error_message:
            # No platform key exists in Vault yet - this is OK for new installations
            logger.info(
                "No existing platform key found in Vault. This is normal for new installations. "
                "Create one manually: python manage.py create_platform_key_version --version v1 --activate"
            )
        else:
            # Vault connection issue or other error
            logger.warning(
                f"Could not read platform key from Vault: {e}. "
                "Skipping automatic v1 creation. "
                "If you have an existing platform key in Vault, create v1 manually: "
                "python manage.py create_platform_key_version --version v1"
            )


def reverse_initialization(apps, schema_editor):
    """
    Reverse migration - delete v1 if it was auto-created.

    Only deletes if there are no escrows referencing it.
    """
    PlatformKeyVersion = apps.get_model("surveys", "PlatformKeyVersion")
    UserSurveyKEKEscrow = apps.get_model("surveys", "UserSurveyKEKEscrow")

    try:
        v1 = PlatformKeyVersion.objects.get(version="v1")

        # Check if any escrows reference v1
        escrow_count = UserSurveyKEKEscrow.objects.filter(
            platform_key_version=v1
        ).count()

        if escrow_count > 0:
            logger.warning(
                f"Cannot delete PlatformKeyVersion v1: {escrow_count} escrows reference it. "
                f"Manual cleanup required."
            )
        else:
            v1.delete()
            logger.info("Deleted PlatformKeyVersion v1 (no escrows referencing it).")

    except PlatformKeyVersion.DoesNotExist:
        logger.info("PlatformKeyVersion v1 does not exist. Nothing to reverse.")


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0043_add_platform_key_versioning"),
    ]

    operations = [
        migrations.RunPython(
            initialize_platform_key_v1,
            reverse_code=reverse_initialization,
        ),
    ]
