# Managing Datasets

This guide shows you how to manage datasets for prefilled dropdown options in CheckTick.

## Overview

CheckTick supports three types of datasets for dropdown questions:

1. **NHS Data Dictionary (NHS DD)** - Standardized, read-only medical codes and classifications
2. **External APIs** - Data from external sources like the RCPCH NHS Organisations API
3. **User-Created Lists** - Custom lists created by organizations for their specific needs

All datasets are stored in the database and can be managed through the Django admin interface or management commands.

## Dataset Categories

### NHS Data Dictionary (NHS DD)

NHS DD datasets are standardized medical codes and classifications from the [NHS Data Dictionary](https://www.datadictionary.nhs.uk/). These are:
- **Read-only** - Cannot be modified to maintain standardization
- **Global** - Available to all organizations
- **Pre-seeded** - Common codes included by default
- **Customizable** - Organizations can create custom versions as templates

**Pre-seeded NHS DD datasets:**
- Main Specialty Code (75 options)
- Treatment Function Code (73 options)
- Ethnic Category (17 options)

### External API Datasets

Datasets synced from external APIs (e.g., RCPCH NHS Organisations API):

- **Database-backed** - Stored in database for fast access
- **Periodically synced** - Updated via scheduled command (daily recommended)
- **Global** - Available to all organizations
- **Offline-capable** - Works without internet once synced

**Available external datasets:**

- Hospitals (England & Wales)
- NHS Trusts
- Welsh Local Health Boards
- London Boroughs
- NHS England Regions
- Paediatric Diabetes Units
- Integrated Care Boards (ICBs)

**Initial Setup:**

```bash
# 1. Create dataset records
docker compose exec web python manage.py seed_external_datasets

# 2. Fetch data from APIs
docker compose exec web python manage.py sync_external_datasets

# 3. Schedule daily sync (see self-hosting-scheduled-tasks.md)
0 4 * * * cd /app && python manage.py sync_external_datasets
```

### User-Created Lists

Custom lists created by organizations:
- **Editable** - Can be modified as needed
- **Organization-specific** or **Globally published** - Can be private to your organization or shared with all users
- **Based on any global dataset** - Can use NHS DD datasets, external API datasets, or other published datasets as templates
- **Taggable** - Can add tags for easy discovery and filtering

## Quick Start: Creating a Custom List

### Option 1: Django Admin (Recommended)

1. Navigate to Django Admin: `/admin/surveys/dataset/`
2. Click "Add Dataset"
3. Fill in:
   - **Key**: Unique identifier (e.g., `our_specialty_codes`)
   - **Name**: Display name (e.g., "Our Specialty Codes")
   - **Category**: Select "User Created"
   - **Options**: Add your list items (one per line or as JSON array)
   - **Organization**: Select your organization (optional for global lists)
4. Save

The dataset will immediately appear in the dropdown selector.

### Option 2: Create from NHS DD Template

To customize an NHS DD dataset while preserving the original:

```python
# In Django shell
from checktick_app.surveys.models import DataSet, Organization
from django.contrib.auth import get_user_model

User = get_user_model()

# Get NHS DD dataset
nhs_dd = DataSet.objects.get(key='main_specialty_code')

# Create custom version
user = User.objects.get(username='your_username')
org = Organization.objects.get(name='Your Hospital')

custom = nhs_dd.create_custom_version(user=user, organization=org)

# Modify as needed
custom.options = custom.options[:20]  # Keep only first 20
custom.description = "Our hospital's specialty codes"
custom.save()
```

## Dataset Sharing and Publishing

### Creating Custom Versions from Global Datasets

Any global dataset (NHS DD, external API, or published by another organization) can be used as a template for your custom list:

**Via API:**

```bash
# Create custom version of any global dataset
curl -X POST https://your-domain/api/datasets-v2/{dataset_key}/create-custom/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Our Custom Hospital List",
    "organization": 123
  }'
```

**Via Django Shell:**

```python
from checktick_app.surveys.models import DataSet, Organization
from django.contrib.auth import get_user_model

User = get_user_model()

# Get any global dataset (NHS DD, external API, or published)
global_dataset = DataSet.objects.get(key='hospitals_england_wales')

# Create custom version
user = User.objects.get(username='your_username')
org = Organization.objects.get(name='Your Hospital')

custom = global_dataset.create_custom_version(
    user=user,
    organization=org,
    custom_name="Our Preferred Hospitals"
)

# Customize as needed
custom.options = custom.options[:50]  # Keep only first 50
custom.tags = ["curated", "local"]
custom.save()
```

**Key benefits:**
- Start with high-quality, maintained data
- Customize for your specific needs
- Independent from the source - your changes don't affect others
- Can be further published for others to use

### Publishing Datasets Globally

Organization ADMINs and CREATORs can publish their custom lists to make them available to all CheckTick users:

**Via API:**

```bash
# Publish your organization's dataset globally
curl -X POST https://your-domain/api/datasets-v2/{your_dataset_key}/publish/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Via Django Shell:**

```python
from checktick_app.surveys.models import DataSet

# Get your organization's dataset
dataset = DataSet.objects.get(key='our_specialty_codes')

# Publish it globally
dataset.publish()

# Now available to all users!
# Your organization attribution is preserved
```

**What happens when you publish:**

1. ✅ **Global availability**: All users can now see and use your dataset
2. ✅ **Attribution preserved**: Your organization remains as the creator
3. ✅ **Continued control**: Your organization can still edit the dataset
4. ⚠️ **Deletion protection**: If others create custom versions, you cannot delete it (prevents breaking dependencies)

### Tags and Discovery

Add tags to make datasets easier to find:

```python
dataset.tags = ["pediatrics", "cardiology", "NHS"]
dataset.save()
```

**Filter by tags via API:**

```bash
# Find all datasets with specific tags (AND logic)
curl https://your-domain/api/datasets-v2/?tags=pediatrics,NHS \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search by name or description
curl https://your-domain/api/datasets-v2/?search=hospital \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get tag counts for faceted filtering
curl https://your-domain/api/datasets-v2/available-tags/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Best Practices

1. **Use templates**: Start from NHS DD or external API datasets when applicable
2. **Add tags**: Help others discover your published datasets
3. **Meaningful names**: Use clear, descriptive names for published datasets
4. **Test before publishing**: Verify your dataset works correctly before making it global
5. **Document changes**: Use the description field to explain customizations
6. **Consider versioning**: If making major changes to a published dataset, consider creating a new version instead

For complete API reference and examples, see [Dataset Sharing and Customization](dataset-sharing-and-customization.md).

## Management Commands

### Seed NHS DD Datasets

Pre-populate common NHS Data Dictionary datasets:

```bash
docker compose exec web python manage.py seed_nhs_datasets

# Clear existing and re-seed
docker compose exec web python manage.py seed_nhs_datasets --clear
```

### Seed External API Datasets

Create database records for external API datasets:

```bash
docker compose exec web python manage.py seed_external_datasets

# Clear existing RCPCH datasets first
docker compose exec web python manage.py seed_external_datasets --clear
```

This creates records with metadata but empty options. Run sync command to populate.

### Sync External Datasets

Fetch data from external APIs and populate datasets:

```bash
# Sync all external datasets
docker compose exec web python manage.py sync_external_datasets

# Sync specific dataset
docker compose exec web python manage.py sync_external_datasets --dataset hospitals_england_wales

# Force sync (bypass frequency check)
docker compose exec web python manage.py sync_external_datasets --force

# Dry-run (preview changes)
docker compose exec web python manage.py sync_external_datasets --dry-run
```

**Recommended**: Schedule daily sync via cron. See [Scheduled Tasks](self-hosting-scheduled-tasks.md).

## Adding New External API Datasets

To add a new dataset from the RCPCH NHS Organisations API or other sources, update the code in `checktick_app/surveys/external_datasets.py`:

### 1. Add to AVAILABLE_DATASETS

```python
AVAILABLE_DATASETS = {
    # ... existing datasets ...
    "your_dataset_key": "Your Dataset Display Name",
}
```

### 2. Add Endpoint Mapping

```python
def _get_endpoint_for_dataset(dataset_key: str) -> str:
    endpoint_map = {
        # ... existing mappings ...
        "your_dataset_key": "/your/endpoint/",  # Include trailing slash
    }
    return endpoint_map.get(dataset_key, "")
```

### 3. Add Transformer Logic

Add a new `elif` block in `_transform_response_to_options()`:

```python
def _transform_response_to_options(dataset_key: str, data: Any) -> list[str]:
    # ... existing code ...

    elif dataset_key == "your_dataset_key":
        # Document the expected API response format
        # Format: {"id": "123", "name": "Example", ...}
        for item in data:
            # Validate required fields exist
            if not isinstance(item, dict) or "name" not in item or "id" not in item:
                logger.warning(f"Skipping invalid item: {item}")
                continue

            # Format as "Name (Code)" for consistency
            options.append(f"{item['name']} ({item['id']})")

    return options
```

### 4. Seed and Sync

```bash
# Create database record
docker compose exec web python manage.py seed_external_datasets

# Populate with data
docker compose exec web python manage.py sync_external_datasets --dataset your_dataset_key
```

The dataset will immediately appear in the dropdown selector!

## Database Schema

The DataSet model stores all datasets with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `key` | String | Unique identifier (e.g., `main_specialty_code`) |
| `name` | String | Display name shown in UI |
| `description` | Text | Optional detailed description |
| `category` | Choice | `nhs_dd`, `external_api`, `rcpch`, or `user_created` |
| `source_type` | Choice | `manual`, `api`, or `import` |
| `is_custom` | Boolean | True for user-created/modified datasets |
| `is_global` | Boolean | True if available to all organizations |
| `parent` | ForeignKey | Reference to NHS DD original if customized |
| `organization` | ForeignKey | Organization that owns this dataset (if not global) |
| `options` | JSONField | Array of option strings |
| `format_pattern` | String | Format hint (e.g., "code - description") |
| `version` | Integer | Incremented on each update |
| `is_active` | Boolean | Whether dataset is available for use |
| `last_synced_at` | DateTime | When API dataset was last updated |
| `created_by` | ForeignKey | User who created this dataset |

### Database Constraints

- **NHS DD datasets must be global**: NHS DD category requires `is_global=True` and `organization=None`
- **Global datasets have no organization**: `is_global=True` requires `organization=None`
- **Unique keys**: Each dataset key must be unique across the system

## Testing Your Datasets

### 1. Check Available Datasets

```python
# In Django shell
from checktick_app.surveys.external_datasets import get_available_datasets

datasets = get_available_datasets()
print(f"Found {len(datasets)} datasets")
for key, name in datasets.items():
    print(f"  {key}: {name}")
```

### 2. Fetch Dataset Options

```python
from checktick_app.surveys.external_datasets import fetch_dataset

options = fetch_dataset('main_specialty_code')
print(f"Got {len(options)} options")
print("First 5:", options[:5])
```

### 3. Organization-Specific Datasets

```python
from checktick_app.surveys.models import Organization

org = Organization.objects.get(name='Your Hospital')
datasets = get_available_datasets(organization=org)
# Returns both global datasets and organization-specific ones
```

### 4. Browser Testing

1. Navigate to survey builder
2. Create a dropdown question
3. Check "Use prefilled options"
4. Select your dataset from the dropdown
5. Click "Load Options"
6. Verify options populate correctly

## Best Practices

### 1. Use NHS DD as Templates

When possible, base custom lists on NHS DD standards:

```python
nhs_dd = DataSet.objects.get(key='main_specialty_code')
custom = nhs_dd.create_custom_version(user=user, organization=org)
# Modify custom.options as needed
```

### 2. Consistent Formatting

Use consistent format patterns for readability:

```python
# Preferred: "Name (Code)"
options = ["General Surgery (100)", "Urology (101)"]

# Document the pattern
dataset.format_pattern = "description (code)"
```

### 3. Version Tracking

Increment version when updating options:

```python
dataset.options = new_options
dataset.increment_version()
dataset.save()
```

### 4. Descriptive Keys

Use clear, descriptive keys:

- ✅ `our_specialty_codes`
- ✅ `hospital_departments`
- ❌ `list1`
- ❌ `custom`

## Migrating from Hardcoded to Database

To migrate existing hardcoded datasets to the database:

```python
from checktick_app.surveys.models import DataSet
from checktick_app.surveys.external_datasets import AVAILABLE_DATASETS, fetch_dataset

for key, name in AVAILABLE_DATASETS.items():
    # Check if already exists
    if DataSet.objects.filter(key=key).exists():
        continue

    # Determine category
    category = "rcpch" if "rcpch" in key else "external_api"

    # Create dataset
    dataset = DataSet.objects.create(
        key=key,
        name=name,
        category=category,
        source_type="api",
        is_global=True,
        options=[],  # Will be populated on first fetch
    )

    print(f"Created dataset: {key}")
```

## Troubleshooting

### Dataset Not Appearing in Dropdown

1. **Check is_active**: `dataset.is_active` must be `True`
2. **Verify organization access**: Global datasets or organization matches
3. **Clear cache**: `python manage.py shell -c "from django.core.cache import cache; cache.clear()"`
4. **Hard refresh browser**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)

