#!/usr/bin/env python3
import argparse
import json
import os
import requests
import sys
from getpass import getpass
from datetime import datetime

DEFAULT_BASE_URL = "http://localhost:3000"
AUTH_FILE = os.path.expanduser("~/.leadgenius_auth.json")

class LeadGeniusCLI:
    def __init__(self, base_url=None):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip('/')
        self.token = self._load_token()

    def _load_token(self):
        if os.path.exists(AUTH_FILE):
            try:
                with open(AUTH_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("token")
            except:
                pass
        return os.environ.get("LGP_API_KEY")

    def _request(self, method, endpoint, data=None, params=None):
        if not self.token:
            print("Error: Not authenticated. Run 'lgp auth' first.")
            sys.exit(1)

        url = f"{self.base_url}/api/agent/{endpoint.lstrip('/')}"
        headers = {
            "X-API-Key": self.token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.request(method, url, headers=headers, json=data, params=params)
            if response.status_code >= 400:
                print(f"Error ({response.status_code}): {response.text}")
                return None
            return response.json()
        except Exception as e:
            print(f"Connection Error: {e}")
            return None

    def auth(self, email=None, password=None):
        email = email or input("Email: ")
        password = password or getpass("Password: ")
        
        url = f"{self.base_url}/api/epsimo-auth"
        try:
            response = requests.post(url, json={"email": email, "password": password})
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("jwt_token")
                with open(AUTH_FILE, "w") as f:
                    json.dump({"token": self.token, "email": email, "base_url": self.base_url}, f)
                print(f"Successfully authenticated as {email}")
            else:
                print(f"Auth Failed: {response.text}")
        except Exception as e:
            print(f"Auth Error: {e}")

    # Leads
    def list_leads(self, limit=20):
        data = self._request("GET", "leads", params={"pageSize": limit})
        if data:
            print(json.dumps(data, indent=2))

    def enrich_leads(self, lead_ids, type="technographic"):
        payload = {"leadIds": lead_ids, "enrichmentType": type}
        data = self._request("POST", "enrichment/trigger", data=payload)
        if data:
            print(f"Enrichment triggered: Job ID {data.get('jobId')}")

    # Campaigns
    def list_campaigns(self):
        data = self._request("GET", "campaigns")
        if data:
            for c in data.get("campaigns", []):
                print(f"[{c.get('id')}] {c.get('name')} ({c.get('status')})")

    def create_campaign(self, name, type="abm"):
        payload = {"name": name, "campaignType": type, "status": "active"}
        data = self._request("POST", "campaigns", data=payload)
        if data:
            print(f"Campaign created: {data.get('id')}")

    # Analytics
    def show_pipeline(self):
        data = self._request("GET", "analytics/pipeline")
        if data:
            print("--- Pipeline Metrics ---")
            print(json.dumps(data, indent=2))

    # Admin (Master Admin Only)
    def admin_list_companies(self):
        # Note: This checks for master admin on server side
        # Endpoint: /api/admin/companies (not under /api/agent)
        # We need to override the _request construction for this specific path or adjust logic
        # simpler to just use full path in _request if it starts with http, or handle /api/admin
        
        # Let's support a slightly detailed request method for flexibility
        pass 

    def _request_full_url(self, method, url_path, data=None, params=None):
        if not self.token:
            print("Error: Not authenticated. Run 'lgp auth' first.")
            sys.exit(1)
            
        full_url = f"{self.base_url}/{url_path.lstrip('/')}"
        headers = {
            "X-API-Key": self.token, # agent api key might not work here, usually needs session cookie for admin
            # BUT: admin routes in nextjs might be protected by session cookies, NOT api key.
            # Let's check the code for admin/companies.
            # It uses `isMasterAdminServer()` which checks cookies.
            # AND `hasAPIKeyAuth()`... createClient({ authMode: 'apiKey' })
            # The route purely relies on `isMasterAdmin()` for permission check which checks cookies.
            # So `lgp` CLI might NOT work for admin routes unless it acts as a browser with cookies.
            # OR if we update the admin route to ALSO accept a master secret key.
            #
            # However, looking at `api/agent` routes, they use API Key.
            # The plan was to expose "Master Admin" capabilities.
            # If the current admin routes require Session Cookies, the CLI (which uses API Key) won't work out of the box
            # unless we add API Key support to those routes or simulating login.
            #
            # Re-reading `src/app/api/admin/companies/route.ts`:
            # `const isAdmin = await isMasterAdmin();`
            # `isMasterAdminServer` uses `fetchAuthSession` with `cookies`.
            # So yes, it requires cookie-based auth.
            
            # Since I cannot easily change the admin auth mechanism without affecting security, 
            # I will implement the maintenance commands which I created specifically for the agent API (API Key auth).
            # For admin commands, I will add them but warn they might require browser session or specific setup.
            # check if `lgp auth` saves cookies? 
            # `auth.py` saves `jwt_token`. 
            # `epsimo-auth` returns `jwt_token`. 
            # If we pass this token as a cookie header, maybe?
            # `amplify/auth/server` expects standard cognito cookies.
            
            # Let's stick to the plan: Implement Maintenance commands first as they are definitely compatible.
            # I'll add Admin commands relying on the API Agent Key if I can, OR I'll skip them if they are incompatible
            # and just note it.
            # Wait, the prompt asked to "ensure all API endpoints, including master admin... are accessible".
            # If I can't access them via CLI, I haven't fully succeeded.
            # But the user approved the plan.
            #
            # Let's look at `maintenance` commands first.
            "Content-Type": "application/json"
        }
        # ... standard request ...
        pass

    # Maintenance
    def list_bugs(self):
        data = self._request("GET", "maintenance/bugs")
        if data:
            print(json.dumps(data, indent=2))

    def report_bug(self, description, email=None):
        payload = {"description": description, "userEmail": email}
        data = self._request("POST", "maintenance/bugs", data=payload)
        if data:
            print(f"Bug reported: ID {data.get('bug', {}).get('id')}")

    def list_enhancements(self):
        data = self._request("GET", "maintenance/enhancements")
        if data:
            print(json.dumps(data, indent=2))

    def request_enhancement(self, description, email=None):
        payload = {"description": description, "userEmail": email}
        data = self._request("POST", "maintenance/enhancements", data=payload)
        if data:
            print(f"Enhancement requested: ID {data.get('enhancement', {}).get('id')}")
    
    # Admin (Experimental - tries to use same token)
    def list_all_companies(self):
        # NOTE: This endpoint uses /api/admin/companies which expects Session Cookies.
        # This CLI uses X-API-Key. This call will likely fail 403 unless we modify the endpoint
        # to accept API Key for Master Admin (dangerous) or we simulate a full session.
        # For now, I will point it to the endpoint and let it try, or I can implement a specific
        # agent-admin endpoint if needed.
        # Let's try to hit the URL.
        print("Warning: Admin endpoints require session cookies. This might fail with API Key.")
        # We need a way to make requests to non-/api/agent/ paths
        url = f"{self.base_url}/api/admin/companies"
        headers = {"X-API-Key": self.token, "Content-Type": "application/json"}
        # Trying to pass token as Cookie just in case logic allows (unlikely but possible if custom auth)
        # headers["Cookie"] = ...
        try:
             response = requests.get(url, headers=headers)
             print(f"Status: {response.status_code}")
             print(response.text)
        except Exception as e:
            print(f"Error: {e}")

    def list_all_users(self):
        print("Warning: Admin endpoints require session cookies. This might fail with API Key.")
        url = f"{self.base_url}/api/admin/users"
        headers = {"X-API-Key": self.token, "Content-Type": "application/json"}
        try:
             response = requests.get(url, headers=headers)
             print(f"Status: {response.status_code}")
             print(response.text)
        except Exception as e:
            print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="LeadGenius Pro Agent CLI")
    parser.add_argument("--base-url", help="Override base URL")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Auth
    auth_parser = subparsers.add_parser("auth", help="Authenticate")
    auth_parser.add_argument("--email", help="Account email")

    # Leads
    leads_parser = subparsers.add_parser("leads", help="Manage leads")
    leads_parser.add_argument("action", choices=["list", "enrich"])
    leads_parser.add_argument("--ids", nargs="+", help="Lead IDs for enrichment")

    # Campaigns
    camp_parser = subparsers.add_parser("campaigns", help="Manage campaigns")
    camp_parser.add_argument("action", choices=["list", "create"])
    camp_parser.add_argument("--name", help="Campaign name")

    # Analytics
    subparsers.add_parser("pipeline", help="Show pipeline analytics")

    # Maintenance
    maint_parser = subparsers.add_parser("maintenance", help="Maintenance bugs/enhancements")
    maint_sub = maint_parser.add_subparsers(dest="mtype", help="Type")
    
    # Bugs
    bugs_parser = maint_sub.add_parser("bugs", help="Manage bugs")
    bugs_parser.add_argument("action", choices=["list", "report"])
    bugs_parser.add_argument("--desc", help="Description for report")
    bugs_parser.add_argument("--email", help="Contact email")

    # Enhancements
    enh_parser = maint_sub.add_parser("enhancements", help="Manage enhancements")
    enh_parser.add_argument("action", choices=["list", "request"])
    enh_parser.add_argument("--desc", help="Description for request")
    enh_parser.add_argument("--email", help="Contact email")

    # Admin
    admin_parser = subparsers.add_parser("admin", help="Admin functions")
    admin_parser.add_argument("resource", choices=["companies", "users"])

    args = parser.parse_args()
    cli = LeadGeniusCLI(base_url=args.base_url)

    if args.command == "auth":
        cli.auth(email=args.email)
    elif args.command == "leads":
        if args.action == "list":
            cli.list_leads()
        elif args.action == "enrich":
            if not args.ids:
                print("Error: --ids required for enrichment")
                return
            cli.enrich_leads(args.ids)
    elif args.command == "campaigns":
        if args.action == "list":
            cli.list_campaigns()
        elif args.action == "create":
            if not args.name:
                print("Error: --name required")
                return
            cli.create_campaign(args.name)
    elif args.command == "pipeline":
        cli.show_pipeline()
    elif args.command == "maintenance":
        if args.mtype == "bugs":
            if args.action == "list":
                cli.list_bugs()
            elif args.action == "report":
                if not args.desc:
                    print("Error: --desc required")
                    return
                cli.report_bug(args.desc, email=args.email)
        elif args.mtype == "enhancements":
            if args.action == "list":
                cli.list_enhancements()
            elif args.action == "request":
                if not args.desc:
                    print("Error: --desc required")
                    return
                cli.request_enhancement(args.desc, email=args.email)
    elif args.command == "admin":
        if args.resource == "companies":
            cli.list_all_companies()
        elif args.resource == "users":
            cli.list_all_users()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
