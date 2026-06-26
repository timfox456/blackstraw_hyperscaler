# IRI Advantage LD API Reference

> **LLM-Friendly Documentation** - Generated from implementation analysis and documentation research.
> Last updated: 2026-04-14

---

## Overview

**IRI Advantage LD** is a retail analytics API from [IRI Worldwide](https://www.iriworldwide.com), providing hierarchical dimension data for retail reporting and analysis.

- **Base URL**: `https://advantage.iriworldwide.com/client3-ld`
- **API Type**: REST/JSON
- **Auth Method**: Basic Authentication with session cookie reuse
- **Documentation**: `https://advantage.iriworldwide.com/unifyhelp/docs/apis/report/`

---

## Authentication

### Two Environment Variables

| Variable | Value | Example |
|----------|-------|--------|
| `ADVANTAGE_AUTHORIZATION` | Full Basic auth header | `Basic VkthbGxpWkNTOlZwcmtiNzg5IQ==` |
| `ADV_LD_BASIC_AUTH` | Base64 credentials only | `VkthbGxpWkNTOlZwcmtiNzg5IQ==` |

### Auth Resolution Logic (Python)

```python
def _authorization_header() -> str:
    full = os.environ.get("ADVANTAGE_AUTHORIZATION", "").strip()
    if full:
        return full if full.lower().startswith("basic ") else f"Basic {full}"
    
    b64 = os.environ.get("ADV_LD_BASIC_AUTH", "").strip()
    if b64:
        return f"Basic {b64}"
    
    # Exit with error if neither is set
    sys.exit(1)
```

### Session Cookie Requirement

The API uses **session cookies** in addition to the Authorization header. You must:

1. Call `/security/login` first with Basic auth
2. Extract session cookies from the login response
3. Reuse those cookies on all subsequent API calls

---

## Endpoints

### 1. Login

**POST** `/security/login`

Authenticates and establishes a session.

#### Request

```http
POST /security/login
Authorization: Basic <base64_credentials>
Content-Type: application/json (optional)
```

#### Response (Success - 200)

```json
{
  "retCode": {
    "code": 0
  }
}
```

#### Response (Failure)

```json
{
  "retCode": {
    "code": <non-zero>,
    "message": "..."
  }
}
```

---

### 2. Get Descendants at Level Members

**POST** `/dimension/getDescendantsAtLevelMembers`

Fetches hierarchical dimension members at a specified level.

#### Request

```http
POST /dimension/getDescendantsAtLevelMembers
Authorization: Basic <base64_credentials>
Accept: text/json
Content-Type: application/json
Cookie: <session cookies from login>
```

#### Request Body

```json
{
  "modelId": "2040",
  "dimension": {
    "name": "Product",
    "memberFullPath": "Product.TOTAL STORE : FOLDER.TOTAL STORE.EDIBLE.DEPT-BEVERAGES.AISLE-CARBONATED SOFT DRINKS.CARBONATED BEVERAGES",
    "levelName": "SubCategory",
    "memberId": ":Category:4527492:3506815:3506816:3506762:3506881"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `modelId` | string | The model/cube ID to query |
| `dimension.name` | string | Dimension name (e.g., "Product", "Geography", "Time") |
| `dimension.memberFullPath` | string | Full hierarchical path to the member |
| `dimension.levelName` | string | Target level to retrieve descendants at |
| `dimension.memberId` | string | Internal member identifier with colon prefix format |

#### Response

Returns JSON array of descendant members at the specified level.

#### Common Errors

| HTTP Code | Cause | Solution |
|-----------|-------|----------|
| `406 Not Acceptable` | Missing `Accept: text/json` header | Add header to request |
| `401 Unauthorized` | Invalid/expired credentials or session | Re-authenticate via `/security/login` |

---

## Complete Python Usage Example

```python
import os
import requests

BASE_URL = "https://advantage.iriworldwide.com/client3-ld"

def get_auth_header():
    full = os.environ.get("ADVANTAGE_AUTHORIZATION", "").strip()
    if full:
        return full if full.lower().startswith("basic ") else f"Basic {full}"
    b64 = os.environ.get("ADV_LD_BASIC_AUTH", "").strip()
    if b64:
        return f"Basic {b64}"
    raise ValueError("Set ADVANTAGE_AUTHORIZATION or ADV_LD_BASIC_AUTH")

def login(session, auth_header):
    url = f"{BASE_URL}/security/login"
    r = session.post(url, headers={"Authorization": auth_header}, timeout=120)
    r.raise_for_status()
    data = r.json()
    if data.get("retCode", {}).get("code") != 0:
        raise Exception(f"Login failed: {data}")
    return data

def get_descendants(session, auth_header, body):
    url = f"{BASE_URL}/dimension/getDescendantsAtLevelMembers"
    headers = {
        "Authorization": auth_header,
        "Accept": "text/json",
    }
    return session.post(url, headers=headers, json=body, timeout=120)

# Usage
session = requests.Session()
auth = get_auth_header()
login(session, auth)

body = {
    "modelId": "2040",
    "dimension": {
        "name": "Product",
        "memberFullPath": "Product.TOTAL STORE : FOLDER.TOTAL STORE.EDIBLE.DEPT-BEVERAGES.AISLE-CARBONATED SOFT DRINKS.CARBONATED BEVERAGES",
        "levelName": "SubCategory",
        "memberId": ":Category:4527492:3506815:3506816:3506762:3506881"
    }
}

response = get_descendants(session, auth, body)
print(response.json())
```

---

## Dimension Hierarchy Pattern

The API follows a hierarchical data model common in retail analytics:

```
Product
├── TOTAL STORE : FOLDER
│   └── TOTAL STORE
│       └── EDIBLE
│           └── DEPT-BEVERAGES
│               └── AISLE-CARBONATED SOFT DRINKS
│                   └── CARBONATED BEVERAGES  ← SubCategory level
```

### Path Format

- Levels separated by `.`
- Special marker `: FOLDER` for grouping nodes
- Member IDs use colon-prefixed format: `:Category:id1:id2:...`

### Common Dimensions

| Dimension | Description |
|-----------|-------------|
| `Product` | Product hierarchy (Category → Dept → Aisle → SubCategory) |
| `Geography` | Store/region hierarchy |
| `Time` | Time periods (Year → Quarter → Period) |

---

## Implementation Notes

### 1. Session Reuse is Critical

```python
# WRONG - Creates new session, loses cookies
def call_api(auth_header, body):
    session = requests.Session()  # New session each call!
    return session.post(url, ...)

# RIGHT - Reuse session with cookies
session = requests.Session()
login(session, auth)           # Login once
get_descendants(session, ...)  # Same session, cookies preserved
```

### 2. Accept Header Required

Without `Accept: text/json`, the server returns `406 Not Acceptable`.

### 3. Timeout Considerations

The API can be slow. The example uses `timeout=120` (120 seconds).

### 4. Error Handling

Check `retCode.code` - `0` means success, non-zero indicates failure.

---

## Integration with agentic-ai-negotiations

This API is **standalone** and not currently integrated into the main orchestrator.

To integrate, create a new MCP or data agent following the pattern in `test_python.py`:

1. Use `requests.Session` for cookie persistence
2. Implement two-step auth: login → API calls
3. Handle `406` by adding `Accept: text/json`
4. Parse `retCode.code` for success/failure

---

## See Also

- **Reference Implementation**: `test_python.py` in this repository
- **Official Docs**: `https://advantage.iriworldwide.com/unifyhelp/docs/apis/report/`
- **Core API Docs**: `https://help.buildwithadvantage.net/coreapi/html/`
