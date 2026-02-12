---
name: leadgenius-api
description: Comprehensive toolset for interacting with LeadGenius Pro APIs. Use for managing B2B leads, clients, companies, enrichment settings, AI-driven lead processing (enrichment, copyright, SDR AI), search history, webhooks, territory analysis, email services, and integrations. Supports Cognito JWT (cookies + Bearer) and API key authentication with multi-tenant data isolation.
---

# LeadGenius Pro API — Skill Reference

This skill provides a comprehensive interface for interacting with the **LeadGenius Pro API v1.1**.

> **Base URL:** `https://last.leadgenius.app/api`
> **Full Reference:** See [references/api_reference.md](references/api_reference.md)

---

## Authentication

LeadGenius supports three authentication methods, tried in order by `getAuthContext`:

| Priority | Method | How It Works | Use Case |
|----------|--------|--------------|----------|
| 1 | **Cognito Cookies** | Automatic via browser session (`next/headers` cookies) | Web app (frontend) |
| 2 | **Bearer JWT** ✨ | `Authorization: Bearer <accessToken>` header; JWT `sub` claim extracted as owner | **External scripts, agents, CLI tools** |
| 3 | **API Key** | `x-api-key: <key>` + `x-user-id: <sub>` headers | Bulk data extraction, service-to-service |

### Getting a JWT Token

```bash
# Option 1: Use the test/auth script
python3 scripts/auth.py --email your@email.com

# Option 2: Direct API call
curl -X POST https://last.leadgenius.app/api/auth \
  -H "Content-Type: application/json" \
  -d '{"username": "your@email.com", "password": "YourPassword"}'
```

**Response:**
```json
{
  "success": true,
  "tokens": {
    "accessToken": "eyJra...",
    "idToken": "eyJra...",
    "refreshToken": "eyJj...",
    "expiresIn": 3600
  }
}
```

Use `tokens.accessToken` as the Bearer token for all subsequent API calls. Tokens expire after 1 hour.

### Token Refresh

When your access token expires, use the refresh token to get a new one without re-authenticating:

```bash
curl -X POST https://last.leadgenius.app/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refreshToken": "<your-refresh-token>"}'
```

**Response:**
```json
{
  "success": true,
  "tokens": {
    "accessToken": "eyJra...",
    "idToken": "eyJra...",
    "refreshToken": "eyJj...",
    "expiresIn": 3600
  }
}
```

**Python Example:**
```python
import requests
import json
import time

def refresh_token(refresh_token):
    response = requests.post(
        "https://last.leadgenius.app/api/auth/refresh",
        json={"refreshToken": refresh_token}
    )
    return response.json()

def get_valid_token(auth_file="~/.leadgenius_auth.json"):
    with open(auth_file, 'r') as f:
        auth = json.load(f)

    # Check if token is expired (simple check)
    # In production, decode JWT and check exp claim
    try:
        # Make a test request
        response = requests.get(
            "https://last.leadgenius.app/api/clients",
            headers={"Authorization": f"Bearer {auth['token']}"}
        )
        if response.status_code == 401:
            # Token expired, refresh it
            new_tokens = refresh_token(auth['refresh_token'])
            auth['token'] = new_tokens['tokens']['accessToken']
            with open(auth_file, 'w') as f:
                json.dump(auth, f)
        return auth['token']
    except:
        return auth['token']
```

### Using Bearer JWT in API Calls

```bash
# All API calls use the accessToken in the Authorization header
curl -H "Authorization: Bearer <accessToken>" \
     -H "Content-Type: application/json" \
     https://last.leadgenius.app/api/clients
```

The `getAuthContext` middleware (`src/utils/apiAuthHelper.ts`) decodes the JWT, extracts the `sub` claim as the `owner`, and resolves the `company_id` for multi-tenant isolation — all automatically.

### Auth Credentials Storage

Tokens are saved to `~/.leadgenius_auth.json` by the auth scripts:
```json
{
  "token": "<accessToken>",
  "id_token": "<idToken>",
  "refresh_token": "<refreshToken>",
  "email": "your@email.com",
  "user_id": "<uuid-user-id>",
  "base_url": "https://last.leadgenius.app"
}
```

