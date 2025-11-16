"""
Management command to scrape NHS Data Dictionary datasets.

This command scrapes standardized lists from the NHS Data Dictionary website
and updates the corresponding DataSet records in the database.

Usage:
    python manage.py scrape_nhs_dd_datasets
    python manage.py scrape_nhs_dd_datasets --dataset accommodation_status_code
    python manage.py scrape_nhs_dd_datasets --force
"""

import re
from datetime import datetime
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from checktick_app.surveys.models import DataSet


class Command(BaseCommand):
    help = "Scrape NHS Data Dictionary datasets and update database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            type=str,
            help="Scrape only a specific dataset by key",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-scrape even if recently updated",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be scraped without saving",
        )

    def handle(self, *args, **options):
        dataset_key = options.get("dataset")
        force = options.get("force", False)
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be saved"))

        # Get datasets that need scraping
        datasets = DataSet.objects.filter(
            source_type="scrape",
            reference_url__isnull=False,
        )

        if dataset_key:
            datasets = datasets.filter(key=dataset_key)
            if not datasets.exists():
                raise CommandError(f"Dataset '{dataset_key}' not found or not scrapable")

        if not datasets.exists():
            self.stdout.write(self.style.WARNING("No datasets found to scrape"))
            return

        total = datasets.count()
        scraped = 0
        updated = 0
        skipped = 0
        errors = 0

        self.stdout.write(f"\n📊 Found {total} dataset(s) to process\n")

        for dataset in datasets:
            try:
                result = self._scrape_dataset(dataset, force=force, dry_run=dry_run)

                if result == "updated":
                    updated += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Updated: {dataset.name}")
                    )
                elif result == "scraped":
                    scraped += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Scraped: {dataset.name}")
                    )
                elif result == "skipped":
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f"⊝ Skipped: {dataset.name} (already up-to-date)")
                    )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error scraping {dataset.name}: {str(e)}")
                )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"✓ Successfully scraped: {scraped}"))
        self.stdout.write(self.style.SUCCESS(f"↻ Successfully updated: {updated}"))
        if skipped:
            self.stdout.write(self.style.WARNING(f"⊝ Skipped: {skipped}"))
        if errors:
            self.stdout.write(self.style.ERROR(f"✗ Errors: {errors}"))
        self.stdout.write("=" * 60 + "\n")

    def _scrape_dataset(
        self, dataset: DataSet, force: bool = False, dry_run: bool = False
    ) -> str:
        """
        Scrape a single dataset from NHS DD.

        Returns:
            "scraped" if new data was scraped
            "updated" if existing data was updated
            "skipped" if no scraping was needed
        """
        # Check if already scraped recently (unless forced)
        if not force and dataset.options and isinstance(dataset.options, dict):
            # If options exist and don't contain placeholder, consider it scraped
            if "PENDING" not in dataset.options:
                return "skipped"

        self.stdout.write(f"  Fetching: {dataset.reference_url}")

        # Fetch the page
        response = requests.get(dataset.reference_url, timeout=30)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract options from the page
        options = self._extract_options_from_html(soup, dataset)

        if not options:
            raise ValueError("No valid options found on the page")

        self.stdout.write(f"  Found {len(options)} items")

        # Determine if this is first scrape or update
        is_update = (
            dataset.options
            and isinstance(dataset.options, dict)
            and "PENDING" not in dataset.options
        )

        if dry_run:
            self.stdout.write(f"  Would save {len(options)} options (DRY RUN)")
            return "updated" if is_update else "scraped"

        # Update the dataset
        with transaction.atomic():
            dataset.options = options
            dataset.last_scraped = timezone.now()
            dataset.save()

        return "updated" if is_update else "scraped"

    def _extract_options_from_html(
        self, soup: BeautifulSoup, dataset: DataSet
    ) -> Dict[str, str]:
        """
        Extract code/value pairs from NHS DD HTML page.

        NHS DD pages typically have tables with codes and descriptions.
        This method tries multiple strategies to find the relevant data.
        """
        options = {}

        # Strategy 1: Look for tables with "Code" and "Description" or "National Code"
        tables = soup.find_all("table")

        for table in tables:
            # Get headers
            headers = []
            header_row = table.find("tr")
            if header_row:
                headers = [
                    th.get_text(strip=True).lower()
                    for th in header_row.find_all(["th", "td"])
                ]

            # Check if this looks like a data table
            if not headers or len(headers) < 2:
                continue

            # Find code and description column indices
            code_idx = None
            desc_idx = None

            for idx, header in enumerate(headers):
                if "code" in header or "value" in header:
                    code_idx = idx
                if "description" in header or "name" in header or "meaning" in header:
                    desc_idx = idx

            if code_idx is None or desc_idx is None:
                continue

            # Extract data rows
            rows = table.find_all("tr")[1:]  # Skip header

            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) <= max(code_idx, desc_idx):
                    continue

                code = cells[code_idx].get_text(strip=True)
                description = cells[desc_idx].get_text(strip=True)

                # Clean up the code and description
                code = re.sub(r"\s+", " ", code).strip()
                description = re.sub(r"\s+", " ", description).strip()

                if code and description:
                    options[code] = description

        # Strategy 2: Look for definition lists (dl/dt/dd)
        if not options:
            dls = soup.find_all("dl")
            for dl in dls:
                terms = dl.find_all("dt")
                definitions = dl.find_all("dd")

                for dt, dd in zip(terms, definitions):
                    code = dt.get_text(strip=True)
                    description = dd.get_text(strip=True)

                    # Try to extract code from the term
                    code_match = re.search(r"^([A-Z0-9]+)", code)
                    if code_match:
                        code = code_match.group(1)
                        description = re.sub(r"^[A-Z0-9]+\s*[-–—]\s*", "", description)

                    if code and description:
                        options[code] = description

        # Strategy 3: Look for lists with specific patterns
        if not options:
            lists = soup.find_all(["ul", "ol"])
            for lst in lists:
                items = lst.find_all("li")
                for item in items:
                    text = item.get_text(strip=True)
                    # Look for pattern: "CODE - Description" or "CODE: Description"
                    match = re.match(r"^([A-Z0-9]+)\s*[-–—:]\s*(.+)$", text)
                    if match:
                        code, description = match.groups()
                        options[code] = description

        return options
