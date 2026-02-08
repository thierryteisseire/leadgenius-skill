#!/usr/bin/env python3
import argparse
import json
import os
import requests
import sys

def main():
    parser = argparse.ArgumentParser(description="Call LeadGenius Pro Agent API")
    parser.add_argument("method", choices=["GET", "POST", "PUT", "DELETE"], help="HTTP method")
    parser.add_argument("endpoint", help="API endpoint (e.g., /leads)")
    parser.add_argument("--data", help="JSON data for POST/PUT requests")
    parser.add_argument("--base-url", default="https://last.leadgenius.app/api/agent", help="Base URL")
    parser.add_argument("--key", help="API Key (defaults to LGP_API_KEY env var)")

    args = parser.parse_args()

    # Authentication resolution order: 
    # 1. --key argument
    # 2. LGP_API_KEY environment variable
    # 3. Saved credentials in ~/.leadgenius_auth.json
    api_key = args.key or os.environ.get("LGP_API_KEY")
    
    if not api_key:
        auth_file = os.path.expanduser("~/.leadgenius_auth.json")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "r") as f:
                    auth_data = json.load(f)
                    api_key = auth_data.get("token")
                    if api_key:
                        print(f"Using saved credentials for {auth_data.get('email', 'unknown user')}")
            except Exception as e:
                print(f"Warning: Failed to read saved credentials: {e}")

    if not api_key:
        print("Error: API Key is required. Run 'python3 scripts/auth.py' first, use --key, or set LGP_API_KEY.")
        sys.exit(1)

    # Detect base path
    root_base = args.base_url.rstrip('/').replace('/api/agent', '')
    
    if args.endpoint.startswith('/admin') or args.endpoint.startswith('admin/'):
         # Admin routes
         base_url = f"{root_base}/api/admin"
         clean_endpoint = args.endpoint.replace('/admin/', '').replace('admin/', '').lstrip('/')
    elif 'epsimo-auth' in args.endpoint or 'agent-api-keys' in args.endpoint:
         # Root API routes
         base_url = f"{root_base}/api"
         clean_endpoint = args.endpoint.lstrip('/')
    else:
         # Default Agent routes
         base_url = f"{root_base}/api/agent"
         clean_endpoint = args.endpoint.lstrip('/')

    url = f"{base_url}/{clean_endpoint}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    try:
        data = None
        if args.data:
            data = json.loads(args.data)

        print(f"Calling: {args.method} {url}")
        response = requests.request(args.method, url, headers=headers, json=data)
        
        print(f"Status: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