---

## Core Workflows (E2E Tested ✅)

The following operations have been validated end-to-end with the test suite.

### 1. Client Management ✅

All client operations are scoped by `company_id` (resolved from JWT).

| Operation | Method | Endpoint | Status |
|-----------|--------|----------|--------|
| List all clients | `GET` | `/api/clients` | ✅ Tested |
| Get single client | `GET` | `/api/clients?clientId=<id>` | ✅ Tested |
| Create client | `POST` | `/api/clients` | ✅ Tested (201) |
| Update client | `PUT` | `/api/clients` | ✅ Tested |
| Delete client | `DELETE` | `/api/clients?id=<id>` | ✅ Tested |
| Purge client + leads | `DELETE` | `/api/clients?id=<id>&purge=true` | ⚠️ See warning below |

#### Create Client Payload
```json
{
  "clientName": "Acme Corp",
  "companyURL": "https://acme.com",
  "description": "Enterprise client for B2B leads"
}
```

**Response (201):**
```json
{
  "success": true,
  "client": {
    "id": "edd5c738-...",
    "client_id": "acme-corp",
    "clientName": "Acme Corp",
    "companyURL": "https://acme.com",
    "description": "Enterprise client for B2B leads",
    "owner": "4428a4f8-...",
    "company_id": "company-177..."
  }
}
```

> ⚠️ **CRITICAL — Slug vs UUID ("Invisible Leads" Bug)**
> The client record has **TWO** identifiers:
> - `id` — The internal DynamoDB UUID (e.g. `edd5c738-...`). Used **only** for update/delete of the client record itself.
> - `client_id` — The human-readable **slug** (e.g. `acme-corp`, `historic-leads`). Used for **all lead operations**.
>
> **ALWAYS use the slug (`client_id`) when creating or querying leads.** The UI queries leads by slug. If you mistakenly use the UUID `id` as the lead's `client_id`, the leads will exist in the database but will be **invisible in the UI**.
>
> **Verification:** `GET /api/leads?client_id=<slug>&limit=1` — if it returns leads, the UI will show them too.

#### Update Client Payload
```json
{
  "id": "<dynamodb-id>",
  "clientName": "Updated Name",
  "description": "Updated description"
}
```

> ⚠️ **Purge Timeout Warning:** The `purge=true` flag on client deletion will time out if the client has more than ~1,000 leads. For large datasets, delete leads first using a concurrent batch deletion script (batches of 50 IDs), then delete the client record.

---

### 2. Lead Management ✅

Leads are stored as `EnrichLeads` in DynamoDB and are scoped by `client_id` and `company_id`.

| Operation | Method | Endpoint | Status |
|-----------|--------|----------|--------|
| List leads | `GET` | `/api/leads?client_id=<slug>&limit=100` | ✅ Tested |
| Create single lead | `POST` | `/api/leads` | ✅ Tested (201) |
| Create batch leads | `POST` | `/api/leads` (with `leads` array) | ⚠️ See warning below |
| Update single lead | `PUT` | `/api/leads` | ✅ Tested |
| Batch update leads | `PUT` | `/api/leads` (with `leads` array) | ✅ Tested |
| Delete single lead | `DELETE` | `/api/leads?id=<id>` | ✅ Tested |
| Batch delete leads | `DELETE` | `/api/leads` (with `ids` array body) | ✅ Tested |

> 🚨 **CRITICAL — Batch POST May Not Persist:**
> The batch endpoint (`POST /api/leads` with `{"leads": [...]}`) returns `201 Created` and reports a correct `created` count, but leads **may not be saved to the database**. This was discovered during production HubSpot imports (Feb 2026). **For reliable imports, always POST leads individually** (single object payload). Single-lead POST is confirmed 100% reliable. See [HUBSPOT_TO_LEADGENIUS.md](HUBSPOT_TO_LEADGENIUS.md) Bug #2 for details.
>
> 💡 **Batch Size Recommendation:** If using batch POST, use a batch size of **50 leads** per request. For maximum reliability, prefer **single-lead POST** with a 150ms delay between requests (~400 leads/min).

