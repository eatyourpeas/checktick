---
title: "Access Audit Log"
category: dspt-4-managing-access
---

# Access Audit Log (Personnel & Infrastructure)

**Policy:** Comprehensive audit of all '{{ platform_name }}' staff accounts with access to NHS-related infrastructure.

## Audit Record: 29/12/2025

**Performed by:** [CTO Name] (SIRO)

| System | Account Found | Role | Status | Verified? |
| :--- | :--- | :--- | :--- | :--- |
| **Northflank** | [CTO Name] | Admin/SIRO | Active | ✅ |
| **Northflank** | [SIRO Name] | Admin/CTO | Active | ✅ |
| **GitHub** | [CTO Name] | Owner | Active | ✅ |
| **GitHub** | [SIRO Name] | Owner | Active | ✅ |
| **PostgreSQL** | `ct_prod_admin` | DB Admin | Active | ✅ (Rotated) |

### Audit Findings:

* **Leavers:** 0 staff departures in this period; no accounts required deactivation.
* **Inappropriate Access:** 0 instances of over-privileged access found.
* **MFA Check:** Confirmed MFA is active on 100% of administrative entry points.
* **Action Taken:** Rotated the primary database administration credentials as a proactive measure.

**Next Audit Due:** [Date + 3 Months]
