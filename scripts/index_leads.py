#!/usr/bin/env python3
import os
import requests
import json
import sys

def main():
    api_key = os.environ.get("LGP_APPSYNC_KEY")
    company_id = os.environ.get("LGP_COMPANY_ID")
    url = "https://ugdmgjyxenhipk74b5swx4xvuy.appsync-api.us-east-1.amazonaws.com/graphql"

    if not api_key or not company_id:
        print("Error: LGP_APPSYNC_KEY and LGP_COMPANY_ID are required.")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    # 1. Fetch a batch of leads from the brevo-followers client that might be missing
    client_id = "client_1769080798982_z98bou" # brevo-followers
    
    query = """
    query ListLeadsByCompany($company_id: String!, $nextToken: String) {
        listEnrichLeadsByCompanyId(company_id: $company_id, nextToken: $nextToken, limit: 100) {
            items {
                id
                client_id
                fullName
            }
            nextToken
        }
    }
    """

    print(f"Fetching leads to re-index for company {company_id}...")
    
    payload = {
        "query": query,
        "variables": {
            "company_id": company_id
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    leads = response.json().get('data', {}).get('listEnrichLeadsByCompanyId', {}).get('items', [])

    if not leads:
        print("No leads found to index.")
        return

    # 2. Touch the leads via Mutation to force re-indexing
    mutation = """
    mutation UpdateEnrichLeads($input: UpdateEnrichLeadsInput!) {
        updateEnrichLeads(input: $input) {
            id
            updatedAt
        }
    }
    """

    print(f"Touching {len(leads)} leads to trigger REST indexing...")
    
    success_count = 0
    for lead in leads:
        # We "touch" it by sending its existing data back, which triggers the indexer
        input_data = {
            "id": lead['id'],
            "lead_id": lead['id'],
            "company_id": company_id,
            "client_id": lead.get('client_id') or client_id,
            "notes": "Triggered re-index via automation"
        }
        
        m_payload = {
            "query": mutation,
            "variables": {"input": input_data}
        }
        
        m_res = requests.post(url, headers=headers, json=m_payload)
        if m_res.status_code == 200 and "errors" not in m_res.json():
            success_count += 1
        else:
            print(f"Failed to touch lead {lead['id']}: {m_res.text}")

    print(f"Finished. Successfully touched {success_count} leads.")
    print("Wait a few minutes for the REST search engine to sync these changes.")

if __name__ == "__main__":
    main()
