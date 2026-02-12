# HubSpot → LeadGenius Import Guide

> Definitive, battle-tested guide for importing HubSpot CRM contacts into LeadGenius.  
> Last validated: February 2026 against `https://last.leadgenius.app/api`.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Step-by-Step Workflow](#2-step-by-step-workflow)
3. [HubSpot Data Extraction](#3-hubspot-data-extraction)
4. [Field Mapping (HubSpot → LeadGenius)](#4-field-mapping-hubspot--leadgenius)
5. [Lead Payload Rules (Critical)](#5-lead-payload-rules-critical)
6. [Import Script Template](#6-import-script-template)
7. [Known Bugs & Pitfalls](#7-known-bugs--pitfalls)
8. [Verification & Troubleshooting](#8-verification--troubleshooting)
9. [Pre-Flight Checklist](#9-pre-flight-checklist)

---

## 1. Prerequisites

### HubSpot
- A **Private App Access Token** (stored in `.env` as `HUBSPOT_ACCESS_TOKEN`)
- Scopes required: `crm.objects.contacts.read`, `crm.objects.companies.read`

### LeadGenius
- A valid account on `https://last.leadgenius.app`
- Credentials saved in `~/.leadgenius_auth.json` (run `python3 scripts/auth.py --save`)
- The auth file must contain: `token`, `email`, `base_url`, `user_id`

### Tools
- Python 3.9+ with `requests` library

---

## 2. Step-by-Step Workflow

```
┌─────────────────────────────────────────────────────┐
│  1. Authenticate to LeadGenius (get fresh JWT)      │
│  2. Create a Client (target workspace)              │
│  3. Note the client_id (UUID slug) from response    │
│  4. Extract contacts + companies from HubSpot       │
│  5. Build lead payloads following field rules        │
│  6. Import leads ONE AT A TIME via POST /api/leads  │
│  7. Verify in the LeadGenius UI                     │
└─────────────────────────────────────────────────────┘
```

### Step 1 — Authenticate

```python
import requests, json, os

resp = requests.post("https://last.leadgenius.app/api/auth", json={
    "username": "your@email.com",
    "password": "your-password"
}, headers={"Content-Type": "application/json"})

token = resp.json()["tokens"]["accessToken"]
# Save it
auth = {"token": token, "email": "your@email.com", "base_url": "https://last.leadgenius.app"}
with open(os.path.expanduser("~/.leadgenius_auth.json"), "w") as f:
    json.dump(auth, f, indent=2)
```

> ⏱ JWT tokens expire after **1 hour**. Refresh every 200 leads during import.

### Step 2 — Create a Client

```python
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
resp = requests.post("https://last.leadgenius.app/api/clients", headers=headers, json={
    "clientName": "My Import Batch",
    "description": "Contacts imported from HubSpot on Feb 2026"
})
client = resp.json()["client"]
CLIENT_ID = client["client_id"]  # ← THIS is what you use for leads
```

> ⚠️ The API returns **two** identifiers:
> - `id` — internal DynamoDB UUID (for client update/delete only)
> - `client_id` — the slug used for **all lead operations**
>
> **Always use `client_id`** — see [Bug #1: Invisible Leads](#bug-1-invisible-leads).

---

## 3. HubSpot Data Extraction

### Why Associations Matter

HubSpot stores company data in **associated Company objects**, NOT in the contact's `company` text field. The contact `company` property is almost always `null` or empty.

```python
# ❌ WRONG — this field is usually empty:
contact["properties"]["company"]  # → None

# ✅ CORRECT — fetch via associations:
GET /crm/v3/objects/contacts?properties=...&associations=companies
# Then batch-fetch company details from the associated IDs
```

### Full Extraction Pattern

```python
HUBSPOT_TOKEN = "your-token"
hs_headers = {"Authorization": f"Bearer {HUBSPOT_TOKEN}"}

# Step A: Fetch ALL contacts with company associations
contacts = []
after = None
props = "firstname,lastname,email,jobtitle,phone,mobilephone,city,country,lifecyclestage,hs_lead_status"

while True:
    url = f"https://api.hubapi.com/crm/v3/objects/contacts?limit=100&properties={props}&associations=companies"
    if after:
        url += f"&after={after}"
    data = requests.get(url, headers=hs_headers).json()
    contacts.extend(data["results"])
    after = data.get("paging", {}).get("next", {}).get("after")
    if not after:
        break

# Step B: Collect unique company IDs
company_ids = set()
for c in contacts:
    for a in c.get("associations", {}).get("companies", {}).get("results", []):
        company_ids.add(a["id"])

# Step C: Batch-fetch company details (100 at a time)
companies = {}
company_list = list(company_ids)
for i in range(0, len(company_list), 100):
    batch = company_list[i:i+100]
    resp = requests.post(
        "https://api.hubapi.com/crm/v3/objects/companies/batch/read",
        headers={**hs_headers, "Content-Type": "application/json"},
        json={
            "properties": ["name", "domain", "industry", "phone", "city", "country"],
            "inputs": [{"id": cid} for cid in batch]
        }
    )
    for r in resp.json().get("results", []):
        companies[r["id"]] = r["properties"]
```

---

## 4. Field Mapping (HubSpot → LeadGenius)

| HubSpot Source | LeadGenius Field | How to Get It |
|---|---|---|
| `contact.properties.firstname` | `firstName` | Direct |
| `contact.properties.lastname` | `lastName` | Direct |
| `contact.properties.email` | `email` | Direct (required) |
| Associated Company `.name` | `companyName` | Via company associations |
| Associated Company `.domain` | `companyUrl` | Via company associations |
| `contact.properties.jobtitle` | `title` | Direct |
| `contact.properties.phone` or `.mobilephone` | `phoneNumber` | Direct (**NOT** `phone`) |
| `contact.properties.lifecyclestage` | In `notes` | Append to notes |
| `contact.properties.hs_lead_status` | In `notes` | Append to notes |
| Associated Company `.industry` | In `notes` | Append to notes |

> ⚠️ **The LeadGenius field for phone is `phoneNumber`, not `phone`.**  
> Sending `phone` causes a **500 Internal Server Error** — see [Bug #3](#bug-3-phone-field-name).

---

## 5. Lead Payload Rules (Critical)

These rules were discovered through extensive testing. Violating any of them causes **silent failures** or **500 errors**.

### Rule 1: Never Send Empty Strings

```python
# ❌ CAUSES 500 ERROR:
{"firstName": "John", "lastName": "Smith", "email": "j@x.com", "title": "", "companyName": ""}

# ✅ CORRECT — omit empty fields entirely:
{"firstName": "John", "lastName": "Smith", "email": "j@x.com"}
```

**Implementation:**
```python
lead = {}
lead["client_id"] = CLIENT_ID
lead["firstName"] = first_name
lead["lastName"] = last_name
lead["email"] = email

# Only add optional fields if they have real values
if company_name:
    lead["companyName"] = company_name
if job_title:
    lead["title"] = job_title
if phone:
    lead["phoneNumber"] = phone  # NOT "phone"!
if notes:
    lead["notes"] = notes
```

### Rule 2: Use Single-Lead POST (Not Batch)

```python
# ❌ BATCH — returns 201 but DOES NOT PERSIST:
requests.post(BASE + "/leads", json={"leads": [lead1, lead2, lead3]})

# ✅ SINGLE — persists reliably:
requests.post(BASE + "/leads", json=lead)
```

> The batch endpoint (`{"leads": [...]}`) returns `201 Created` and even a `created` count, but the leads **are not saved to the database**. This is a confirmed server-side bug. Always POST leads **one at a time**.

### Rule 3: firstName and lastName Must Be Non-Empty

The API requires both `firstName` and `lastName` to be non-empty. If HubSpot data is missing names:

```python
import re

fn = (contact.get("firstname") or "").strip()
ln = (contact.get("lastname") or "").strip()

if not fn or not ln:
    local = email.split("@")[0]
    parts = re.split(r"[._-]", local)
    if not fn:
        fn = parts[0].capitalize()
    if not ln:
        ln = parts[-1].capitalize() if len(parts) >= 2 else "-"
```

> Use `-` (dash) as a fallback for `lastName`, **never `.` (dot)** — a single dot causes 500 errors.

### Rule 4: Use the client_id Slug

```python
# The value returned by POST /api/clients → response.client.client_id
# This is a UUID-like slug, e.g. "d1b40348-a748-4449-99e1-3c326ae61c03"
# NOT the "id" field (which is the internal DynamoDB key)
```

---

## 6. Import Script Template

```python
"""
HubSpot → LeadGenius Import Script Template
"""
import requests, json, os, time, re

# ─── Configuration ───
CLIENT_ID = "your-client-id-slug"  # From POST /api/clients → client.client_id
LG_BASE = "https://last.leadgenius.app/api"
LG_EMAIL = "your@email.com"
LG_PASSWORD = "your-password"

# ─── Authentication ───
def lg_refresh():
    resp = requests.post(f"{LG_BASE}/auth", json={
        "username": LG_EMAIL, "password": LG_PASSWORD
    }, headers={"Content-Type": "application/json"}, timeout=15)
    return resp.json()["tokens"]["accessToken"]

# ─── Build Lead from HubSpot Contact ───
def build_lead(contact, companies_map):
    p = contact.get("properties", {})
    email = p.get("email")
    if not email:
        return None

    # Company from associations (NOT from contact.properties.company)
    company_name = ""
    company_domain = ""
    assocs = contact.get("associations", {}).get("companies", {}).get("results", [])
    if assocs:
        comp = companies_map.get(assocs[0]["id"], {})
        company_name = comp.get("name", "") or ""
        company_domain = comp.get("domain", "") or ""

    # Fallback: derive from email domain
    if not company_name:
        domain = email.split("@")[1] if "@" in email else ""
        generic = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}
        if domain and domain not in generic:
            company_name = domain.split(".")[0].capitalize()

    # Names
    fn = (p.get("firstname") or "").strip()
    ln = (p.get("lastname") or "").strip()
    if not fn:
        parts = re.split(r"[._-]", email.split("@")[0])
        fn = parts[0].capitalize()
    if not ln:
        parts = re.split(r"[._-]", email.split("@")[0])
        ln = parts[-1].capitalize() if len(parts) >= 2 else "-"

    # Build payload — OMIT empty fields
    lead = {
        "client_id": CLIENT_ID,
        "firstName": fn,
        "lastName": ln,
        "email": email,
    }
    if company_name:
        lead["companyName"] = company_name
    title = (p.get("jobtitle") or "").strip()
    if title:
        lead["title"] = title
    phone = (p.get("phone") or p.get("mobilephone") or "").strip()
    if phone:
        lead["phoneNumber"] = phone   # ← NOT "phone"
    if company_domain:
        lead["companyUrl"] = company_domain

    # Notes
    notes_parts = ["Historic Contact imported from HubSpot"]
    if p.get("lifecyclestage"):
        notes_parts.append(f"Lifecycle: {p['lifecyclestage']}")
    if p.get("hs_lead_status"):
        notes_parts.append(f"Status: {p['hs_lead_status']}")
    lead["notes"] = "\n".join(notes_parts)

    return lead

# ─── Import Loop ───
def import_leads(leads):
    token = lg_refresh()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    created = 0
    failed = 0
    start = time.time()

    for i, lead in enumerate(leads):
        # Refresh JWT every 200 leads (~1 hour safety margin)
        if i > 0 and i % 200 == 0:
            token = lg_refresh()
            headers["Authorization"] = f"Bearer {token}"
            elapsed = time.time() - start
            rate = i / elapsed * 60
            print(f"  [{i}/{len(leads)}] created={created} failed={failed} rate={rate:.0f}/min")

        try:
            resp = requests.post(f"{LG_BASE}/leads", headers=headers, json=lead, timeout=15)
            if resp.status_code == 201:
                created += 1
                if created % 50 == 0:
                    print(f"  ✅ Created {created}...")
            elif resp.status_code == 401:
                # Token expired mid-batch
                token = lg_refresh()
                headers["Authorization"] = f"Bearer {token}"
                resp = requests.post(f"{LG_BASE}/leads", headers=headers, json=lead, timeout=15)
                if resp.status_code == 201:
                    created += 1
                else:
                    failed += 1
            else:
                failed += 1
                if failed <= 10:
                    print(f"  ❌ {lead['email']}: {resp.status_code} {resp.text[:80]}")
        except Exception as e:
            failed += 1

        time.sleep(0.15)  # ~400 leads/min, safe rate

    print(f"\n{'='*50}")
    print(f"DONE in {(time.time()-start)/60:.1f} min | Created: {created} | Failed: {failed}")
    print(f"{'='*50}")
```

### Expected Performance

| Contacts | Estimated Time | Notes |
|----------|---------------|-------|
| 100 | ~1.5 min | No token refresh needed |
| 500 | ~8 min | 2 token refreshes |
| 1,000 | ~16 min | 5 token refreshes |
| 5,000 | ~80 min | Consider splitting into multiple clients |

---

## 7. Known Bugs & Pitfalls

### Bug #1: Invisible Leads

| | |
|---|---|
| **Symptom** | Leads return 201 but don't appear in the LeadGenius UI |
| **Cause** | Using the client's internal `id` (UUID) instead of `client_id` (slug) for lead operations |
| **Fix** | Always use `client_id` from the create-client response |
| **Verify** | `GET /api/leads?client_id=<slug>&limit=1` — if this returns data, the UI will too |

### Bug #2: Batch POST Does Not Persist

| | |
|---|---|
| **Symptom** | `POST /api/leads` with `{"leads": [...]}` returns `201 Created` with a correct `created` count, but leads don't appear in subsequent GET queries |
| **Cause** | Server-side bug in the batch insertion path |
| **Fix** | **Always POST leads individually** (single object, not wrapped in a `leads` array) |
| **Impact** | ~3x slower than batch, but 100% reliable |

### Bug #3: `phone` Field Name Causes 500

| | |
|---|---|
| **Symptom** | `500 Internal Server Error: "Failed to create lead - no data returned"` |
| **Cause** | Sending phone number as `"phone"` instead of `"phoneNumber"` |
| **Fix** | Use `"phoneNumber"` as the JSON field name |

### Bug #4: Empty String Fields Cause 500

| | |
|---|---|
| **Symptom** | `500 Internal Server Error: "Failed to create lead - no data returned"` |
| **Cause** | Sending optional fields with empty string values like `"title": ""` or `"companyName": ""` |
| **Fix** | **Omit** any field that has an empty string — do not include it in the payload at all |

### Bug #5: HubSpot Company Field Is Empty

| | |
|---|---|
| **Symptom** | All imported leads have no `companyName` despite HubSpot showing company data |
| **Cause** | HubSpot stores company info in **associated Company objects**, not in the contact's `company` text property (which is almost always `null`) |
| **Fix** | Fetch contacts with `&associations=companies`, then batch-read company details from `/crm/v3/objects/companies/batch/read` |

### Bug #6: Dot-Only LastName Causes 500

| | |
|---|---|
| **Symptom** | `500 Internal Server Error` when `lastName` is `"."` |
| **Cause** | Server validation rejects single-character punctuation as lastNames |
| **Fix** | Use `"-"` (dash) as fallback for missing lastNames |

### Bug #7: LeadGenius Total Count Is Unreliable

| | |
|---|---|
| **Symptom** | `GET /api/leads?limit=100` returns `total: 100` even when there are 1,000+ leads |
| **Cause** | The API returns the page size as `total`, not the true count |
| **Workaround** | Paginate using `lastKey` or trust your import script's `created` counter instead |

---

## 8. Verification & Troubleshooting

### Post-Import Checks

```python
# 1. Spot-check a specific lead
resp = requests.get(f"{BASE}/leads?client_id={CLIENT_ID}&limit=10", headers=headers)
for lead in resp.json()["leads"]:
    print(f"{lead['firstName']} {lead['lastName']} | {lead['email']} | {lead.get('companyName', 'N/A')}")

# 2. The UI should show leads at:
# https://last.leadgenius.app → Select "Historic Contacts" client → Leads tab
```

### If Leads Are Invisible in the UI
1. Check you're using `client_id` (slug), not `id` (UUID)
2. Try `GET /api/leads?client_id=<YOUR_SLUG>&limit=1` — if empty, wrong slug
3. Check the client exists: `GET /api/clients`
4. Recreate the client and re-import

### If Import Returns 500 Errors
1. Check for **empty string fields** → remove them
2. Check the **phone** field → rename to `phoneNumber`
3. Check **lastName** → must not be `"."`, use `"-"` instead
4. Test with a minimal payload first:
   ```json
   {"client_id": "...", "firstName": "Test", "lastName": "One", "email": "test@example.com"}
   ```

---

## 9. Pre-Flight Checklist

Before running any import, verify each item:

- [ ] **LeadGenius auth** — `~/.leadgenius_auth.json` exists with valid `token`
- [ ] **HubSpot token** — `.env` contains `HUBSPOT_ACCESS_TOKEN`
- [ ] **Client created** — `POST /api/clients` returned successfully
- [ ] **CLIENT_ID captured** — using `client_id` (slug), NOT `id` (UUID)
- [ ] **Associations enabled** — HubSpot query includes `&associations=companies`
- [ ] **Company data** — using associated company objects, not contact `company` field
- [ ] **Field names correct** — `phoneNumber` (not `phone`), `companyUrl`, `title`
- [ ] **No empty strings** — all empty optional fields are omitted, not `""`
- [ ] **Names populated** — fallback logic for missing `firstName`/`lastName`
- [ ] **Single-lead POST** — NOT using batch `{"leads": [...]}` endpoint
- [ ] **Token refresh** — logic to re-auth every 200 leads
- [ ] **Test with 5 leads first** — verify persistence before full import
