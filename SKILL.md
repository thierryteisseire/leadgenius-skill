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

### 2. Campaign Operations
- **Overview**: List all active ABM campaigns with `GET /campaigns`.
- **Performance**: Monitor ROI with `GET /campaigns/{id}/metrics`.
- **Creation**: Launch new initiatives with `POST /campaigns`.

### 3. Targeted ABM
- **Account Lists**: Manage high-value targets with `GET /target-accounts`.
- **Scoring**: Update account intent and fit scores with `PUT /target-accounts/{id}/score`.

## Technical Reference

### Base URL
All requests are relative to: `/api/agent` (e.g. `https://your-domain.com/api/agent/leads`)

### Authentication
Include your API key in the headers:
```http
X-API-Key: lgp_your_secret_key
# OR
Authorization: Bearer lgp_your_secret_key
```

### Reference Material
- **OpenAPI Spec**: See [openapi.json](references/openapi.json) for a full list of endpoints, parameters, and schemas.
- **Documentation**: A detailed HTML guide is available at `/api/agent/docs`.

### Helper Scripts
Use [scripts/api_call.py](scripts/api_call.py) to make authenticated requests from the command line.

## Guardrails
- **Rate Limits**: Default limit is 60 requests per minute.
- **Batching**: Limit batch lead creation to 100 per request.
- **Permissions**: Ensure your API key has the required scope (Read/Write/Admin).
