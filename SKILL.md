---
name: leadgenius-api
description: Comprehensive toolset for interacting with LeadGenius Pro Agent APIs. Use for managing ABM campaigns, lead lifecycle, AI enrichment, target accounts, outreach sequences, and system integrations. Supports listing, creating, and updating resources via the LeadGenius RESTful API.
---

# LeadGenius Pro Agent API

This skill provides a comprehensive interface for interacting with the LeadGenius Pro Agent API.

## Core Workflows

### 1. Lead Management
- **Find Leads**: Use `GET /leads` to list contacts.
- **Enrich Leads**: Use `POST /enrichment/trigger` to start AI augmentation.
- **Update Status**: Use `PUT /leads/{id}/status` to track progress (New -> Qualified -> Contacted).
- **Batch Operations**: Create or delete multiple leads simultaneously with `POST /leads/batch` or `DELETE /leads/batch`.

### 2. Campaign Operations
- **Overview**: List all active ABM campaigns with `GET /campaigns`.
- **Performance**: Monitor ROI with `GET /campaigns/{id}/metrics`.
- **Creation**: Launch new initiatives with `POST /campaigns`.

### 3. Targeted ABM
- **Account Lists**: Manage high-value targets with `GET /target-accounts`.
- **Scoring**: Update account intent and fit scores with `PUT /target-accounts/{id}/score`.

### 4. Outreach & Engagement
- **Sequences**: List communication sequences with `GET /sequences`.
- **Enrollment**: Enroll leads into a specific sequence with `POST /sequences/{id}/enroll`.

### 5. Automation & Workflows
- **Custom Workflows**: Manage automated processes and agent handoffs with `GET /workflows`.
- **Status Jobs**: Monitor long-running processes (like enrichment or exports) with `GET /enrichment/status/{jobId}`.

### 6. Analytics & Insights
- **Pipeline Health**: Total visibility into conversion rates and pipeline velocity with `GET /analytics/pipeline`.

### 7. Maintenance & System Health
- **Bug Reporting**: Use `POST /maintenance/bugs` to report issues discovered by agents.
- **Enhancement Requests**: Use `POST /maintenance/enhancements` to suggest features.

### 8. Master Administration
- **Global Visibility**: List all companies and users across the platform (Admin only).
- **API Key Management**: Generate and rotate API keys for agent access.

## Technical Reference

### Base URL
The API uses separate root paths for different scopes:
- **Agent Scope (Default)**: `/api/agent` (e.g. `https://last.leadgenius.app/api/agent/leads`) 
- **Admin Scope**: `/api/admin` (e.g. `.../api/admin/companies`)
- **System Scope**: `/api` (e.g. `.../api/epsimo-auth`)

### Unified CLI (lgp.py)
The primary way to interact with LeadGenius is via the `lgp` CLI tool.

#### 1. Setup & Auth
```bash
python3 scripts/lgp.py auth --email your@email.com
```

#### 2. Manage Leads
```bash
# List leads
python3 scripts/lgp.py leads list

# Enrich specific leads
python3 scripts/lgp.py leads enrich --ids lead_1 lead_2
```

#### 3. Manage Campaigns
```bash
# List active campaigns
python3 scripts/lgp.py campaigns list

# Create a new campaign
python3 scripts/lgp.py campaigns create --name "Q3 Expansion"
```

#### 4. Insights & Analytics
```bash
# Show pipeline health for a specific period
python3 scripts/lgp.py pipeline --start 2026-01-01 --end 2026-02-08
```

#### 5. Maintenance & Support
```bash
# List and report bugs
python3 scripts/lgp.py maintenance bugs list
python3 scripts/lgp.py maintenance bugs report --desc "Enrichment fails on LinkedIn URLs"

# List and request enhancements
python3 scripts/lgp.py maintenance enhancements list
python3 scripts/lgp.py maintenance enhancements request --desc "Add support for Google Maps leads"
```

#### 6. API Key Generation
```bash
# Generate a new API Key (Requires active session)
python3 scripts/lgp.py generate-key --name "Production Agent" --desc "Key for main auto-agent"
```

#### 7. Global Administration (Admin Only)
```bash
# View system-wide data
python3 scripts/lgp.py admin companies
python3 scripts/lgp.py admin users
```

### Reference Material
- **API Reference**: See [api_reference.md](references/api_reference.md) for detailed endpoint descriptions.
- **OpenAPI Spec**: See [openapi.json](references/openapi.json) for machine-readable schemas.

### Helper Scripts
- **[scripts/lgp.py](scripts/lgp.py)**: Unified CLI for all common operations.
- **[scripts/api_call.py](scripts/api_call.py)**: Low-level utility for custom raw API requests.
- **[scripts/auth.py](scripts/auth.py)**: Standalone auth utility.



## Common Payloads

### Create Campaign
```json
{
  "name": "Q1 ABM Tech Giants",
  "description": "Targeting top 50 tech firms for SaaS expansion",
  "campaignType": "abm",
  "status": "active"
}
```

### Enrich Leads
```json
{
  "leadIds": ["lead_123", "lead_456"],
  "enrichmentType": "technographic",
  "priority": "high"
}
```

## Quick Start
To test your connection:
1. Set your API Key: `export LGP_API_KEY=lgp_your_key`
2. Fetch campaigns:
   ```bash
   python3 scripts/api_call.py GET /campaigns
   ```


## Guardrails
- **Rate Limits**: Default limit is 60 requests per minute.
- **Batching**: Limit batch lead creation to 100 per request.
- **Permissions**: Ensure your API key has the required scope (Read/Write/Admin).

