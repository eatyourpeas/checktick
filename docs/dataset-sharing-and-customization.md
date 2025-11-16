# Dataset Sharing and Customization

This document describes how users can create custom versions of global datasets, publish their datasets globally, and use tags for discovery.

## Overview

The dataset system supports:
- **Creating custom versions** from any global dataset
- **Publishing datasets globally** to share with all users
- **Tagging datasets** for better discovery and filtering
- **Retaining ownership** while sharing globally

## Creating Custom Versions

Users can create custom versions of any global dataset (NHS DD, External API, or user-published datasets) to modify for their organization's needs.

### Via API

```http
POST /api/datasets/{key}/create-custom/
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Our Custom Hospital List",
  "organization": 123  // Optional, defaults to user's first org
}
```

### Requirements

- User must be **ADMIN** or **CREATOR** in an organization
- Source dataset must be **global** (is_global=True)
- Creates a new dataset with `parent` pointing to the source

### What Happens

1. New dataset created with unique key: `{original_key}_custom_{org_id}_{timestamp}`
2. Copies all options from parent dataset
3. Inherits tags and format pattern
4. Owned by the user's organization
5. Marked as `is_custom=True`, `is_global=False`
6. Can be freely edited without affecting parent

### Example Workflow

```python
# User finds a global dataset they want to customize
GET /api/datasets/hospitals_england_wales/

# Create custom version
POST /api/datasets/hospitals_england_wales/create-custom/
{
  "name": "London Hospitals (Custom)"
}

# Response includes new dataset with unique key
{
  "key": "hospitals_england_wales_custom_5_1731744000",
  "name": "London Hospitals (Custom)",
  "parent": "hospitals_england_wales",
  "parent_name": "Hospitals (England & Wales)",
  "is_custom": true,
  "is_global": false,
  "organization": 5,
  "options": [...],  // Copy of parent options
  "is_editable": true
}

# Now edit the custom version
PATCH /api/datasets/hospitals_england_wales_custom_5_1731744000/
{
  "options": ["Royal London Hospital", "Guy's Hospital", ...]  // Modified list
}
```

## Publishing Datasets Globally

Organization admins/creators can publish their custom datasets to make them available to all users.

### Via API

```http
POST /api/datasets/{key}/publish/
Authorization: Bearer <token>
```

### Requirements