#### Create Single Lead Payload
```json
{
  "client_id": "acme-corp",
  "firstName": "John",
  "lastName": "Smith",
  "email": "john.smith@example.com",
  "companyName": "Acme Corp",
  "companyDomain": "acme.com",
  "title": "VP Engineering",
  "linkedinUrl": "https://linkedin.com/in/johnsmith"
}
```
> ⚠️ The `client_id` here is the **slug** (e.g. `acme-corp`), NOT the DynamoDB UUID. See the [Slug vs UUID warning](#1-client-management-) above.

#### Create Batch Leads Payload
```json
{
  "leads": [
    {
      "client_id": "acme-corp",
      "firstName": "Jane",
      "lastName": "Doe",
      "email": "jane@example.com",
      "companyName": "BatchCorp",
      "title": "CTO"
    },
    {
      "client_id": "acme-corp",
      "firstName": "Bob",
      "lastName": "Wilson",
      "email": "bob@example.com",
      "companyName": "BatchCorp",
      "title": "VP Sales"
    }
  ]
}
```

**Batch Response (201):**
```json
{
  "success": true,
  "created": 2,
  "skipped": []
}
```

#### Update Single Lead Payload
```json
{
  "id": "<lead-dynamodb-id>",
  "title": "Senior VP Engineering",
  "notes": "Updated via API"
}
```

#### Batch Update Payload
```json
{
  "leads": [
    { "id": "<id-1>", "notes": "Updated lead 1" },
    { "id": "<id-2>", "notes": "Updated lead 2" }
  ]
}
```

#### Batch Delete Payload (body)
```json
{
  "ids": ["<id-1>", "<id-2>"]
}
```

#### List Leads Query Parameters
- `client_id` (**required**) — The **slug** from the Client record (not the DynamoDB `id`)
- `limit` — 1 to 1000 (default: 100)
- `nextToken` — Pagination token

#### AI Fields & the Notes Catch-All Pattern

Structured AI fields (`aiLeadScore`, `aiQualification`, etc.) are persisted in the backend but **may not be visible** in the standard LeadGenius UI table view. To guarantee visibility and searchability, **aggregate all analytical data into the `notes` field** using Markdown formatting:

```python
# Recommended: Aggregate AI fields into Notes for visibility
lead["notes"] = f"""
## 🎯 AI SCORE: {row['aiLeadScore']} ({row['leadScore']}/100)

### 🧐 JUSTIFICATION
{row['justification']}

### 💡 STRATEGIC RECOMMENDATIONS
{row['recommendations']}

### 📝 SDR SYNTHESIS
{row['sdr_synthesis']}
""".strip()
```

This ensures all critical data is immediately visible in the lead detail view and searchable across the UI.

---

### 3. Bulk Data Extraction

High-volume extraction bypasses standard auth for raw GSI performance.

| Operation | Endpoint | Auth |
|-----------|----------|------|
| Bulk EnrichLeads | `GET /api/enrich-leads/list` | API Key |
| Bulk SourceLeads | `GET /api/source-leads/list` | API Key |

#### Bulk List Query Parameters
- `companyId` (required) — Multi-tenant isolation
- `clientId` (optional) — Filter by client. Use `ALL`/`DEFAULT` or omit for all
- `limit` (optional) — Default 1000, max 5000
- `nextToken` (optional) — Pagination token
- `fields` (optional) — Comma-separated field projection (reduces payload)

---

### 4. Company Management

| Operation | Endpoint | Auth |
|-----------|----------|------|
| Get Company | `GET /api/company` | JWT |
| Create Company | `POST /api/company` | JWT |
| Update Company | `PUT /api/company` | JWT (Owner/Admin) |

---

### 5. Search History

Track and manage lead search operations (e.g., Apify scraping runs).

| Operation | Endpoint | Auth |
|-----------|----------|------|
| Create Search History | `POST /api/search-history` | JWT / API Key |
| List Search History | `GET /api/search-history` | JWT |
| Update Search History | `PUT /api/search-history` | JWT |

#### List Query Parameters
- `client_id`, `status` (initiated/running/completed/failed), `icpId`, `category`, `limit`, `cursor`

#### Create Payload
```json
{
  "searchName": "Tech Companies in SF",
  "searchDescription": "Looking for SaaS companies",
  "searchCriteria": { "industry": "Technology", "location": "San Francisco" },
  "searchFilters": { "companySize": "50-200" },
  "client_id": "client-123",
  "clientName": "Acme Corp",
  "icpId": "icp-456",
  "icpName": "Enterprise SaaS",
  "apifyActorId": "actor-789",
  "category": "prospecting",
  "tags": ["enterprise", "saas"]
}
```

---

### 6. Webhook Management

Create and manage inbound webhooks for third-party integrations.

| Operation | Endpoint | Auth |
|-----------|----------|------|
| List Webhooks | `GET /api/webhook-workbench` | JWT / API Key |
| Create Webhook | `POST /api/webhook-workbench` | JWT / API Key |

**Supported Platforms:** `heyreach`, `woodpecker`, `lemlist`, `generic`

#### Create Webhook Payload
```json
{
  "name": "My Webhook",
  "platform": "heyreach",
  "description": "Webhook for lead capture",
  "platformConfig": "{\"field_mapping\": {}}",
  "client_id": "client-123"
}
```
Returns: `webhookUrl` with embedded secret key for the external platform to call.

---

### 7. Territory Workbench

Aggregated company-level analytics for territory planning.

| Operation | Endpoint | Auth |
|-----------|----------|------|
| List Companies | `GET /api/territory-workbench/companies` | JWT |
| Create/Update Company | `POST /api/territory-workbench/companies` | JWT |

#### List Query Parameters
- `client_id` (required), `sortBy`, `sortDirection`, `industry`, `minLeads`, `maxLeads`, `search`, `startDate`, `endDate`

---

### 8. Settings Management ⚙️

**Settings drive all Lead Processing endpoints.** Configure settings first, then trigger processing.

All settings endpoints require **JWT auth** and are scoped by `company_id`.

#### URL Settings (Enrichment Service URLs)
| Operation | Endpoint |
|-----------|----------|
| Get | `GET /api/settings/url` |
| Create | `POST /api/settings/url` |
| Update | `PUT /api/settings/url` |

Available URL/key pairs: `companyUrl`, `emailFinder`, `enrichment1` through `enrichment10` (each with `_Apikey`).

#### Agent Settings (EpsimoAI Agent IDs for Copyright)
| Operation | Endpoint |
|-----------|----------|
| Get | `GET /api/settings/agent` |
| Create | `POST /api/settings/agent` |
| Update | `PUT /api/settings/agent` |

Available fields: `projectId`, `enrichment1AgentId` through `enrichment10AgentId`.

#### SDR AI Settings (EpsimoAI Agent IDs for SDR AI)
| Operation | Endpoint |
|-----------|----------|
| Get | `GET /api/settings/sdr-ai` |
| Create | `POST /api/settings/sdr-ai` |
| Update | `PUT /api/settings/sdr-ai` |

Available fields: `projectId`, plus `<fieldName>AgentId` for all SDR fields.

---

### 9. Lead Processing 🚀

Settings-driven execution routes that trigger enrichment, copyright, and SDR AI processing on individual leads.

| Processing Type | Endpoint | Settings Source |
|-----------------|----------|-----------------|
| Enrichment | `POST /api/leads/process/enrich` | URL Settings |
| Copyright AI | `POST /api/leads/process/copyright` | Agent Settings |
| SDR AI | `POST /api/leads/process/sdr` | SDR AI Settings |

#### Enrichment Processing
```json
{
  "leadId": "enrich-lead-id",
  "services": ["companyUrl", "enrichment1", "enrichment3"],
  "overwrite": false
}
```

#### Copyright Processing
```json
{
  "leadId": "enrich-lead-id",
  "processes": [1, 3, 5],
  "overwrite": false
}
```

#### SDR AI Processing
```json
{
  "leadId": "enrich-lead-id",
  "fields": ["message1", "aiLeadScore", "aiQualification"],
  "overwrite": false
}
```

#### Response Format (all three)
```json
{
  "success": true,
  "runIds": ["run-abc-123", "run-def-456"],
  "batchTag": "enrich-process-1707654321-x8k2m1",
  "triggered": ["companyUrl", "enrichment1"],
  "skipped": ["enrichment3"],
  "leadId": "enrich-lead-id"
}
```

#### Processing Workflow
1. **Configure** (one-time per company): `POST /api/settings/url`, `POST /api/settings/agent`, `POST /api/settings/sdr-ai`
2. **Trigger** (per lead): `POST /api/leads/process/enrich`, `.../copyright`, `.../sdr`
3. **Track**: Use `runIds` → `GET /api/trigger-task-status?runId=...`

---

### 10. Background Tasks (Trigger.dev)

| Operation | Endpoint |
|-----------|----------|
| Submit Task | `POST /api/trigger` |
| Check Status | `GET /api/trigger-task-status?runId=...` |
| List Recent Runs | `GET /api/trigger-recent-runs?limit=20` |

---

### 11. Email Services

| Operation | Endpoint |
|-----------|----------|
| Validate Email | `POST /api/email-validate` |
| Verify Email (deep) | `POST /api/email-verify` |

---

### 12. Integration APIs

| Operation | Endpoint |
|-----------|----------|
| Start Apify Scrape | `POST /api/start-lead-scrape-complete` |
| Check Scrape Status | `GET /api/lead-generation-status?runId=...` |
| Epsimo AI Chat | `POST /api/epsimo-chat` |
| Unipile Accounts | `GET /api/unipile-accounts` |

---

## Data Architecture

### Multi-Tenant Isolation
All data is strictly isolated. Three isolation layers are enforced:
1. **Owner-based** — Data filtered by authenticated user's `owner` ID (JWT `sub`)
2. **Company-based** — Data filtered by user's `company_id` (resolved from CompanyMember table)
3. **Client-based** — Data filtered by `client_id` (the **slug**, not the UUID)

### Key ID Fields

| Field | Example | Used For |
|-------|---------|----------|
| Client `id` | `edd5c738-a1b2-...` (UUID) | Update/delete the **client record itself** |
| Client `client_id` | `acme-corp` (slug) | ⭐ **All lead operations** — creating, listing, and querying leads |
| Lead `id` | `lead-a3f2b1c8-...` (UUID) | Update/delete individual **lead records** |
| `owner` | `4428a4f8-...` (UUID) | Set automatically from JWT `sub` claim |

> 🚨 **Never confuse Client `id` with Client `client_id`.** Using the wrong one when creating leads causes the "Invisible Leads" bug — leads exist in the database but don't appear in the UI. See the [Slug vs UUID warning](#1-client-management-) above.

### Data Operations Auth Mode
After `getAuthContext` resolves the owner, all data queries use `generateClient<Schema>({ authMode: 'apiKey' })` — meaning the Amplify API key handles DynamoDB access while the JWT provides identity and isolation.

---

## Error Handling

All errors follow a consistent format:
```json
{
  "success": false,
  "error": "Error message",
  "errorType": "authentication_error",
  "details": "Additional error details",
  "recommendation": "Suggested action"
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes | Recommended Action |
|------|---------|---------------|-------------------|
| 200 | Success | Request completed successfully | Continue processing |
| 201 | Created | Resource created successfully | Capture returned ID |
| 400 | Bad Request | Invalid payload, missing required fields | Validate request body |
| 401 | Unauthorized | Invalid/expired token, missing auth | Refresh or re-authenticate |
| 403 | Forbidden | Insufficient permissions, wrong company_id | Check user permissions |
| 404 | Not Found | Resource doesn't exist | Verify ID/slug is correct |
| 409 | Conflict | Duplicate resource, constraint violation | Check for existing records |
| 429 | Too Many Requests | Rate limit exceeded | Implement exponential backoff |
| 500 | Server Error | Backend issue, database timeout | Retry with exponential backoff |
| 503 | Service Unavailable | Temporary downtime | Wait and retry |

### Common Error Types
- **Authentication** — `no_valid_credentials`, `token_expired`, `federated_jwt`, `no_valid_tokens`
- **Authorization** — `insufficient_permissions`, `owner_mismatch`
- **Validation** — `missing_required_field`, `invalid_format`, `invalid_value`
- **Resource** — `not_found`, `already_exists`, `conflict`

---

## Rate Limits & Pagination

### Rate Limits
| Tier | Limit |
|------|-------|
| Standard | 100 requests/minute |
| Premium | 1,000 requests/minute |

### Handling Rate Limits

When you hit rate limits (429 status), implement exponential backoff:

```python
import time
import requests
from requests.exceptions import HTTPError

def make_request_with_retry(url, headers, method="GET", json_data=None, max_retries=5):
    """Make API request with automatic retry on rate limits and server errors."""
    for attempt in range(max_retries):
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=json_data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=json_data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, json=json_data)

            response.raise_for_status()
            return response.json()

        except HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited - exponential backoff
                wait_time = min(60 * (2 ** attempt), 300)  # Max 5 minutes
                print(f"Rate limited. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            elif e.response.status_code >= 500:
                # Server error - retry with backoff
                wait_time = min(10 * (2 ** attempt), 60)  # Max 1 minute
                print(f"Server error. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            elif e.response.status_code == 401:
                # Token expired - try to refresh
                print("Token expired. Attempting refresh...")
                # Implement token refresh here
                raise
            else:
                # Other errors - don't retry
                raise

        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    raise Exception(f"Max retries ({max_retries}) exceeded")

# Usage example
headers = {"Authorization": f"Bearer {access_token}"}
result = make_request_with_retry(
    "https://last.leadgenius.app/api/clients",
    headers=headers
)
```

### Pagination
- **Standard API**: Cursor-based (`limit` + `nextToken`)
- **Bulk API**: Token-based (`limit` default 1000, max 5000 + `nextToken`)

---

## Helper Scripts

| Script | Description |
|--------|-------------|
| [`scripts/test_api.py`](scripts/test_api.py) | **E2E test suite** — tests auth, client CRUD, lead CRUD with cleanup |
| [`scripts/lgp.py`](scripts/lgp.py) | Unified CLI for all common operations |
| [`scripts/import_csv.py`](scripts/import_csv.py) | **CSV import tool** — batch import leads from CSV with rate limiting |
| [`scripts/api_call.py`](scripts/api_call.py) | Low-level utility for custom raw API requests |
| [`scripts/auth.py`](scripts/auth.py) | Standalone auth utility |

### Running the E2E Test Suite
```bash
python3 scripts/test_api.py \
  --username your@email.com \
  --password YourPassword \
  --base-url https://last.leadgenius.app
```

Options:
- `--base-url` — Override base URL (default: `https://last.leadgenius.app`)
- `--skip-cleanup` — Keep test data after run

The test creates a temporary client and leads, exercises all CRUD operations, and cleans up automatically.

---

## CLI Usage (`lgp.py`)

```bash
# Auth
python3 scripts/lgp.py auth --email your@email.com

# Leads
python3 scripts/lgp.py leads list
python3 scripts/lgp.py leads find --full-name "Hugo Sanchez"
python3 scripts/lgp.py leads enrich --ids lead_1 lead_2

# Campaigns
python3 scripts/lgp.py campaigns list
python3 scripts/lgp.py campaigns create --name "Q3 Expansion"

# Pipeline analytics
python3 scripts/lgp.py pipeline --start 2026-01-01 --end 2026-02-08

# Maintenance
python3 scripts/lgp.py maintenance bugs list
python3 scripts/lgp.py maintenance bugs report --desc "Enrichment fails on LinkedIn URLs"
python3 scripts/lgp.py maintenance enhancements list
python3 scripts/lgp.py maintenance enhancements request --desc "Add support for Google Maps leads"

# API Key generation
python3 scripts/lgp.py generate-key --name "Production Agent" --desc "Key for main auto-agent"

# Admin (admin only)
python3 scripts/lgp.py admin companies
python3 scripts/lgp.py admin users
```

---

## Quick Start

```bash
# 1. Authenticate and get JWT
python3 scripts/auth.py --email your@email.com

# 2. Run the full E2E test suite
python3 scripts/test_api.py --username your@email.com --password YourPassword

# 3. Or make individual API calls
python3 scripts/api_call.py GET /clients
python3 scripts/api_call.py GET /leads?client_id=acme-corp
python3 scripts/api_call.py POST /leads --data '{"client_id": "acme-corp", "firstName": "Test", "lastName": "User"}'
```

---

## High-Fidelity Import Workflow

This is the recommended end-to-end procedure for creating a client workspace and importing leads in a single, robust run. Following these steps prevents data orphaning and ensures full visibility in the UI.

### Step 1: Authenticate (Dual Level)
```bash
# JWT for administrative tasks (client creation, GraphQL)
python3 scripts/lgp.py auth --email your@email.com

# API Key for high-speed batch imports (generate if needed)
python3 scripts/lgp.py generate-key --name "Import-Key"
```
Verify `~/.leadgenius_auth.json` contains both a `token` and an API key.

### Step 2: Create the Client
Use the REST API or GraphQL mutation. **Capture the returned `client_id` (slug)** from the response — this is what you'll use for all lead operations.

```bash
python3 scripts/api_call.py POST /clients \
  --data '{"clientName": "Historic Leads", "description": "Legacy imported leads"}'
```

### Step 3: Import Leads
Use the **slug** (`client_id`) from Step 2 in every lead object.

> ⚠️ **Use single-lead POST for reliability.** Batch POST (`{"leads": [...]}`) may return 201 but not persist leads. See [HUBSPOT_TO_LEADGENIUS.md](HUBSPOT_TO_LEADGENIUS.md) Bug #2.

```python
# Recommended: Single-lead POST (100% reliable)
for lead in all_leads:
    payload = {"client_id": "historic-leads", "firstName": "...", ...}
    response = requests.post(f"{BASE_URL}/api/leads", json=payload, headers=headers)
    time.sleep(0.15)  # ~400 leads/min, safe rate
```

### Step 4: Verify
```bash
# Confirm leads are visible via the same slug the UI uses
python3 scripts/api_call.py GET "/leads?client_id=historic-leads&limit=1"
```

### Automated CSV Import (Recommended)

Use the provided CSV import script for automated batch import with best practices:

```bash
# Authenticate first
python3 scripts/auth.py --email your@email.com

# Import from CSV (auto-creates client)
python3 scripts/import_csv.py \
  --csv leads.csv \
  --client-name "My Client" \
  --company-url "https://example.com"

# Dry run to test
python3 scripts/import_csv.py \
  --csv leads.csv \
  --client-name "My Client" \
  --dry-run
```

**CSV Format:**
```csv
firstName,lastName,email,companyName,companyDomain,title,linkedinUrl,notes
John,Doe,john@acme.com,Acme Corp,acme.com,VP Sales,https://linkedin.com/in/johndoe,Demo lead
```

The script handles:
- ✅ Client creation and slug capture
- ✅ Batch processing (50 leads per request)
- ✅ Rate limit handling with exponential backoff
- ✅ Progress tracking and error reporting
- ✅ Import verification

### Import Checklist
- [ ] **Auth**: `~/.leadgenius_auth.json` has both token and API key
- [ ] **Client created**: Slug (`client_id`) captured from response
- [ ] **ID mapping correct**: Lead `client_id` uses the slug, NOT the UUID
- [ ] **Notes populated**: AI fields aggregated into `notes` for UI visibility
- [ ] **Batch size**: 50 leads per request for stability
- [ ] **Verification**: `GET /api/leads?client_id=<slug>&limit=1` returns results

---

## HubSpot → LeadGenius Import

For importing contacts from HubSpot CRM into LeadGenius, a comprehensive battle-tested guide is available. This covers all the nuances discovered during production imports.

> **Full Guide:** [HUBSPOT_TO_LEADGENIUS.md](HUBSPOT_TO_LEADGENIUS.md)

### Quick Reference: HubSpot Field Mapping

| HubSpot Source | LeadGenius Field | Notes |
|---|---|---|
| `contact.properties.firstname` | `firstName` | Direct mapping |
| `contact.properties.lastname` | `lastName` | Fallback to email-derived if empty |
| `contact.properties.email` | `email` | Required — skip contacts without |
| Associated Company `.name` | `companyName` | Via `&associations=companies`, NOT `contact.company` |
| Associated Company `.domain` | `companyUrl` | Via company associations |
| `contact.properties.jobtitle` | `title` | Omit if empty |
| `contact.properties.phone` / `.mobilephone` | `phoneNumber` | ⚠️ NOT `phone` — wrong name causes 500 |
| `lifecyclestage`, `hs_lead_status`, `industry` | `notes` | Append to notes for UI visibility |

### Critical HubSpot Import Rules

1. **Use Single-Lead POST** — Batch `{"leads": [...]}` returns 201 but does NOT persist. Always POST one lead at a time.
2. **Never Send Empty Strings** — Omit any optional field that has an empty string value. Empty strings cause 500 errors.
3. **Phone Field Name** — Use `phoneNumber`, NOT `phone`. Wrong name causes 500 Internal Server Error.
4. **LastName Fallback** — Use `"-"` (dash) for missing lastNames. A single dot (`"."`) causes 500 errors.
5. **Company from Associations** — HubSpot's `contact.properties.company` is almost always empty. Fetch via `&associations=companies` and batch-read company details.
6. **JWT Refresh** — Tokens expire after 1 hour. Refresh every ~200 leads during import.
7. **Use client_id Slug** — Same as the core import rule: always use the `client_id` (slug), never the `id` (UUID).

### Known Bugs (HubSpot-Specific)

| # | Bug | Symptom | Fix |
|---|-----|---------|-----|
| 1 | Invisible Leads | 201 but not in UI | Use `client_id` slug, not `id` UUID |
| 2 | Batch POST Non-Persistence | 201 + count but leads gone | POST leads individually |
| 3 | `phone` Field Name | 500 error | Use `phoneNumber` |
| 4 | Empty String Fields | 500 error | Omit empty fields entirely |
| 5 | HubSpot Company Field Empty | No companyName imported | Use associations API |
| 6 | Dot-Only LastName | 500 error | Use `"-"` as fallback |
| 7 | Unreliable Total Count | API returns page size as total | Paginate with `lastKey` or trust import counter |

### Pre-Flight Checklist (HubSpot Import)

- [ ] LeadGenius auth — `~/.leadgenius_auth.json` exists with valid `token`
- [ ] HubSpot token — `.env` contains `HUBSPOT_ACCESS_TOKEN`
- [ ] Client created — `POST /api/clients` returned successfully
- [ ] CLIENT_ID captured — using `client_id` (slug), NOT `id` (UUID)
- [ ] Associations enabled — HubSpot query includes `&associations=companies`
- [ ] Company data — using associated company objects, not contact `company` field
- [ ] Field names correct — `phoneNumber` (not `phone`), `companyUrl`, `title`
- [ ] No empty strings — all empty optional fields are omitted, not `""`
- [ ] Names populated — fallback logic for missing `firstName`/`lastName`
- [ ] Single-lead POST — NOT using batch `{"leads": [...]}` endpoint
- [ ] Token refresh — logic to re-auth every 200 leads
- [ ] Test with 5 leads first — verify persistence before full import

---

## Reference Material

- **API Reference**: See [references/api_reference.md](references/api_reference.md) for detailed endpoint descriptions, payloads, and response schemas
- **Import Guidelines**: See [LEADGENIUS_IMPORT_GUIDELINES.md](LEADGENIUS_IMPORT_GUIDELINES.md) for detailed pitfalls and lessons learned
- **HubSpot Import Guide**: See [HUBSPOT_TO_LEADGENIUS.md](HUBSPOT_TO_LEADGENIUS.md) for the complete HubSpot → LeadGenius import workflow, field mapping, script templates, and known bugs
- **Auth Helper**: See `src/utils/apiAuthHelper.ts` for the 3-layer auth implementation
- **OpenAPI Spec**: See [references/openapi.json](references/openapi.json) for machine-readable schemas
