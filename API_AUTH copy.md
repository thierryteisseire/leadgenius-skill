# API Authentication

## Endpoint

```
POST /api/auth
```

| Environment | URL |
|-------------|-----|
| Production | `https://last.leadgenius.app/api/auth` |
| Local | `http://localhost:3000/api/auth` |

## Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "username": "user@example.com",
  "password": "yourpassword"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| username | string | yes | 3–128 characters |
| password | string | yes | 8–128 characters |

## Example

```bash
curl -X POST https://last.leadgenius.app/api/auth \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"yourpassword"}'
```

## Successful Response (200)

```json
{
  "success": true,
  "message": "Authentication successful",
  "tokens": {
    "accessToken": "eyJraWQ...",
    "idToken": "eyJraWQ...",
    "refreshToken": "eyJjdHk...",
    "expiresIn": 3600
  },
  "user": {
    "username": "user@example.com"
  },
  "timestamp": "2026-02-09T17:39:17.746Z"
}
```

### Token Usage

| Token | Purpose | Lifetime |
|-------|---------|----------|
| `accessToken` | Authorize API requests (`Authorization: Bearer <token>`) | 1 hour |
| `idToken` | Contains user identity claims (email, sub) | 1 hour |
| `refreshToken` | Obtain new access/id tokens without re-authenticating | 30 days |

## Error Responses

### 401 — Invalid Credentials
```json
{
  "success": false,
  "error": "Invalid credentials",
  "details": "The username or password is incorrect",
  "solution": "Please check your username and password and try again"
}
```

### 401 — User Not Confirmed
```json
{
  "success": false,
  "error": "User not confirmed",
  "details": "The user account has not been confirmed",
  "solution": "Please confirm your account before attempting to sign in"
}
```

### 404 — User Not Found
```json
{
  "success": false,
  "error": "User not found",
  "details": "No user exists with the provided username",
  "solution": "Please check your username or create a new account"
}
```

### 429 — Rate Limited
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "details": "Too many authentication attempts from this IP. Please wait 15 minutes before trying again.",
  "retryAfter": 900000
}
```

Rate limit: 5 attempts per IP per 15-minute window.

### 400 — Bad Request
Returned for missing fields, invalid JSON, wrong content type, or invalid input length.

### 500 — Configuration / Server Error
Returned if the backend cannot load Cognito configuration or an unexpected error occurs.

## Using the Access Token

Include the `accessToken` in subsequent API requests:

```bash
curl -X GET https://last.leadgenius.app/api/some-endpoint \
  -H "Authorization: Bearer eyJraWQ..."
```

## Notes

- Authentication uses AWS Cognito `USER_PASSWORD_AUTH` flow
- MFA challenges are detected but not currently supported through this endpoint
- Tokens should be stored securely and never exposed in client-side code or URLs
- The `refreshToken` can be used with Cognito's token refresh flow to get new tokens without re-entering credentials
