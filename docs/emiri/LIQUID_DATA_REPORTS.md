# Liquid Data (LD) Reports - API Documentation

## Overview

Liquid Data (LD) is a set of APIs for accessing Circana's data warehouse directly. Unlike the Emiri copilot endpoints which provide AI-generated analysis, LD APIs provide raw data export capabilities through the Unify platform.

**Primary Use Case**: Creating, running, saving, and extracting data reports from Circana's retail analytics platform.

---

## Authentication

### LD Services Authentication

All LD API calls require **LTPA cookie-based authentication** (not Basic Auth or Bearer tokens).

**Authentication Flow:**
1. Login via `j_security_check` form POST
2. Receive LTPA cookies (`LtpaToken2` and `JSESSIONID`)
3. Pass cookies in all subsequent LD API calls

### Get LTPA Cookies

```bash
# Step 1: Get session cookie
curl -c /tmp/unify_cookies.txt \
  "https://advantageqa2.iriworldwide.com/alerts-dev/login.jsp"

# Step 2: Login with credentials
curl -c /tmp/unify_cookies.txt -b /tmp/unify_cookies.txt \
  -X POST "https://advantageqa2.iriworldwide.com/alerts-dev/j_security_check" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "j_username={UNIFY_ID}&j_password={PASSWORD}"
```

**Required Cookies:**
- `LtpaToken2` - Authentication token
- `JSESSIONID` - Session identifier

---

## URLs

### Environment URLs (QA)

| URL | Purpose |
|-----|---------|
| `https://advantageqa2.iriworldwide.com/unify-dev/plus/landing/2/` | Unify UI Dashboard |
| `https://advantageqa2.iriworldwide.com/unify-dev/apps/ee_shell.html` | Report Editor (Emiri Everywhere Shell) |
| `https://advantageqa2.iriworldwide.com/ld_dev/` | Liquid Data API Base URL |

### Obtaining URLs from Auth Response

The `ldServiceURL` is returned in the authentication response's `unify_defaults`:

```json
{
  "unify_defaults": {
    "ldServiceURL": "https://advantageqa2.iriworldwide.com/ld_dev/",
    "model": {
      "POS": {
        "baseURL": "https://advantageqa2.iriworldwide.com/ld_dev/",
        "modelID": 1101.0,
        "modelName": "TSV_WB",
        "modelType": "POS",
        "unifyURL": "https://advantageqa2.iriworldwide.com/unify-dev/"
      },
      "PANEL": {
        "modelID": 1138.0,
        "modelName": "IRI_PNL",
        "modelType": "PANEL",
        "unifyURL": "https://advantageqa2.iriworldwide.com/unify-dev/"
      }
    },
    "tenant": "CL1"
  }
}
```

---

## Data Models

| Model | ID | Name | Type | Use Case |
|-------|-----|------|------|----------|
| POS (Scanner) | 1101.0 | TSV_WB | POS | Retail sales data |
| Panel | 1138.0 | IRI_PNL | PANEL | Consumer panel data |

---

## API Reference

### 1. Get Descendant at Level Members

Navigate the product hierarchy to get dimension members for filtering.

**Endpoint:**
```
POST {ldServiceURL}/dimensions/getDescendantAtLevelMembers
```

**Headers:**
```
Content-Type: application/json
Cookie: LtpaToken2={token};JSESSIONID={session}
```

**Request Body:**
```json
{
  "modelID": 1101.0,
  "dimension": "Product",
  "member": {
    "memberFullPath": "Total Store > Edible > Department > Beverages",
    "memberID": "12345"
  },
  "level": "SubCategory"
}
```

**Response:**
```json
{
  "code": 0,
  "members": [
    {
      "id": "67890",
      "name": "Carbonated Soft Drinks",
      "fullPath": "Total Store > Edible > Department > Beverages > Carbonated Soft Drinks",
      "selected": false
    },
    {
      "id": "67891",
      "name": "Juice",
      "fullPath": "Total Store > Edible > Department > Beverages > Juice",
      "selected": false
    }
  ]
}
```

**Key Fields:**
- `modelID` - From `unify_defaults.model.{type}.modelID`
- `dimension` - e.g., "Product", "Geography", "Time"
- `member` - Anchor member (starting point for hierarchy)
- `level` - Target level to retrieve (e.g., "SubCategory", "Brand")

**Member Lookup Precedence:**
1. `memberID` (most precise)
2. `memberFullPath`
3. `memberName` (least precise)

---

### 2. Export Report

Trigger a report export. Returns either an `exportId` (immediate) or `qid` (async).

**Endpoint:**
```
POST {ldServiceURL}/export/find
```

**Headers:**
```
Content-Type: application/json
Cookie: LtpaToken2={token};JSESSIONID={session}
```