### Custom Version Not Editable

1. **Check is_custom flag**: Must be `True`
2. **Verify not NHS DD**: Custom versions have category `user_created`
3. **Check constraints**: Ensure no database constraint violations

### Options Not Saving

1. **JSON format**: Options must be valid JSON array of strings
2. **Check field type**: Using JSONField, not TextField
3. **Validate data**: `dataset.full_clean()` before save

### Parent-Child Relationship Issues

1. **Only NHS DD can be parents**: Parent must have `category='nhs_dd'`
2. **No circular references**: Custom cannot reference another custom
3. **Use create_custom_version()**: Don't manually set parent on custom datasets

## Current Available Datasets

| Dataset Key | Display Name | Category | Type | Count |
|------------|--------------|----------|------|-------|
| `main_specialty_code` | Main Specialty Code | NHS DD | Manual | 75 |
| `treatment_function_code` | Treatment Function Code | NHS DD | Manual | 73 |
| `ethnic_category` | Ethnic Category | NHS DD | Manual | 17 |
| `hospitals_england_wales` | Hospitals (England & Wales) | RCPCH | API | ~2000 |
| `nhs_trusts` | NHS Trusts | RCPCH | API | ~200 |
| `welsh_lhbs` | Welsh Local Health Boards | RCPCH | API | ~20 |
| `london_boroughs` | London Boroughs | RCPCH | API | 33 |
| `nhs_england_regions` | NHS England Regions | RCPCH | API | 7 |
| `paediatric_diabetes_units` | Paediatric Diabetes Units | RCPCH | API | ~200 |
| `integrated_care_boards` | Integrated Care Boards (ICBs) | RCPCH | API | 42 |

## Related Documentation

- [Prefilled Datasets Setup](./prefilled-datasets-setup.md) - Configuration and API details
- [Prefilled Datasets Quick Start](./prefilled-datasets-quickstart.md) - User guide
- [Getting Started](./getting-started.md) - Environment variables
- [API Documentation](./api.md) - API endpoints for datasets

## Support

If you encounter issues or need help managing datasets:

1. Check the [troubleshooting section](#troubleshooting) above
2. Verify dataset in Django Admin: `/admin/surveys/dataset/`
3. Review model code: `checktick_app/surveys/models.py` (DataSet model)
4. Check integration: `checktick_app/surveys/external_datasets.py`
5. Run tests: `python -m pytest checktick_app/surveys/tests/test_datasets.py`
6. Check logs: `docker compose logs web --tail=50`
