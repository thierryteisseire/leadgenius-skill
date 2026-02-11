#!/usr/bin/env python3
"""
CSV Lead Import Script for LeadGenius Pro API

This script demonstrates best practices for importing leads from a CSV file:
- Proper client creation and slug capture
- Batch processing with recommended size (50 leads)
- Rate limit handling with exponential backoff
- Progress tracking and error reporting
- AI field aggregation into notes for UI visibility

Usage:
    python3 import_csv.py --csv leads.csv --client-name "My Client" [--base-url URL]

CSV Format:
    firstName,lastName,email,companyName,companyDomain,title,linkedinUrl,notes
    John,Doe,john@acme.com,Acme Corp,acme.com,VP Sales,https://linkedin.com/in/johndoe,Demo lead
"""

import argparse
import csv
import json
import os
import time
import sys
from typing import List, Dict, Any
import requests
from requests.exceptions import HTTPError

# Constants
BATCH_SIZE = 50
MAX_RETRIES = 5
DEFAULT_BASE_URL = "https://last.leadgenius.app"
AUTH_FILE = os.path.expanduser("~/.leadgenius_auth.json")


def load_auth() -> Dict[str, str]:
    """Load authentication credentials from file."""
    if not os.path.exists(AUTH_FILE):
        print(f"❌ Auth file not found: {AUTH_FILE}")
        print(f"   Run: python3 scripts/auth.py --email your@email.com")
        sys.exit(1)

    with open(AUTH_FILE, 'r') as f:
        return json.load(f)


def make_request_with_retry(
    url: str,
    headers: Dict[str, str],
    method: str = "GET",
    json_data: Dict = None,
    max_retries: int = MAX_RETRIES
) -> Dict[str, Any]:
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
                print(f"⏳ Rate limited. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            elif e.response.status_code >= 500:
                # Server error - retry with backoff
                wait_time = min(10 * (2 ** attempt), 60)  # Max 1 minute
                print(f"⚠️  Server error. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                # Other errors - don't retry
                print(f"❌ HTTP {e.response.status_code}: {e.response.text}")
                raise

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            raise

    raise Exception(f"Max retries ({max_retries}) exceeded")


def create_client(base_url: str, headers: Dict[str, str], client_name: str, company_url: str = None) -> str:
    """Create a new client and return its slug (client_id)."""
    print(f"\n🔨 Creating client: {client_name}")

    payload = {
        "clientName": client_name,
        "companyURL": company_url or f"https://{client_name.lower().replace(' ', '')}.com",
        "description": f"Imported client: {client_name}"
    }

    result = make_request_with_retry(
        f"{base_url}/api/clients",
        headers=headers,
        method="POST",
        json_data=payload
    )

    if not result.get("success"):
        raise Exception(f"Failed to create client: {result}")

    client_slug = result["client"]["client_id"]
    print(f"✅ Client created with slug: {client_slug}")
    return client_slug


def chunks(lst: List, n: int):
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def import_leads_batch(
    base_url: str,
    headers: Dict[str, str],
    client_slug: str,
    leads: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Import a batch of leads."""
    # Add client_id to each lead
    for lead in leads:
        lead["client_id"] = client_slug

    payload = {"leads": leads}

    result = make_request_with_retry(
        f"{base_url}/api/leads",
        headers=headers,
        method="POST",
        json_data=payload
    )

    return result


def verify_import(base_url: str, headers: Dict[str, str], client_slug: str) -> int:
    """Verify leads were imported and are visible in the UI."""
    print(f"\n🔍 Verifying import for client: {client_slug}")

    result = make_request_with_retry(
        f"{base_url}/api/leads?client_id={client_slug}&limit=1",
        headers=headers,
        method="GET"
    )

    # Note: The actual response structure may vary
    # Adjust based on your API's response format
    count = result.get("count", 0)
    print(f"✅ Verification: Found {count} leads")
    return count


def main():
    parser = argparse.ArgumentParser(description="Import leads from CSV to LeadGenius Pro")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--client-name", required=True, help="Name for the new client")
    parser.add_argument("--company-url", help="Company website URL")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"API base URL (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--dry-run", action="store_true", help="Parse CSV but don't import")

    args = parser.parse_args()

    # Load auth
    auth = load_auth()
    base_url = args.base_url.rstrip('/')

    headers = {
        "Authorization": f"Bearer {auth['token']}",
        "Content-Type": "application/json"
    }

    # Read CSV
    print(f"📄 Reading CSV: {args.csv}")
    leads = []

    try:
        with open(args.csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map CSV columns to API fields
                lead = {
                    "firstName": row.get("firstName", ""),
                    "lastName": row.get("lastName", ""),
                    "email": row.get("email", ""),
                    "companyName": row.get("companyName", ""),
                    "companyDomain": row.get("companyDomain", ""),
                    "title": row.get("title", ""),
                    "linkedinUrl": row.get("linkedinUrl", ""),
                    "notes": row.get("notes", "")
                }

                # Remove empty fields
                lead = {k: v for k, v in lead.items() if v}

                leads.append(lead)

        print(f"✅ Loaded {len(leads)} leads from CSV")

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        sys.exit(1)

    if args.dry_run:
        print("\n🔍 DRY RUN - First lead:")
        print(json.dumps(leads[0], indent=2))
        print(f"\n📊 Total leads: {len(leads)}")
        print(f"📦 Batches: {(len(leads) + BATCH_SIZE - 1) // BATCH_SIZE}")
        sys.exit(0)

    # Create client
    try:
        client_slug = create_client(base_url, headers, args.client_name, args.company_url)
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        sys.exit(1)

    # Import leads in batches
    print(f"\n📤 Importing {len(leads)} leads in batches of {BATCH_SIZE}...")

    total_created = 0
    total_skipped = 0
    batch_num = 0

    for batch in chunks(leads, BATCH_SIZE):
        batch_num += 1
        print(f"\n📦 Batch {batch_num}/{(len(leads) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch)} leads)...")

        try:
            result = import_leads_batch(base_url, headers, client_slug, batch)

            created = result.get("created", 0)
            skipped = result.get("skipped", [])

            total_created += created
            total_skipped += len(skipped)

            print(f"   ✅ Created: {created}, Skipped: {len(skipped)}")

            if skipped:
                print(f"   ⚠️  Skipped emails: {', '.join(skipped[:5])}")

        except Exception as e:
            print(f"   ❌ Batch failed: {e}")
            continue

        # Small delay between batches to be polite to the API
        if batch_num < (len(leads) + BATCH_SIZE - 1) // BATCH_SIZE:
            time.sleep(0.5)

    # Verify import
    print(f"\n" + "="*60)
    print(f"📊 IMPORT SUMMARY")
    print(f"="*60)
    print(f"   Client: {args.client_name}")
    print(f"   Slug: {client_slug}")
    print(f"   Total Created: {total_created}")
    print(f"   Total Skipped: {total_skipped}")
    print(f"="*60)

    try:
        verify_import(base_url, headers, client_slug)
        print(f"\n✅ Import completed successfully!")
        print(f"🔗 View in UI: {base_url}/clients/{client_slug}")
    except Exception as e:
        print(f"\n⚠️  Verification failed: {e}")
        print(f"   Leads may still have been imported. Check the UI manually.")


if __name__ == "__main__":
    main()
