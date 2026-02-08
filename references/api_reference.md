# LeadGenius Pro Agent API Reference

This document provides a detailed breakdown of all available endpoints in the LeadGenius Pro Agent API.

## Base URL
`https://last.leadgenius.app/api/agent`

## Authentication
All requests require an API key passed in headers:
- `X-API-Key: lgp_...`
- OR `Authorization: Bearer lgp_...`

---

## 📊 Campaigns
Manage ABM campaigns and track performance.

### `GET /campaigns`
List all campaigns.
- **Query Params**: `page`, `pageSize`, `status`, `campaignType`.

### `POST /campaigns`
Create a new campaign.
- **Body**: `{ name, description, campaignType, startDate, endDate, goals: { targetAccounts, targetEngagement, targetPipeline } }`

### `GET /campaigns/{id}`
Retrieve campaign details.

### `GET /campaigns/{id}/metrics`
Get real-time performance metrics (ROI, conversion rates, etc.).

---

## 👤 Leads
Lifecycle management for marketing and sales leads.

### `GET /leads`
List leads with advanced filtering.
- **Filters**: `status`, `campaignId`, `email`, `companyName`.

### `POST /leads`
Create a single lead.

### `POST /leads/batch`
Create up to 100 leads in a single request.
- **Body**: `{ leads: [...] }`

### `PUT /leads/{id}/status`
Transition a lead status (e.g., `new` -> `qualified`).

---

## ✨ Enrichment
Trigger AI-powered data augmentation.

### `POST /enrichment/trigger`
Queue enrichment for specific lead IDs.
- **Body**: `{ leadIds: [], enrichmentType, priority }`

### `GET /enrichment/status/{jobId}`
Check the progress of an enrichment job.

### `GET /enrichment/services`
List all available third-party and AI enrichment services.

---

## 🏢 Target Accounts (ABM)
### `GET /target-accounts`
List high-value target accounts.

### `PUT /target-accounts/{id}/score`
Update account intent, engagement, and fit scores.

---

## 📈 Analytics
### `GET /analytics/pipeline`
Overall funnel performance metrics.

### `GET /analytics/trends`
Historical conversion trends.

### `POST /analytics/reports`
Request a custom data export.

---

## ⚙️ Workflows & Integrations
### `GET /workflows`
List automated sequences and workflows.

### `GET /integrations`
Manage connections to CRMs (Salesforce, HubSpot) and Mail Platforms.

### `GET /webhooks`
Configure event-based real-time notifications.

---

## 🛠️ Maintenance & System Health
Endpoints for reporting issues and providing feedback.

### `GET /maintenance/bugs`
List reported bugs.

### `POST /maintenance/bugs`
Report a discovered issue.
- **Body**: `{ description, userEmail }`

### `GET /maintenance/enhancements`
List requested enhancements.

### `POST /maintenance/enhancements`
Request a new feature.
- **Body**: `{ description, userEmail }`

---

## 👑 Global Administration (Admin Only)
High-level system management. Requires Master Admin status.
Root Path: `/api/admin`

### `GET /companies`
List all organizations currently using the platform.

### `GET /users`
Get the global directory of all platform users and their roles.

---

## 🔑 Authentication & API Keys
### `POST /epsimo-auth`
Exchange email/password for a JWT token.
- **Root Path**: `/api/epsimo-auth`
- **Body**: `{ email, password }`

### `POST /agent-api-keys`
Generate a new persistent API Key.
- **Auth**: Requires JWT (Bearer)
- **Body**: `{ name, description }`

### `GET /agent-api-keys`
List active API keys for the current user.
