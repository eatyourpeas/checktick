"""
Management command to seed external API dataset records.

This creates the initial DataSet records for external API datasets
(hospitals, NHS trusts, etc.) without fetching the actual data.

Use sync_external_datasets to populate them with data.

Usage:
    python manage.py seed_external_datasets
    python manage.py seed_external_datasets --clear  # Remove existing external datasets first
"""

from django.core.management.base import BaseCommand

from checktick_app.surveys.external_datasets import (
    AVAILABLE_DATASETS,
    _get_api_url,
    _get_endpoint_for_dataset,
)
from checktick_app.surveys.models import DataSet


class Command(BaseCommand):
    help = "Seed external API dataset records (without data)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing external API datasets before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted_count = DataSet.objects.filter(category="rcpch").delete()[0]
            self.stdout.write(
                self.style.WARNING(
                    f"Deleted {deleted_count} existing RCPCH API datasets"
                )
            )

        self.stdout.write(
            f"Seeding {len(AVAILABLE_DATASETS)} external dataset records..."
        )

        created_count = 0
        exists_count = 0

        for key, name in AVAILABLE_DATASETS.items():
            dataset, created = DataSet.objects.get_or_create(
                key=key,
                defaults={
                    "name": name,
                    "description": "External dataset from RCPCH NHS Organisations API",
                    "category": "rcpch",
                    "source_type": "api",
                    "is_custom": False,
                    "is_global": True,
                    "options": [],  # Empty until synced
                    "external_api_endpoint": _get_endpoint_for_dataset(key),
                    "external_api_url": _get_api_url(),
                    "sync_frequency_hours": 24,
                    "last_synced_at": None,  # Never synced yet
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created dataset: {name} ({key})")
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"⏭️  Dataset already exists: {name} ({key})")
                )
                exists_count += 1

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("SEEDING COMPLETE"))
        self.stdout.write(f"  Created: {created_count}")
        self.stdout.write(f"  Already existed: {exists_count}")
        self.stdout.write("=" * 60)

        if created_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Run 'python manage.py sync_external_datasets' to populate with data"
                )
            )