- User must be **ADMIN** or **CREATOR** in the dataset's organization
- Dataset must be **organization-owned** (not already global)
- Cannot publish NHS DD datasets (they're already global)

### What Happens

1. `is_global` set to `True`
2. `published_at` timestamp recorded
3. Organization reference **retained** for attribution
4. Dataset becomes visible to all users
5. Original organization retains edit rights

### Example Workflow

```python
# User creates a useful dataset in their org
POST /api/datasets/
{
  "key": "uk_cancer_centers",
  "name": "UK Cancer Treatment Centers",
  "description": "Comprehensive list of cancer treatment facilities",
  "tags": ["medical", "NHS", "oncology", "UK"],
  "options": [...]
}

# Verify it's useful and ready to share
PATCH /api/datasets/uk_cancer_centers/
{
  "description": "Peer-reviewed list of cancer treatment centers...",
  "tags": ["medical", "NHS", "oncology", "UK", "verified"]
}

# Publish globally
POST /api/datasets/uk_cancer_centers/publish/

# Now all users can see and create custom versions
# Organization that published it retains edit rights
```

## Tags and Discovery

Datasets can be tagged for better organization and discovery.

### Adding Tags

Tags are a simple list of strings:

```python
PATCH /api/datasets/{key}/
{
  "tags": ["medical", "NHS", "England", "primary-care"]
}
```

### Searching and Filtering

#### Filter by Tags

```http
GET /api/datasets/?tags=medical,NHS
```

This uses **AND logic** - returns datasets that have ALL specified tags.

#### Search by Name/Description

```http
GET /api/datasets/?search=hospital
```

#### Filter by Category

```http
GET /api/datasets/?category=user_created
```

#### Combine Filters

```http
GET /api/datasets/?tags=medical&search=london&category=user_created
```

### Faceted Filtering

Get all available tags with counts:

```http
GET /api/datasets/available-tags/

{
  "tags": [
    {"tag": "medical", "count": 45},
    {"tag": "NHS", "count": 38},
    {"tag": "England", "count": 25},
    {"tag": "Wales", "count": 12},
    ...
  ]
}
```

This enables building faceted search UIs where users can see tag popularity and filter interactively.

## Permissions Summary

### Reading Datasets

| User Type | Can See |
|-----------|---------|
| Anonymous | Global datasets only |
| Authenticated | Global datasets + their organization's datasets |

### Creating Custom Versions

| Requirement | Details |
|-------------|---------|
| Role | ADMIN or CREATOR in an organization |
| Source Dataset | Must be global (is_global=True) |
| Result | New dataset owned by user's organization |

### Publishing Datasets

| Requirement | Details |
|-------------|---------|
| Role | ADMIN or CREATOR in dataset's organization |
| Dataset Status | Must be organization-owned, not already global |
| Result | Dataset becomes global, organization retains attribution and edit rights |

### Editing Datasets

| Dataset Type | Who Can Edit |
|--------------|--------------|
| NHS DD | No one (read-only) |
| External API | No one (synced from API) |
| Platform Global (no org) | Superusers only |
| Published Global (has org) | ADMIN/CREATOR in original organization |
| Organization-owned | ADMIN/CREATOR in that organization |

## API Endpoints Reference

### List Datasets (with filtering)

```http
GET /api/datasets/
  ?tags=medical,NHS           # Filter by tags (AND logic)
  &search=hospital            # Search name/description
  &category=user_created      # Filter by category
```

### Get Available Tags

```http
GET /api/datasets/available-tags/
```

### Create Custom Version

```http
POST /api/datasets/{key}/create-custom/
{
  "name": "Optional custom name",
  "organization": 123  // Optional
}
```

### Publish Dataset

```http
POST /api/datasets/{key}/publish/
```

### Update Dataset (including tags)

```http
PATCH /api/datasets/{key}/
{
  "name": "Updated name",
  "description": "Updated description",
  "tags": ["new", "tags", "list"],
  "options": [...]
}
```

## Response Fields

```json
{
  "key": "dataset_key",
  "name": "Dataset Name",
  "description": "Description text",
  "category": "user_created",
  "source_type": "manual",
  "reference_url": "",
  "is_custom": true,
  "is_global": false,
  "organization": 123,
  "organization_name": "Org Name",
  "parent": "parent_key",
  "parent_name": "Parent Dataset Name",
  "options": [...],
  "format_pattern": "CODE - NAME",
  "tags": ["tag1", "tag2"],
  "created_by": 456,
  "created_by_username": "jdoe",
  "created_at": "2025-11-16T10:00:00Z",
  "updated_at": "2025-11-16T11:00:00Z",
  "published_at": null,
  "version": 1,
  "is_active": true,
  "is_editable": true,
  "can_publish": false
}
```

## Best Practices

### For Creating Custom Versions

1. **Start from global datasets** - Don't recreate standard lists
2. **Name descriptively** - Make it clear what's different
3. **Document changes** - Use description to explain modifications
4. **Tag appropriately** - Include inherited tags + custom ones

### For Publishing Datasets

1. **Verify quality** - Ensure data is accurate and complete
2. **Add comprehensive tags** - Make it discoverable
3. **Write clear descriptions** - Explain what the dataset contains
4. **Set format pattern** - Help users understand the data structure
5. **Test first** - Use within your organization before publishing

### For Tagging

1. **Be consistent** - Use standard terms (e.g., "NHS" not "nhs" or "N.H.S.")
2. **Be specific** - Include category, region, specialty
3. **Don't over-tag** - 3-7 tags is usually sufficient
4. **Think about search** - What would users look for?

Example good tagging:
```json
{
  "tags": ["medical", "NHS", "England", "primary-care", "GP-practices"]
}
```

Example poor tagging:
```json
{
  "tags": ["data", "list", "stuff", "important", "new", "2025", "version-1"]
}
```

## Migration Guide

### Existing Datasets

All existing datasets have been migrated with:
- `published_at`: null (not published)
- `tags`: [] (empty list)

### Making Existing Datasets Discoverable

1. Add appropriate tags to your datasets:
   ```http
   PATCH /api/datasets/{key}/
   {
     "tags": ["medical", "NHS", "specialty"]
   }
   ```

2. If you want to share an org dataset, publish it:
   ```http
   POST /api/datasets/{key}/publish/
   ```

## Troubleshooting

### "Can only create custom versions of global datasets"

The source dataset is not global. Only global datasets can be customized. Check `is_global` field.

### "Dataset is already published globally"

The dataset is already public. You can't publish it again.

### "Only organization-owned datasets can be published"

Platform-wide global datasets (like NHS DD) can't be published because they're already global.

### "You must be an ADMIN or CREATOR in this organization"

You don't have the required role. Ask an organization admin to grant you ADMIN or CREATOR role.

### Tags not filtering correctly

Tags use AND logic, so `?tags=A,B` returns only datasets with BOTH tags A and B.
For OR logic, make separate requests or adjust your query.
