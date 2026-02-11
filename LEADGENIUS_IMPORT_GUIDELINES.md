# LeadGenius High-Fidelity Import Guidelines

This document outlines the professional workflow for creating a client workspace and importing leads in a single, robust run. Following these steps prevents data "orphaning" and ensures maximum visibility in the LeadGenius UI.

## 1. The "Single Run" Workflow

To properly link leads to a workspace, you must follow this sequence:

### Step A: Authenticate (Dual Level)
- **JWT (Login)**: Required for administrative tasks (like GraphQL client creation).
- **API Key**: Required for high-speed batch lead imports.
```bash
# 1. Login to get JWT
lgp auth --email your@email.com

# 2. Generate API key if you don't have one
lgp generate-key --name "Import-Key"
```

### Step B: Create the Client (GraphQL)
Always use the GraphQL mutation to create a client. This allows you to specify a **human-readable slug** (`client_id`) which is vital for later operations.

**Crucial Note**: Capture the returned `id` (the UUID) from the response.

### Step C: Batch Import (REST)
When importing leads, use the **UUID** returned in Step B as the `client_id` for your lead objects.
- **Why?** The UI uses the UUID for internal linkage, while the API often accepts the slug. Using the UUID is 100% safe.

---

## 2. Technical Pitfalls & "Skill" Issues

During the EPSIMO AI import, we identified several critical "gotchas" in the LeadGenius API integration:

### ❌ The "Invisible Leads" Bug (Slug vs UUID)
- **Problem**: The client record has TWO identifiers: `id` (a UUID like `e2c3d00d-...`) and `client_id` (a slug like `historic-leads`). The **UI queries leads using the slug**, not the UUID. If you import leads with `client_id` set to the UUID, they exist in the database but the UI cannot find them.
- **Root Cause**: Using the UUID (`e2c3d00d-...`) as the lead's `client_id` field instead of the slug (`historic-leads`).
- **Solution**: **ALWAYS use the slug** (the `client_id` field from the client record) when creating leads. Never use the `id` (UUID) field.
- **Example**: If your client has `id: "e2c3d00d-..."` and `client_id: "historic-leads"`, set lead `client_id` to `"historic-leads"`.
- **Verification**: Query `GET /api/leads?client_id=<slug>&limit=1` — if it returns leads, the UI will show them too.

### ❌ Field Persistence (Structured vs. Notes)
- **Problem**: Structured fields like `aiLeadScore` or `aiQualification` may be saved in the backend but hidden in the standard UI table view.
- **Solution**: **Notes catch-all.** Aggregate all critical analytical data (AI scores, justifications, SDR notes) into the `notes` field using Markdown headers. This ensures data is immediately visible and searchable.

### ❌ Purge Timeouts
- **Problem**: The `purge=true` flag on client deletion often times out if the dataset exceeds 1,000 leads.
- **Solution**: Use a concurrent deletion script (`super_fast_delete.py`) that fetches lead IDs and deletes them in separate threads.

---

## 3. Recommended Import Script Template (V3)

Your import script should include this specific logic for AI fields:

```python
# Aggregate AI fields into Notes for visibility
lead["notes"] = f"""
## 🎯 AI SCORE: {row['aiLeadScore']} ({row['leadScore']}/100)

### 🧐 JUSTIFICATION
{row['Justification Jason']}

### 💡 STRATEGIC RECOMMENDATIONS
{row['Recommandations']}

### 📝 SDR SYNTHESIS
{row['Synthèse SDR']}
""".strip()
```

## 4. Summary Checklist for 1-Run Success
1. [ ] **Auth**: Run `lgp auth` and verify `~/.leadgenius_auth.json` has both a token and an API key.
2. [ ] **Client**: Use `create_historic_client.py` (GraphQL) to establish the workspace.
3. [ ] **ID Mapping**: Ensure the script uses the returned Registry ID for the leads.
4. [ ] **Notes**: Concatenate analytical fields into the `notes` property.
5. [ ] **Batch**: Use a batch size of 50 for optimal API stability.
