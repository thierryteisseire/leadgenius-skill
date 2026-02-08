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

### 7. Ecosystem & Connectivity
- **Webhooks**: Register listeners for real-time event notifications with `POST /webhooks`.
- **Integrations**: Manage sync status for external CRMs (HubSpot, Salesforce) with `GET /integrations`.

## Technical Reference

### Base URL
All requests are relative to: `/api/agent` (e.g. `https://your-domain.com/api/agent/leads`)

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

#### 4. Insights
```bash
# Show pipeline health
python3 scripts/lgp.py pipeline
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

