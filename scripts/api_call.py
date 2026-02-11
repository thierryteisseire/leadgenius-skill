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
    parser.add_argument("--base-url", default="https://last.leadgenius.app/api", help="Base URL")
    parser.add_argument("--key", help="API Key (defaults to LGP_API_KEY env var)")

    args = parser.parse_args()

    # Authentication resolution order: 
    # 1. --key argument
    # 2. LGP_API_KEY environment variable
    # 3. Saved credentials in ~/.leadgenius_auth.json
    api_key = args.key or os.environ.get("LGP_API_KEY")
    user_id = os.environ.get("LGP_USER_ID")
    
    if not api_key:
        auth_file = os.path.expanduser("~/.leadgenius_auth.json")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "r") as f:
                    auth_data = json.load(f)
                    # Prefer API Key if stored
                    api_key = auth_data.get("api_key") or auth_data.get("token")
                    
                    # Also load user_id if not in env
                    if not user_id:
                        user_id = auth_data.get("user_id")
                        
                    if api_key:
                        print(f"Using saved credentials for {auth_data.get('email', 'unknown user')}")
            except Exception as e:
                print(f"Warning: Failed to read saved credentials: {e}")

    if not api_key:
        print("Error: API Key is required. Run 'python3 scripts/auth.py' first, use --key, or set LGP_API_KEY.")
        sys.exit(1)

    url = f"{args.base_url.rstrip('/')}/{args.endpoint.lstrip('/')}"
    headers = { "Content-Type": "application/json" }
    
    # Check if it looks like an API Key (lgp_...)
    if api_key.startswith("lgp_"):
        if not user_id:
             print("Error: API Key requires user_id. Please re-authenticate or manually add 'user_id' to ~/.leadgenius_auth.json")
             sys.exit(1)
        headers["x-api-key"] = api_key
        headers["x-user-id"] = user_id
    else:
        # Fallback for JWT
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        data = None
        if args.data:
            data = json.loads(args.data)

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
