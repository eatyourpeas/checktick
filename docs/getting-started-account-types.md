# Account Types and Organization Setup

This guide explains the differences between individual and organization accounts in CheckTick, helping you choose the right option for your needs.

## Account Types Overview

CheckTick offers two types of accounts, each designed for different use cases:

### 👤 - Individual Account

**Best for:** Personal research, small studies, individual clinicians

***Features***

- Create and manage your own surveys
- Full control over your data and encryption keys
- Simple setup and management
- No collaboration features
- You are responsible for all encryption key management

***Key Characteristics***

- **Data ownership:** You own all surveys and responses
- **Key management:** You manage encryption keys yourself
- **Recovery:** If you lose encryption keys, data cannot be recovered
- **Collaboration:** No team features - surveys are private to you
- **Cost:** Free for personal use

### 🏢 - Organization Account

**Best for:** Healthcare teams, research institutions, collaborative projects

***Features***

- Create an organization with multiple team members
- Collaborative survey creation and management
- Role-based access control (Admin, Creator, Viewer)
- Organization-level encryption key management
- Key recovery and backup services

***Key Characteristics***

- **Data ownership:** Organization owns surveys, members can access based on roles
- **Key management:** Organization can recover lost encryption keys
- **Recovery:** Admins can help recover access to encrypted data
- **Collaboration:** Multiple users can work on surveys together
- **Audit trail:** All actions are logged for compliance

## Choosing the Right Account Type

### Choose Individual Account If

- You're conducting personal research
- You work independently
- You don't need to share surveys with others
- You're comfortable managing encryption keys yourself
- You want the simplest setup experience

**Example use cases:**

- Personal health tracking
- Small-scale research projects
- Learning to use CheckTick
- Independent consultants

### Choose Organization Account If

- You work as part of a healthcare team
- Multiple people need access to surveys
- You need institutional oversight
- Data recovery is important for compliance
- You need audit trails for healthcare regulations

**Example use cases:**

- Hospital departments
- Research institutions
- Healthcare practices with multiple staff
- Clinical trial teams
- Public health organizations

## Organization Roles Explained

When you create or join an organization, you'll have one of these roles:

### Admin

- **Full control** over the organization
- Can add/remove members and change their roles
- Can access all organization surveys
- Can manage organization settings
- Can recover encryption keys for the organization

### Creator

- Can create and manage their own surveys
- Can be granted access to specific surveys by admins
- Cannot manage organization members
- Can collaborate on surveys they're invited to

### Viewer

- Read-only access to surveys they're invited to
- Can view survey results and responses
- Cannot create or edit surveys
- Cannot manage organization members

## Security and Encryption Differences

### Individual Account Security

**Encryption Model:**

- You generate and manage all encryption keys
- Keys are derived from passwords you create
- Recovery phrases provided for key backup
- **No external recovery options**

> **Risk Considerations:**
>
> - ⚠️ Lost passwords + recovery phrases = permanent data loss
> - ⚠️ No administrative support for key recovery
> - ⚠️ All security responsibility on individual user
>

### Organization Account Security

**Encryption Model:**

- Organization manages master encryption keys
- Individual survey keys derived from organization keys
- Administrative key escrow and recovery
- **Organization can recover lost access**

**Enhanced Security Features:**

- Professional key management
- Administrative oversight
- Audit logging for compliance
- Backup and recovery procedures
- Role-based access controls

## Upgrading from Individual to Organization

If you start with an individual account, you can upgrade to an organization account later:

### Upgrade Process

1. **Go to your Profile page**
2. **Click "Upgrade to Organization"**
3. **Choose your organization name**
4. **You become the organization admin**
5. **Your existing surveys transfer to the organization**

### What Happens During Upgrade

**Your surveys:**

- All existing surveys are preserved
- Survey data and responses remain intact
- You maintain full access as organization admin
- Encryption keys are migrated to organization management

**Your access:**

- You become the organization admin
- You can now invite team members
- You can manage organization settings
- You get administrative key recovery options

**Team building:**

- Invite colleagues via email
- Assign appropriate roles (Admin, Creator, Viewer)
- Share existing surveys with team members
- Collaborate on new surveys

### Important Notes About Upgrading

- ⚠️ **Upgrade is permanent** - you cannot downgrade back to individual
- **No data loss** - all your surveys and responses are preserved
- **Enhanced security** - organization key management is more robust
- **Better compliance** - audit trails and administrative oversight

## Getting Help

### For Individual Accounts

- Use the in-app help system
- Check the [User Documentation](./getting-started.md)
- Join the [Community Discussions](https://github.com/eatyourpeas/checktick/discussions)

### For Organization Accounts

- All individual account resources, plus:
- Organization admin training materials
- [User Management Guide](./user-management.md)
- [Authentication Setup](./authentication-and-permissions.md)
- Priority support for compliance questions

## Compliance Considerations

### Individual Accounts

- **HIPAA/GDPR:** User is responsible for compliance
- **Data retention:** User manages all data lifecycle
- **Audit trails:** Limited to basic system logs
- **Key management:** No institutional oversight

### Organization Accounts

- **HIPAA/GDPR:** Organization-level compliance support
- **Data retention:** Administrative controls and policies
- **Audit trails:** Comprehensive logging for all actions
- **Key management:** Professional-grade key escrow and recovery

## Next Steps

### Ready to Get Started?

**For Individual Account:**

1. Complete the signup process
2. Read the [Getting Started Guide](./getting-started.md)
3. Create your first survey

**For Organization Account:**

1. Complete the signup process with organization option
2. Set up your organization name
3. Read the [User Management Guide](./user-management.md)
4. Invite your team members
5. Create collaborative surveys

### Questions?

Visit our [Community Discussions](https://github.com/eatyourpeas/checktick/discussions) or check the [FAQ section](./getting-started.md#frequently-asked-questions) for common questions about account types.