**Request Body:**
```json
{
  "exportType": 7,
  "reportName": "Beverages Sales Report",
  "reportID": "abc123-def456",
  "dimension": "Product",
  "multipleSelection": true,
  "rules": [
    {
      "dimensionName": "Product",
      "members": [
        {
          "id": "11111",
          "name": "Pepsi",
          "fullPath": "Total Store > Edible > Department > Beverages > Carbonated Soft Drinks > PepsiCo Inc > Pepsi",
          "selected": true
        },
        {
          "id": "11112",
          "name": "Coca-Cola",
          "fullPath": "Total Store > Edible > Department > Beverages > Carbonated Soft Drinks > Coca-Cola Co > Coca-Cola",
          "selected": true
        }
      ]
    },
    {
      "dimensionName": "Time",
      "members": [
        {
          "id": "L4W",
          "name": "Latest 4 Weeks",
          "fullPath": "Latest 4 Weeks",
          "selected": true
        }
      ]
    },
    {
      "dimensionName": "Geography",
      "members": [
        {
          "id": "TOTUS",
          "name": "Total US - Multi Outlet+ with Conv",
          "fullPath": "Total US - Multi Outlet+ with Conv",
          "selected": true
        }
      ]
    }
  ]
}
```

**Export Types:**
| Type | Format |
|------|--------|
| 7 | CSV |
| 3 | Excel |
| 4 | PowerPoint |
| 5 | Data Legends |

**Response (Immediate):**
```json
{
  "exportId": "export-abc123"
}
```

**Response (Async):**
```json
{
  "qid": "queue-xyz789"
}
```

**Key Fields:**
- `exportType` - Export format (7 = CSV recommended)
- `reportName` / `reportID` - Report identifier
- `dimension` - Primary dimension for rows
- `multipleSelection` - `true` when providing multiple members
- `rules` - Array of dimension filters with members

---

### 3. Get Export Status

Check status of async export. Only needed if `export/find` returns a `qid`.

**Endpoint:**
```
GET {ldServiceURL}/export/status/{qid}
```

**Headers:**
```
Cookie: LtpaToken2={token};JSESSIONID={session}
```

**Response (Pending):**
```json
{
  "status": "processing"
}
```

**Response (Complete):**
```json
{
  "status": "complete",
  "exportId": "export-abc123"
}
```

**Polling Strategy:**
- Poll every 2-5 seconds
- Max 30 attempts (60-150 seconds)
- Stop when `status` is "complete" or "error"

---

### 4. Download Export

Download the actual report data.

**Endpoint:**
```
GET {ldServiceURL}/export/download/{exportId}
```

**Headers:**
```
Cookie: LtpaToken2={token};JSESSIONID={session}
```

**Response:**
CSV file content (text/plain)

**CSV Format:**
```
Row 1: Report name
Row 2-3: Page filter information (Geography, Time, etc.)
Row 4+: Data rows with headers

Report Name,Pepsi Sales Report
Geography: Total US - Multi Outlet+ with Conv
Time: Latest 4 Weeks

Product,Dollar Sales,Unit Sales,Volume Sales
Pepsi,123456789,45678901,78901234
Coca-Cola,234567890,56789012,89012345
```

**Parsing CSV:**
- Row 1: Report name (informational)
- Row 2-3: Page filter context (informational)
- Row 4+: Actual data (skip header row for processing)

---

## Complete Workflow

### Workflow 1: Export with Known Report

```python
# 1. Login and get cookies
cookies = get_ltpa_cookies()

# 2. Export report with member overrides
export_response = await export_report(
    ld_service_url="https://advantageqa2.iriworldwide.com/ld_dev/",
    report_id="abc123",
    dimension="Product",
    members=[{"id": "11111", "name": "Pepsi", "selected": True}],
    cookies=cookies
)

# 3. Get export ID (immediate or async)
if "exportId" in export_response:
    export_id = export_response["exportId"]
else:
    export_id = await poll_export_status(
        qid=export_response["qid"],
        cookies=cookies
    )

# 4. Download CSV
csv_data = await download_export(export_id, cookies)
```

### Workflow 2: Dynamic Report with Dimension Lookup

```python
# 1. Login and get cookies
cookies = get_ltpa_cookies()

# 2. Get descendants to find target members
members = await get_descendant_members(
    ld_service_url="https://advantageqa2.iriworldwide.com/ld_dev/",
    model_id=1101.0,
    dimension="Product",
    anchor_member={"fullPath": "Total Store > Edible > Department > Beverages"},
    level="SubCategory",
    cookies=cookies
)

# 3. Filter/select members based on user query
selected = [m for m in members if "soft drink" in m["name"].lower()]

# 4. Export with selected members
export_response = await export_report(
    report_id="abc123",
    dimension="Product",
    members=[{**m, "selected": True} for m in selected],
    cookies=cookies
)

# 5. Download data
export_id = await get_export_id(export_response, cookies)
csv_data = await download_export(export_id, cookies)
```

