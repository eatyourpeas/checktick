# Self-hosting: Dataset Management

This guide covers the setup and maintenance of datasets for self-hosted CheckTick instances.

## Overview

CheckTick provides three types of datasets for dropdown questions:

1. **NHS Data Dictionary** - Standardized medical codes (scraped from NHS DD website)
2. **RCPCH NHS Organisations** - Organizational data (synced from RCPCH API)
3. **User-Created** - Custom lists created by organizations

All datasets are stored in the database for fast access and offline capability.

## Initial Setup

Run these commands once when first setting up your CheckTick instance.

### 1. Seed NHS Data Dictionary Datasets

Create NHS DD dataset records and scrape initial data:

```bash
# Create dataset records
docker compose exec web python manage.py seed_nhs_datasets

# Scrape data from NHS DD website (takes 1-2 minutes)
docker compose exec web python manage.py scrape_nhs_dd_datasets
```

This creates 48 NHS DD datasets including:

- Main Specialty Code (75 options)
- Treatment Function Code (73 options)
- Ethnic Category (17 options)
- Smoking Status Code (6 options)
- Clinical Frailty Scale (9 options)
- Plus 40+ additional standardized lists

See the [NHS DD Dataset Reference](nhs-data-dictionary-datasets.md) for the complete list.

### 2. Seed External API Datasets

Create RCPCH dataset records and fetch initial data:

```bash
# Create dataset records
docker compose exec web python manage.py seed_external_datasets

# Fetch data from RCPCH API (takes 2-3 minutes)
docker compose exec web python manage.py sync_external_datasets
```

This creates and populates 7 datasets:

- Hospitals (England & Wales) - ~500 hospitals
- NHS Trusts - ~240 trusts
- Welsh Local Health Boards - 7 boards
- London Boroughs - 33 boroughs
- NHS England Regions - 7 regions
- Paediatric Diabetes Units - ~175 units
- Integrated Care Boards - 42 ICBs

## Scheduled Synchronization

To keep datasets current, schedule regular sync commands.

### NHS Data Dictionary Scraping

**Recommended schedule:** Weekly (Sundays at 5 AM UTC)

```cron
0 5 * * 0 cd /app && python manage.py scrape_nhs_dd_datasets
```

**Northflank setup:**

1. Create a new Cron Job service
2. Configure:
   - **Name**: `checktick-nhs-dd-scrape`
   - **Schedule**: `0 5 * * 0`
   - **Command**: `python manage.py scrape_nhs_dd_datasets`
3. Copy environment variables from web service
4. Deploy

