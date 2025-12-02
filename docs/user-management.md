---
title: User Management
category: configuration
priority: 3
---

This document explains how organisation, team, and survey-level user management works, including roles, permissions, invitations, and security protections.

## Account Types

There are three types of user contexts in the system:

- **Individual users**: Users who create surveys without an organisation or team. Individual users can only create and manage their own surveys and **cannot share surveys or invite collaborators**.
- **Team members**: Users who belong to a team. Teams provide collaboration for 5-20 users with shared billing and role-based access.
- **Organisation members**: Users who belong to an organisation. Organisations can host both individual members AND teams, with permissions managed by organisation admins.

## Team Size Limits

Teams have capacity limits based on their subscription tier:

| Team Size | Maximum Members |
|-----------|-----------------|
| Small     | 5 members       |
| Medium    | 10 members      |
| Large     | 20 members      |

**Note**: Pending invitations count toward the team capacity limit. For example, a Small team with 3 members and 2 pending invitations has reached its 5-member limit.

**Organisation teams**: Organisations can create unlimited teams with unlimited members.

## Roles and Scopes

There are three membership scopes with separate roles:

### Organisation Membership (OrganizationMembership)

- **admin**: Full administrative control over the organisation context, including managing org members, teams, and surveys within the organisation.
- **creator**: Can create and manage their own surveys; read-only visibility to organisation content is up to app policy, but creators do NOT manage org members or teams.
- **viewer**: Read-only role for organisation context where applicable; cannot manage org members or teams.
- **data_custodian**: Specialised role for data governance responsibilities.

### Team Membership (TeamMembership)

- **admin**: Can manage team members, settings, and all team surveys. If the team is within an organisation, organisation admins also have admin rights.
- **creator**: Can create and edit surveys within the team.
- **viewer**: Read-only access to team surveys.

**Team hierarchy**: Organisation admin > Team admin > Survey owner

**Unique constraint**: Each user can only have one role per team `(team, user)`.

**Role persistence**: Team roles remain intact if a team migrates to an Organisation.

### Survey Membership (SurveyMembership)

**Only available for organisation surveys**

- **creator**: Can manage members for that specific survey and edit the survey.
- **viewer**: Can view the survey content and results according to app policy; cannot manage survey members.

## Additional Implicit Authorities

- **Survey owner**: For organisation/team surveys, always has full control over the survey, including member management for that survey.
- **Organisation admin**: Has admin rights for all surveys that belong to their organisation, including surveys in teams hosted by the organisation. Has supreme access.
- **Team admin**: Has admin rights for surveys within their team. Can manage team members and team surveys.

## Single-Organisation Model

- A user can be an ADMIN of at most one organisation. The "User management" hub focuses on that single org context.
- A user can be an ADMIN of multiple teams.
- A user can have multiple roles simultaneously: PRO account + team member + organisation member.

## Permission Matrix (Summary)

- **Manage org members** (add/update/remove): Organisation admin only
- **Manage team members** (add/update/remove): Team admin OR organisation admin (if team is in their org)
- **Manage survey members** (add/update/remove): **Organisation/team surveys only** - Survey owner, organisation admin (if applicable), team admin (if applicable), or survey creator for that survey
- **View survey**: Owner, org admin (if applicable), team admin (if applicable), any survey member (creator/viewer)
- **Individual users**: Cannot share surveys or manage survey members

## Guardrails

- Organisation admins cannot remove themselves from their own admin role via the SSR UI or the API. Attempts are rejected.
- Individual users (surveys without organisation or team) cannot access user management endpoints or share their surveys.
- SSR UI supports email-based lookup and creation for convenience. The API endpoints expect explicit user IDs for membership resources; scoped user creation endpoints exist to create a user in a given org, team, or survey.

## Inviting Users

When adding a user to an organisation or team, the system handles two scenarios:

### Existing Users

If the email address belongs to an existing user account, they are added immediately with the specified role. The user will see the organisation/team in their dashboard on their next login.

### New Users (Invitation System)

If the email address does not match any existing account, an **invitation** is sent:

1. **Invitation email**: The user receives a branded email inviting them to join the organisation or team
2. **Signup link**: The email contains a link to create an account
3. **Automatic membership**: When the user signs up with that email address, they are automatically added to the organisation/team with the invited role
4. **Expiration**: Invitations expire after 7 days

### Managing Pending Invitations

The User Management Hub displays pending invitations alongside existing members. Admins can:

- **Resend**: Send the invitation email again (useful if the original was missed)
- **Cancel**: Remove the pending invitation

Pending invitations are shown with a warning indicator and include:
- The invited email address
- The role they will be assigned
- How long ago the invitation was sent
- Resend and Cancel buttons

### Capacity and Invitations

For teams with size limits:
- Pending invitations count toward the team capacity
- You cannot invite more users than your remaining capacity
- Example: A Small team (5 max) with 3 members and 1 pending invitation can only invite 1 more user

### Invitation Models

The system uses two invitation models:

- **TeamInvitation**: For team-level invitations
- **OrgInvitation**: For organisation-level invitations

Both track: email, role, invited_by, created_at, expires_at, and accepted_at (set when the user signs up).

## SSR Management Pages

**Note**: User management pages are only accessible for organisation/team surveys. Individual users cannot share their surveys or access these pages.

### User Management Hub: `/surveys/manage/users/`

Shows:

1. **Organisation section** (if you're an org admin):
   - Your organisation and all its members
   - Quick-add form to add users to the organisation by email and role
   - Pending invitations with resend/cancel options
   - View all teams within the organisation

2. **Teams you manage section** (if you're a team admin):
   - All teams where you have admin role
   - Add/remove team members
   - Assign roles to team members
   - View team capacity (e.g., 5/10/20 members) including pending invitations
   - Pending invitations with resend/cancel options

3. **Users by survey section**:
   - Shows surveys and their members
   - Quick-add form to assign users to surveys by email and role

Actions:

- Prevents an org admin from removing themselves as an admin
- Sends invitation emails when adding users who don't have accounts
- All actions are audit-logged
- Shows UK spelling: "Organisation" throughout

### Organisation Users: `/surveys/org/<org_id>/users/`

- Admins can add or update members by email, change roles, and remove users
- Non-admins receive 403
- Actions are audit-logged

### Survey Users: `/surveys/{slug}/users/`

- **Only available for organisation surveys**. Individual users cannot access this page.
- Owners, org admins (if the survey belongs to their org), and survey creators can add/update/remove survey members.
- Survey viewers see a read-only list.
- Actions are audit-logged.

## API endpoints

Authentication: All endpoints below require JWT. Include "Authorization: Bearer <access_token>".

### Organization memberships

- List: GET /api/org-memberships/
- Create: POST /api/org-memberships/
- Update: PUT/PATCH /api/org-memberships/{id}/
- Delete: DELETE /api/org-memberships/{id}/

Scope and permissions:

- Queryset is restricted to organizations where the caller is an admin.
- Create/Update/Delete require admin role in the target organization.
- Delete: additionally prevents an org admin from removing their own admin membership.
- Unauthorized or out-of-scope access returns 403 Forbidden. Missing/invalid JWT returns 401 Unauthorized.

Serializer fields:

- id, organization, user, username (read-only), role, created_at (read-only)

### Survey memberships

**Note**: Survey memberships are only available for organization surveys. Individual users cannot create or manage survey memberships.

- List: GET /api/survey-memberships/
- Create: POST /api/survey-memberships/
- Update: PUT/PATCH /api/survey-memberships/{id}/
- Delete: DELETE /api/survey-memberships/{id}/

Scope and permissions:

- Queryset contains only memberships for surveys the caller can view (owner, org-admin for the survey's org, or the caller is a member of the survey).
- Create/Update/Delete require manage permission on the survey (owner, org admin for the survey's org, or survey creator).
- **Individual users (surveys without organization) will receive 403 Forbidden when attempting to manage memberships.**
- Unauthorized or out-of-scope access returns 403; missing/invalid JWT returns 401.

Serializer fields:

- id, survey, user, username (read-only), role, created_at (read-only)

### Scoped user creation

To support flows where an admin/creator wants to add a person who may not yet exist:

- Create user within an org context (org admin only):
  - POST /api/scoped-users/org/{org_id}/create

- Create user within a survey context (survey owner/org admin/creator):
  - POST /api/scoped-users/survey/{survey_id}/create
  - **Only available for organization surveys. Individual users will receive 403 Forbidden.**

Request schema:

- email (string, required)
- password (string, optional)

Behavior:

- If a user with the given email already exists, it is reused; otherwise a new user is created with username=email. Password is required only when creating a new user (optional if reusing).
- On success, returns the user's id/username/email and adds them as a Viewer in the specified scope by default (org Viewer or survey Viewer).
- Permission checks mirror the membership rules above. Unauthorized attempts receive 403.

Note: The SSR UI allows searching by email and will create or reuse users accordingly, with audit logging. If you need similar behavior via API, use the scoped user creation endpoints described here.

## Audit logging

Membership actions performed via the SSR UI are recorded in AuditLog with:

- actor, scope (organization or survey), organization/survey context, action (add/update/remove), target_user, metadata (e.g., role), timestamp

These records enable traceability of who changed which memberships and when.

## Security notes

- JWT is required for API access. Missing/invalid tokens result in 401; valid tokens without sufficient privileges result in 403.
- SSR uses session auth with CSRF protection and enforces permissions via centralized helpers.
- Organization admins cannot remove themselves as admins via the UI or the API; requests to remove self-admin are rejected.
- Sensitive demographics remain encrypted per-survey and are unaffected by membership operations.

### Account Deletion Security

For security and data integrity reasons, account deletion is restricted:

- **User account deletion**: Only superusers can delete user accounts through the Django Admin interface (`/admin/`).
- **Regular users cannot delete their own accounts** to prevent accidental data loss and maintain audit trails.
- **Organization deletion**: Only superusers can delete organizations through the Django Admin interface.
- **Survey deletion**: Survey owners and organization admins can delete surveys they manage, following proper confirmation workflows.

**Rationale**: User and organization deletion can have cascading effects that permanently remove data belonging to multiple users. This restriction ensures:

1. **Data protection**: Prevents accidental loss of surveys and responses that may be shared with other users
2. **Audit compliance**: Maintains proper audit trails for account management actions
3. **Security**: Prevents malicious or compromised accounts from destroying organizational data
4. **Intentionality**: Ensures deletion decisions are made by administrators with full context

**For users needing account deletion**: Contact your system administrator, who can safely perform the deletion through the admin interface after confirming the impact on shared data.

## Testing

The test suite includes:

- JWT auth enforcement (missing/invalid tokens, refresh flow)
- API permission tests for list/detail/update/seed
- SSR portal tests for org/survey user management behaviors and permission boundaries

All tests are designed to ensure that protections are consistent and robust across SSR and API.
