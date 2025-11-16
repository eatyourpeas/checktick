# Dataset Management Features

CheckTick provides powerful dataset management features for creating, sharing, and discovering prefilled dropdown options across your organization and the entire platform.

## Overview

Datasets are reusable lists that power dropdown questions in your surveys. Instead of manually typing options for every dropdown, you can:

- **Use standardized data** from NHS Data Dictionary
- **Sync from external APIs** like RCPCH NHS Organisations
- **Create custom lists** tailored to your organization
- **Share your lists** with the entire CheckTick community
- **Build upon others' work** by creating custom versions of any global dataset

## Types of Datasets

### 1. NHS Data Dictionary (NHS DD)

Authoritative medical codes and classifications:

- **Main Specialty Code** - 75 medical specialties
- **Treatment Function Code** - 73 treatment classifications
- **Ethnic Category** - 17 standardized ethnic categories

**Characteristics:**

- ✅ Read-only (maintains standardization)
- ✅ Always up-to-date with NHS standards
- ✅ Available to all users
- ✅ Can be used as templates for custom versions

### 2. External API Datasets

Automatically synced from trusted sources:

- **Hospitals** (England & Wales) - ~500 hospitals
- **NHS Trusts** - ~240 trusts
- **Welsh Local Health Boards** - 7 health boards
- **London Boroughs** - 33 boroughs
- **NHS England Regions** - 7 regions
- **Paediatric Diabetes Units** - ~175 units
- **Integrated Care Boards** - 42 ICBs

**Characteristics:**

- ✅ Automatically updated daily
- ✅ Reliable, maintained data
- ✅ Offline-capable (cached in database)
- ✅ Available to all users
- ✅ Can be used as templates

### 3. User-Created Datasets

Custom lists created by your organization:

**Examples:**

- Department-specific codes
- Local hospital networks
- Custom specialty classifications
- Research cohort categories

**Capabilities:**

- ✅ Fully editable
- ✅ Can be private or published globally
- ✅ Taggable for easy discovery
- ✅ Based on any global dataset as a template

## Key Features

### Creating Custom Versions

Start with any global dataset (NHS DD, external API, or published by others) and customize it for your needs:

**Example: Creating a Regional Hospital List**

1. Find the "Hospitals (England & Wales)" dataset
2. Click "Create Custom Version"
3. Name it "Our Regional Hospitals"
4. Remove hospitals outside your region
5. Add local clinics if needed
6. Save and use in your surveys

**Benefits:**

- **Time-saving**: Start with quality data instead of from scratch
- **Independence**: Your changes don't affect the original
- **Flexibility**: Mix and match from multiple sources
- **No limits**: Create as many custom versions as you need

### Publishing Datasets Globally

Share your curated lists with the entire CheckTick community:

**When to publish:**

- You've created a useful list others might need
- You want to contribute to the community
- Your organization is authoritative for this data type
- You've curated a subset of a larger dataset for specific use cases

**What happens:**

1. Your dataset becomes visible to all CheckTick users
2. Your organization is credited as the source
3. Others can use it directly or create custom versions
4. You retain full editing rights
5. If others depend on it, deletion is protected

**Example: Publishing a Pediatric Cardiology Codes List**

```python
# You've created a comprehensive list of pediatric cardiology codes
# based on NHS DD specialty codes, filtered and enhanced

dataset = DataSet.objects.get(key='our_peds_cardio_codes')
dataset.tags = ['pediatrics', 'cardiology', 'specialty-codes']
dataset.description = "Pediatric cardiology codes curated by..."
dataset.publish()

# Now available globally!
```

### Tags and Discovery

Find datasets easily with tags and search:

**Common tag categories:**

- **Medical specialty**: `pediatrics`, `cardiology`, `oncology`
- **Data type**: `hospitals`, `codes`, `geographic`
- **Source**: `NHS`, `curated`, `research`
- **Region**: `england`, `wales`, `london`

**Search and filter:**

```bash
# Find pediatric datasets
GET /api/datasets-v2/?tags=pediatrics

# Find all cardiology datasets published by NHS
GET /api/datasets-v2/?tags=cardiology,NHS

# Search by name or description
GET /api/datasets-v2/?search=hospital

# Get faceted tag counts
GET /api/datasets-v2/available-tags/
# Returns: [{"tag": "pediatrics", "count": 15}, ...]
```

### Dependency Protection

Published datasets with dependents cannot be deleted:

**Scenario:**

1. Hospital A publishes "Preferred Specialists List"
2. Hospital B creates a custom version for their region
3. Hospital A tries to delete the original
4. ❌ Deletion blocked: "Cannot delete published dataset that has custom versions created by others"

**Why:**

- Protects users who depend on your data
- Prevents breaking existing surveys
- Encourages stable, reliable shared datasets

**You can still:**

- ✅ Edit the dataset
- ✅ Update options
- ✅ Change description and tags