See [Self-hosting Scheduled Tasks](self-hosting-scheduled-tasks.md#4-nhs-data-dictionary-scraping-recommended) for full setup details.

### External API Sync

**Recommended schedule:** Daily (4 AM UTC)

```cron
0 4 * * * cd /app && python manage.py sync_external_datasets
```

**Northflank setup:**

1. Create a new Cron Job service
2. Configure:
   - **Name**: `checktick-dataset-sync`
   - **Schedule**: `0 4 * * *`
   - **Command**: `python manage.py sync_external_datasets`
3. Copy environment variables from web service
4. Deploy

See [Self-hosting Scheduled Tasks](self-hosting-scheduled-tasks.md#3-external-dataset-sync-recommended) for full setup details.

## Management Commands

### seed_nhs_datasets

Create NHS Data Dictionary dataset records.

```bash
# Create all NHS DD dataset records
python manage.py seed_nhs_datasets

# Clear existing and re-seed
python manage.py seed_nhs_datasets --clear
```

**What it does:**

- Creates 48 NHS DD dataset records with metadata
- Sets `source_type="scrape"` and `reference_url` fields
- Options initially set to placeholder (requires scraping)

**When to use:**

- Initial setup
- After database reset
- When new NHS DD datasets are added to seed file

### scrape_nhs_dd_datasets

Scrape NHS Data Dictionary datasets from the NHS DD website.

```bash
# Scrape all datasets that need updating
python manage.py scrape_nhs_dd_datasets

# Scrape a specific dataset
python manage.py scrape_nhs_dd_datasets --dataset smoking_status_code

# Force re-scrape all datasets
python manage.py scrape_nhs_dd_datasets --force

# Preview what would be scraped (dry-run)
python manage.py scrape_nhs_dd_datasets --dry-run
```

**Options:**

- `--dataset KEY` - Scrape only a specific dataset
- `--force` - Re-scrape even if recently updated
- `--dry-run` - Preview changes without saving

**What it does:**

- Fetches HTML from NHS DD website
- Parses tables/lists to extract codes and descriptions
- Updates dataset options in database
- Records `last_scraped` timestamp

**Example output:**

```text
📊 Found 48 dataset(s) to process

  Fetching: https://www.datadictionary.nhs.uk/data_elements/smoking_status_code.html
  Found 6 items
✓ Scraped: Smoking Status Code

  Fetching: https://www.datadictionary.nhs.uk/data_elements/ethnic_category.html
  Found 17 items
↻ Updated: Ethnic Category

============================================================
✓ Successfully scraped: 42
↻ Successfully updated: 6
============================================================
```

**When to use:**

- Initial setup (after `seed_nhs_datasets`)
- Scheduled weekly sync
- After NHS DD publishes updates
- Manual refresh of specific dataset

### seed_external_datasets

Create External API dataset records.

```bash
# Create all external dataset records
python manage.py seed_external_datasets
```

**What it does:**

- Creates 7 RCPCH dataset records with metadata
- Sets `source_type="api"` and API endpoint configuration
- Options initially empty (requires sync)

**When to use:**

- Initial setup
- After database reset

### sync_external_datasets

Sync external datasets from RCPCH API.

```bash
# Sync all external datasets
python manage.py sync_external_datasets

# Sync a specific dataset
python manage.py sync_external_datasets --dataset hospitals_england_wales

# Force sync even if recently synced
python manage.py sync_external_datasets --force

# Preview changes without saving
python manage.py sync_external_datasets --dry-run
```

**Options:**

- `--dataset KEY` - Sync only a specific dataset
- `--force` - Bypass sync frequency check
- `--dry-run` - Preview without saving

**What it does:**

- Fetches data from RCPCH API
- Transforms into CheckTick format
- Updates dataset options in database
- Records `last_synced_at` timestamp and increments `version`

**Example output:**

```text
Syncing 7 external datasets...

✓ Synced: Hospitals (England & Wales) - 487 options (version 2)
✓ Synced: NHS Trusts - 238 options (version 2)
✓ Synced: Welsh Local Health Boards - 7 options (version 2)
⊝ Skipped: London Boroughs (synced 2 hours ago, next sync in 22 hours)
...

Summary:
✓ Synced: 5
⊝ Skipped: 2
✗ Errors: 0
```

**When to use:**

- Initial setup (after `seed_external_datasets`)
- Scheduled daily sync
- Manual refresh when API data changes

## Configuration

### Environment Variables

#### RCPCH API Configuration

```bash
# Optional: Override RCPCH API URL
EXTERNAL_DATASET_API_URL=https://api.rcpch.ac.uk/nhs-organisations/v1

# Optional: Add API key if required in future
EXTERNAL_DATASET_API_KEY=your_api_key_here
```

**Defaults:**

- `EXTERNAL_DATASET_API_URL`: `https://api.rcpch.ac.uk/nhs-organisations/v1`
- `EXTERNAL_DATASET_API_KEY`: Not required (public API)

#### Sync Frequency

Configure in dataset model (via Django admin or database):

```python
# sync_frequency_hours field (default: 24)
dataset.sync_frequency_hours = 24  # Daily sync
dataset.save()
```

## Database Schema

### DataSet Model Fields

Key fields for dataset management:

```python
# Identity
key = CharField(max_length=255, unique=True)
name = CharField(max_length=255)
description = TextField(blank=True)
category = CharField(choices=[...])  # nhs_dd, rcpch, external_api, user_created

# Source tracking
source_type = CharField(choices=[...])  # manual, api, imported, scrape
reference_url = URLField(blank=True)  # Source URL for NHS DD datasets
api_endpoint = CharField(blank=True)  # API endpoint for external datasets

# Options storage
options = JSONField(default=dict)  # Key-value pairs

# Sync metadata
last_synced_at = DateTimeField(null=True)  # For API datasets
last_scraped = DateTimeField(null=True)  # For NHS DD datasets
sync_frequency_hours = IntegerField(default=24)
version = IntegerField(default=1)

# Sharing
is_custom = BooleanField(default=False)
is_global = BooleanField(default=False)
parent = ForeignKey('self', null=True)  # For custom versions
organization = ForeignKey(Organization, null=True)

# Discovery
tags = JSONField(default=list)
```

## Troubleshooting

### NHS DD Scraping Issues

**Problem:** Scraper can't find options on NHS DD page

```text
✗ Error scraping Smoking Status Code: No valid options found on the page
```

**Solutions:**

1. Check if NHS DD page structure changed:
   ```bash
   curl https://www.datadictionary.nhs.uk/data_elements/smoking_status_code.html
   ```

2. Update scraper parsing strategies in `scrape_nhs_dd_datasets.py`

3. Report issue to development team

**Problem:** HTTP errors when fetching NHS DD pages

```text
✗ Error scraping: HTTPError 503 Service Unavailable
```

**Solutions:**

1. Wait and retry (NHS DD might be temporarily down)
2. Check NHS DD website status
3. Run with `--force` to retry specific datasets

### External API Sync Issues

**Problem:** RCPCH API connection errors

```text
✗ Error syncing: ConnectionError
```

**Solutions:**

1. Check RCPCH API status: https://api.rcpch.ac.uk/
2. Verify `EXTERNAL_DATASET_API_URL` environment variable
3. Check firewall/proxy settings
4. Retry with `--force`

**Problem:** API rate limiting

```text
✗ Error syncing: 429 Too Many Requests
```

**Solutions:**

1. Reduce sync frequency
2. Stagger sync commands (don't run all at once)
3. Contact RCPCH for rate limit increase

### Performance

**Problem:** Syncing takes too long

**Solutions:**

1. Sync specific datasets instead of all:
   ```bash
   python manage.py sync_external_datasets --dataset hospitals_england_wales
   ```

2. Increase worker timeout for cron jobs

3. Run syncs during low-traffic periods

## Monitoring

### Check Dataset Status

Via Django admin:

1. Navigate to `/admin/surveys/dataset/`
2. Filter by `category` or `source_type`
3. Check `last_synced_at` / `last_scraped` timestamps
4. Review `version` numbers for update history

Via API:

```bash
# Get all datasets with sync status
curl https://checktick.example.com/api/datasets-v2/ | jq '.results[] | {key, last_synced_at, last_scraped}'
```

### Audit Logs

Dataset updates are logged in the audit log:

```python
from checktick_app.surveys.models import AuditLog

# Check recent dataset updates
AuditLog.objects.filter(
    action__in=['dataset_synced', 'dataset_scraped']
).order_by('-timestamp')
```

## Related Documentation

- [Datasets User Guide](datasets.md) - Using datasets in surveys
- [Dataset API Reference](api-datasets.md) - API endpoints
- [NHS DD Dataset Reference](nhs-data-dictionary-datasets.md) - Complete NHS DD list
- [Scheduled Tasks](self-hosting-scheduled-tasks.md) - Cron job setup
