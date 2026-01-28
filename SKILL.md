---
name: leadgenius-api
description: Comprehensive toolset for interacting with LeadGenius Pro Agent APIs. Use for managing ABM campaigns, lead lifecycle, AI enrichment, target accounts, outreach sequences, and system integrations. Supports listing, creating, and updating resources via the LeadGenius RESTful API.
---

# LeadGenius Pro Agent API Skill

This skill allows agents to manage the full lead lifecycle and ABM campaigns in LeadGenius Pro.

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

### 3. Client Management
- **List Clients**: `GET /clients` to list workspace clients and ensure correct data mapping.

### 4. Statistics & Reporting
- **Lead Distribution Stats**: When asked for "stats" or "lead counts", follow this workflow:
  1. Call `GET /clients` to retrieve the list of active clients.
  2. For each relevant client, call `GET /leads?client_id={client_id}&pageSize=1` to retrieve the `totalItems` count from the pagination metadata.
  3. Aggregate the data and present a clear table showing **Client Name**, **Client ID**, and **Lead Count**.
  4. Identify any "Orphaned" leads (leads with no `client_id`) by calling `GET /leads` without a filter.

## Technical Reference

### Base URL
Production: `https://last.leadgenius.app/api/agent`

### Authentication
Include your API key in the `Authorization` header:
```http
Authorization: Bearer lgp_your_secret_key
```

### Reference Material
- **OpenAPI Spec**: See [openapi.json](references/openapi.json) for full schema details.
- **Helper Scripts**: 
  - [scripts/api_call.py](scripts/api_call.py): General authenticated requests.
  - [scripts/lead_distribution.py](scripts/lead_distribution.py): Aggregate and audit leads per client (useful for debugging visibility).

## Troubleshooting & Tips

### Organization Mismatch (Leads or Clients not visible)
If the skill returns 0 leads or 0 clients but you see them in the dashboard:
1. **Check API Key Context**: API keys are organization-specific. Ensure you generated your key in the correct workspace.
2. **Personal vs Company Orgs**: Many users have a personal sandbox. Verify the "Company ID" in your settings matches the one where the data was loaded.

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