## User Workflows

### For Survey Creators

**Using existing datasets:**

1. Add a dropdown question to your survey
2. Check "Use prefilled options"
3. Browse available datasets (filter by tags if needed)
4. Select a dataset and click "Load Options"
5. Customize further if needed

**Creating custom datasets:**

1. Navigate to Dataset Management in Django Admin
2. Click "Add Dataset"
3. Set Category to "User Created"
4. Enter your options
5. Add tags for discoverability
6. Save - immediately available in surveys

**Creating from templates:**

1. Find a global dataset that's close to what you need
2. Use "Create Custom Version" action
3. Modify the options
4. Save with a descriptive name
5. Use in your surveys

### For Data Curators

**Publishing a new dataset:**

1. Create a high-quality, well-documented dataset
2. Add descriptive tags
3. Write a clear description explaining the use case
4. Review all options for accuracy
5. Publish globally
6. Monitor usage and feedback

**Maintaining published datasets:**

1. Keep data up-to-date
2. Respond to user feedback
3. Add versioning notes to description
4. Consider creating new versions for major changes

### For Platform Administrators

**Managing NHS DD datasets:**

```bash
# Seed initial NHS DD datasets
docker compose exec web python manage.py seed_nhs_datasets

# Update as needed
docker compose exec web python manage.py update_nhs_datasets
```

**Managing external API datasets:**

```bash
# Initial setup
docker compose exec web python manage.py seed_external_datasets
docker compose exec web python manage.py sync_external_datasets

# Schedule daily sync
0 4 * * * cd /app && python manage.py sync_external_datasets
```

## Permissions Summary

| Action | Individual Users | Org VIEWER | Org CREATOR/ADMIN |
|--------|-----------------|------------|-------------------|
| View global datasets | ✅ | ✅ | ✅ |
| View org datasets | ❌ | ✅ (own org) | ✅ (own org) |
| Create datasets | ✅* | ❌ | ✅ |
| Edit own datasets | ✅ | ❌ | ✅ (own org) |
| Delete own datasets | ✅** | ❌ | ✅ (own org)** |
| Create custom versions | ✅* | ❌ | ✅ |
| Publish globally | ✅* | ❌ | ✅ (own org) |

*Individual users can create, customize, and publish datasets. In future, this will require a pro account.

**Cannot delete if published with dependents from other organizations

## Best Practices

### When Creating Datasets

1. **Use descriptive names**: "London Teaching Hospitals" not "Hospital List 1"
2. **Add meaningful tags**: Help others discover your dataset
3. **Write clear descriptions**: Explain the purpose and source
4. **Start from templates**: Build on existing quality data
5. **Keep it focused**: One dataset per concept (don't mix hospitals and specialties)

### When Publishing

1. **Verify accuracy**: Double-check all entries before publishing
2. **Document sources**: Note where data came from
3. **Add version info**: Include date or version in description
4. **Use appropriate tags**: Make it discoverable
5. **Consider maintenance**: Can you keep it updated?

### When Using Datasets

1. **Check recency**: Look at last updated date
2. **Read descriptions**: Understand the scope and limitations
3. **Use tags to filter**: Find exactly what you need
4. **Create custom versions**: Don't modify shared datasets directly
5. **Provide feedback**: Contact dataset creators with suggestions

## API Reference

For developers and advanced users:

### List Datasets

```bash
GET /api/datasets-v2/
GET /api/datasets-v2/?tags=pediatrics,NHS
GET /api/datasets-v2/?search=hospital
GET /api/datasets-v2/?category=user_created
```

### Create Custom Version

```bash
POST /api/datasets-v2/{key}/create-custom/
{
  "name": "My Custom Version",
  "organization": 123
}
```

### Publish Dataset

```bash
POST /api/datasets-v2/{key}/publish/
```

### Get Tag Counts

```bash
GET /api/datasets-v2/available-tags/
```

For complete API documentation, see:

- **[Dataset Sharing and Customization](dataset-sharing-and-customization.md)** - Detailed technical guide
- **[API Reference](api.md)** - Complete API documentation
- **[Using the API](using-the-api.md)** - Authentication and usage guide

## Related Documentation

- **[Prefilled Datasets Quick Start](prefilled-datasets-quickstart.md)** - Getting started guide
- **[Prefilled Datasets Setup](prefilled-datasets-setup.md)** - Detailed setup instructions
- **[Adding External Datasets](adding-external-datasets.md)** - Developer guide
- **[Authentication and Permissions](authentication-and-permissions.md)** - Security and access control

## Getting Help

If you have questions about dataset management:

1. Check the [documentation](README.md)
2. Review the [API examples](using-the-api.md)
3. Ask in [Discussions](https://github.com/eatyourpeas/checktick/discussions)
4. Report issues in [Issues](https://github.com/eatyourpeas/checktick/issues)