---

## Member Object Reference

### Member Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier |
| `name` | Yes | Display name |
| `fullPath` | Yes | Hierarchy path |
| `selected` | Yes | Must be `true` for export |

### Time Dimension Members

Special members for time periods (auto-updating):

| ID | Name | Description |
|----|------|-------------|
| L4W | Latest 4 Weeks | Rolling 4-week period |
| L12W | Latest 12 Weeks | Rolling 12-week period |
| L13W | Latest 13 Weeks | Rolling 13-week period |
| L52W | Latest 52 Weeks | Rolling 52-week period |

### Geography Dimension Members

| ID | Name |
|----|------|
| TOTUS | Total US - Multi Outlet+ with Conv |
| MULO | Multi Outlet |

---

## Copilot Integration

The LD services URL is used by the Emiri copilot endpoints (`runCopilotAsync`, `fetchCopilotData`):

```json
{
  "baseURL": "https://advantageqa2.iriworldwide.com/ld_dev/",
  "unifyURL": "https://advantageqa2.iriworldwide.com/unify-dev/plus/landing/2/"
}
```

**Copilot vs Direct LD APIs:**
- **Copilot**: AI-powered analysis, returns natural language answers
- **Direct LD**: Raw data export, returns CSV/tabular data

---

## Error Handling

### Common Errors

| HTTP Code | Error | Solution |
|-----------|-------|----------|
| 302 | Redirect (auth required) | Re-authenticate with j_security_check |
| 401 | Unauthorized | Check LTPA cookie validity |
| 404 | Endpoint not found | Verify ldServiceURL |
| 500 | Server error | Retry or contact support |

### Export Status Codes

| Code | Status | Action |
|------|--------|--------|
| 0 | Success | Continue |
| 1 | Processing | Poll again |
| 2 | Error | Check error message |

---

## Configuration

### Environment Variables (MCP Server)

```bash
EMIRI_UNIFY_ID=TFox01ZCS
EMIRI_ALERTS_LOGIN_URL=https://advantageqa2.iriworldwide.com/alerts-dev/login.jsp
EMIRI_ALERTS_AUTH_URL=https://advantageqa2.iriworldwide.com/alerts-dev/j_security_check
```

### Obtained from Auth Response

```python
# From unify_defaults
ld_service_url = auth_response["unify_defaults"]["ldServiceURL"]
model_id = auth_response["unify_defaults"]["model"]["POS"]["modelID"]
tenant = auth_response["unify_defaults"]["tenant"]
```

---

## Testing

### Quick Test with curl

```bash
# 1. Get cookies
curl -c /tmp/ld_cookies.txt \
  "https://advantageqa2.iriworldwide.com/alerts-dev/login.jsp"

curl -c /tmp/ld_cookies.txt -b /tmp/ld_cookies.txt \
  -X POST "https://advantageqa2.iriworldwide.com/alerts-dev/j_security_check" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "j_username=TFox01ZCS&j_password=YOUR_PASSWORD"

# 2. Get descendants
curl -b /tmp/ld_cookies.txt \
  -X POST "https://advantageqa2.iriworldwide.com/ld_dev/dimensions/getDescendantAtLevelMembers" \
  -H "Content-Type: application/json" \
  -d '{
    "modelID": 1101.0,
    "dimension": "Product",
    "member": {"memberFullPath": "Total Store"},
    "level": "Department"
  }'

# 3. Export report
curl -b /tmp/ld_cookies.txt \
  -X POST "https://advantageqa2.iriworldwide.com/ld_dev/export/find" \
  -H "Content-Type: application/json" \
  -d '{
    "exportType": 7,
    "reportName": "Test Report",
    "reportID": "YOUR_REPORT_ID",
    "dimension": "Product",
    "rules": []
  }'
```

---

## MCP Tools (Proposed)

| Tool | Purpose | Input |
|------|---------|-------|
| `ld_get_dimension_members` | Navigate hierarchy | modelID, dimension, member, level |
| `ld_export_report` | Trigger export | reportID, dimension, members |
| `ld_get_export_status` | Poll async export | qid |
| `ld_download_export` | Download CSV | exportId |

---

## References

- Meeting Notes: `docs/meetings/meeting_20260222_liquid_data.md`
- Meeting Notes: `docs/meetings/meeting_20260414_liquid_data.md`
- Meeting Notes: `docs/meetings/meeting_20260416_emiri_api.md`
- Emiri Payloads: `docs/emiri_payloads_and_response.md`
- Unify UI: `https://advantageqa2.iriworldwide.com/unify-dev/plus/landing/2/`
