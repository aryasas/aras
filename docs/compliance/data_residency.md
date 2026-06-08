# Data Residency Policy

Aras supports region-based data residency to comply with local regulations (e.g. GDPR in EU, PDPA in SEA).

## Region Pinning
Tenants are assigned a `region` during provisioning. This region determines the physical database target where the tenant's data is stored.

### Supported Regions
- `sea`: Southeast Asia (Default)
- `eu`: European Union
- `us`: United States

## DB Target Mapping
The framework selects the DB target based on the environment configuration:
- `TENANT_DB_HOST_{REGION}`: If specified, the provisioner uses this host for the given region.
- Default fallback: If no region-specific host is found, the default `TENANT_DB_HOST` or `DB_HOST` is used.

**Current Limitation:** In single-target deployments (e.g. a single RDS instance), all regions map to the same physical host. Region pinning in this state acts as metadata for future migration or governance but does not provide physical isolation between regions.

## Cross-Border Data Transfer
Data is stored in the region selected at signup. Cross-border transfers occur only under the following conditions:
1. **Explicit Consent**: The user has consented to the transfer as part of the terms of service.
2. **Adequacy Decision**: The transfer is to a country with an adequate level of protection as determined by relevant authorities.
3. **Standard Contractual Clauses (SCCs)**: Transfers are governed by approved SCCs.

## Regional Governance
- **EU**: Data residency enforced via `eu` region pinning on `saas_subscription` and `tenant_registry`.
- **SEA**: Defaults to `sea` region, stored locally in approved data centers.
