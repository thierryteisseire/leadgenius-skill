---
name: leadgenius-api
description: Comprehensive toolset for interacting with LeadGenius Pro Agent APIs. Use for managing ABM campaigns, lead lifecycle, AI enrichment, target accounts, outreach sequences, and system integrations. Supports listing, creating, and updating resources via the LeadGenius RESTful API.
---

# LeadGenius Pro Agent API Skill

This skill allows agents to manage the full lead lifecycle and ABM campaigns in LeadGenius Pro.

## 🏁 Getting Started: Infrastructure Discovery

**CRITICAL**: At the start of any session or when asked to list "leads", "stats", or "clients", you **MUST** run the following command first. The REST API often returns limited data; this script provides the full, aggregated truth:

```bash
# Recommended First Command
python3 scripts/rest_lead_stats.py
```

## ⚠️ Critical: Dashboard Visibility Rules

To ensure resources (campaigns, leads) are visible in the LeadGenius Pro dashboard, you MUST follow these mapping rules:

1. **Client Identification**: 
   - Use `client_id` (a string identifier like `client_acme_inc`) in both Campaign and Lead creation.
   - Without a valid `client_id`, items may appear as "Orphaned" or be hidden from specific workspace views.

2. **Lead Naming**:
   - Always provide `firstName`, `lastName`, `fullName`, and `contactName`.
   - The UI primarily uses `fullName` and `contactName` for rendering lists. If these are missing, leads might appear empty.

3. **Multi-Tenancy**:
   - Resources are automatically isolated by the `company_id` associated with your API Key.
   - If you create resources but can't see them, verify that your API Key was generated within the correct organization context.

## Core Workflows

### 1. Lead Management
- **Find Leads**: `GET /leads` (supports `campaignId`, `client_id`, and `email` filters).
- **Create Leads**: `POST /leads` or `POST /leads/batch`.
- **Update Status**: `PUT /leads/{id}/status` (Transitions: `new` -> `qualified` -> `contacted` -> `converted`).

### 2. Campaign Operations
- **Launch Campaign**: `POST /campaigns`. Set `status` to `active` immediately if you want it to appear in active lists.
- **Metrics**: `GET /campaigns/{id}/metrics` to track performance.

### 3. Data Synchronization (Indexing)
If you notice that `GET /leads` returns fewer results than `rest_lead_stats.py`, the REST search index needs to be synced:
- **Trigger Sync**: Run `python3 scripts/index_leads.py`. This touches leads via GraphQL to force them into the REST search engine.

## Technical Reference

### Base URL
Production: `https://last.leadgenius.app/api/agent`

### Authentication
Include your API key in the `Authorization` header. The skill automatically looks for `LEADGENIUS_API_KEY` or `LGP_API_KEY` in the project's `.env` file.
```http
Authorization: Bearer lgp_your_secret_key
```

### Reference Material
- **OpenAPI Spec**: See [openapi.json](references/openapi.json) for full schema details.
- **Helper Scripts**: 
  - [scripts/api_call.py](scripts/api_call.py): General authenticated requests.
  - [scripts/rest_lead_stats.py](scripts/rest_lead_stats.py): Aggregate leads per client using the REST API (fastest for small/medium datasets).
  - [scripts/lead_distribution.py](scripts/lead_distribution.py): Aggregate and audit leads per client using GraphQL.

## Troubleshooting & Tips

### Large Datasets
If a client has a massive number of leads (e.g., >1000), listing leads might require multiple paginated calls. Use the `nextToken` in the API response to scroll through records efficiently.

### Orphaned Leads
Leads without a `client_id` or `campaignId` are considered "Orphaned". They are still in the system (visible via `GET /leads`) but won't appear in client-specific dashboards. Use `lead_distribution.py` to identify them.

### UI Sync
After creating leads via the API, the dashboard might take a few seconds to refresh. If leads don't appear, try a hard refresh (Cmd+R) or clear your local cache.

## Guardrails
- **Batch Limits**: Max 100 leads per batch request.
- **Rate Limits**: 60 requests/minute default.
- **Permission Scopes**: Standard keys have `read` and `write`. `admin` is required for key management.
