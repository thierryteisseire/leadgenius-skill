# Auth Logic Update for API Key Support

## Overview
The current implementation of the LeadGenius skill scripts (`lgp.py` and `api_call.py`) treats all tokens as Bearer tokens. However, the LeadGenius backend requires specific headers for long-lived API Keys (`lgp_...`).

When using an API Key, the backend requires:
1. `x-api-key`: The API Key (starting with `lgp_`)
2. `x-user-id`: The UUID of the user owing the key (the `sub` claim from the original JWT)

Failure to provide `x-user-id` with an API Key results in a `401 Unauthorized` error.

## Required Changes

### 1. Update `scripts/lgp.py`

**Goal**: Update the `LeadGeniusCLI` class to load `user_id` alongside the token and switch header strategies dynamically.

#### A. Update `__init__` and `_load_token` -> `_load_auth`

Change the `__init__` method to store `user_id`:
```python
    def __init__(self, base_url=None):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip('/')
        # Changed: Load both token and user_id
        self.token, self.user_id = self._load_auth()
```

Rename and update `_load_token` to `_load_auth`:
```python
    def _load_auth(self):
        # 1. Prefer Environment Variable
        api_key = os.environ.get("LGP_API_KEY")
        user_id = os.environ.get("LGP_USER_ID")
        
        if api_key:
            # Try to load user_id from file if not in env
            if not user_id and os.path.exists(AUTH_FILE):
                 try:
                    with open(AUTH_FILE, "r") as f:
                        data = json.load(f)
                        user_id = data.get("user_id")
                 except:
                     pass
            return api_key, user_id
            
        # 2. Check Auth File
        if os.path.exists(AUTH_FILE):
            try:
                with open(AUTH_FILE, "r") as f:
                    data = json.load(f)
                    # Prefer API Key if stored
                    token = data.get("api_key") or data.get("token")
                    uid = data.get("user_id")
                    return token, uid
            except:
                pass
        return None, None
```

#### B. Update `_request` to use Conditional Headers

Modify `_request` to detect API keys and send the correct headers:

```python
    def _request(self, method, endpoint, data=None, params=None):
        if not self.token:
            print("Error: Not authenticated. Set LGP_API_KEY or run 'lgp auth'.")
            sys.exit(1)

        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        headers = { "Content-Type": "application/json" }
        
        # New Logic: Check for API Key format
        if self.token and self.token.startswith("lgp_"):
            if not self.user_id:
                print("Error: API Key requires user_id. Please re-authenticate or manually add 'user_id' to ~/.leadgenius_auth.json")
                sys.exit(1)
            headers["x-api-key"] = self.token
            headers["x-user-id"] = self.user_id
        else:
            # Fallback for JWT
            headers["Authorization"] = f"Bearer {self.token}"

        # ... rest of method ...
```

### 2. Update `scripts/api_call.py`

**Goal**: Apply similar logic to the standalone script.

#### A. Load `user_id`
```python
    # After loading args...
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
                    user_id = auth_data.get("user_id") # Load user_id
                    if api_key:
                        print(f"Using saved credentials for {auth_data.get('email', 'unknown user')}")
            except Exception as e:
                print(f"Warning: Failed to read saved credentials: {e}")
```

#### B. Conditional Headers
```python
    url = f"{args.base_url.rstrip('/')}/{args.endpoint.lstrip('/')}"
    headers = { "Content-Type": "application/json" }
    
    # Check if it looks like an API Key
    is_api_key = api_key.startswith("lgp_")
    
    if is_api_key:
        if not user_id:
             print("Error: API Key requires user_id. Please re-authenticate or manually add 'user_id' to ~/.leadgenius_auth.json")
             sys.exit(1)
        headers["x-api-key"] = api_key
        headers["x-user-id"] = user_id
    else:
        headers["Authorization"] = f"Bearer {api_key}"
```

## Testing
1. Authenticate normally to get a JWT.
2. Generate an API Key (or manually switch to one).
3. Ensure `~/.leadgenius_auth.json` contains `"user_id": "..."`.
4. Run `lgp.py leads list` — should succeed with `x-api-key` headers.
