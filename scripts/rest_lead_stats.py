#!/usr/bin/env python3
import json
import os
import requests
import sys
from collections import Counter

def main():
    api_key = os.environ.get("LEADGENIUS_API_KEY") or os.environ.get("LGP_API_KEY")
    if not api_key:
        print("Error: API Key is required (LEADGENIUS_API_KEY or LGP_API_KEY).")
        sys.exit(1)

    base_url = "https://last.leadgenius.app/api/agent/leads"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    all_leads = []
    page = 1
    
    print("Fetching leads from REST API...")
    
    while True:
        try:
            response = requests.get(base_url, headers=headers, params={"page": page, "pageSize": 100})
            if response.status_code != 200:
                print(f"Error fetching leads: {response.status_code}")
                break
                
            data = response.json()
            leads = data.get("data", [])
            all_leads.extend(leads)
            
            pagination = data.get("pagination", {})
            if page >= pagination.get("totalPages", 1):
                break
            page += 1
        except Exception as e:
            print(f"Error: {e}")
            break

    if not all_leads:
        print("No leads found.")
        return

    # Aggregate by client_id
    stats = Counter(lead.get("client_id", "Unassigned") for lead in all_leads)

    print("\n--- Lead Statistics per Client ID ---")
    print(f"{'Client ID':<30} | {'Leads':<10}")
    print("-" * 45)
    for client_id, count in stats.most_common():
        print(f"{str(client_id):<30} | {count:<10}")
    
    print(f"\nTotal Leads analyzed: {len(all_leads)}")

if __name__ == "__main__":
    main()
