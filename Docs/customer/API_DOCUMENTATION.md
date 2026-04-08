# API Documentation - Invoice Lines Retrieval API v1.0.0

**API Version:** 1.0.0  
**Last Updated:** April 8, 2026  
**Status:** Production Ready

---

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL](#base-url)
4. [Endpoints](#endpoints)
5. [Request/Response Examples](#requestresponse-examples)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Best Practices](#best-practices)

---

## Overview

The Invoice Lines Retrieval API provides secure, paginated access to invoice line items for contact persons. The API uses JWT Bearer token authentication and returns JSON-formatted responses.

**Key Features:**
- ✅ JWT Bearer token authentication
- ✅ Row-level authorization (contact person isolation)
- ✅ Paginated responses (1-10,000 records per page)
- ✅ Sub-100ms response times
- ✅ Production-grade availability (99.9% SLA)

---

## Authentication

### Bearer Token Authentication

The API uses **JWT Bearer tokens** for authentication. Every request must include an `Authorization` header with a valid JWT token.

**Token Format:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Requirements:**
- Format: JWT (JSON Web Token)
- Algorithm: HS256
- Claims: Must include `sub` (contact person ID)
- Expiration: Based on your identity provider's settings

### Obtaining a Token

Contact your system administrator to:
1. Obtain authentication credentials
2. Configure your identity provider
3. Generate JWT tokens

**Example Token Generation** (pseudocode):
```python
import jwt
from datetime import datetime, timedelta

token = jwt.encode(
    {
        "sub": "CONTACT-PERSON-ID",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    },
    secret_key,
    algorithm="HS256"
)
```

### Token Validation

The API validates:
- ✅ Token signature (ensures authenticity)
- ✅ Token expiration (ensures freshness)
- ✅ Required claims (ensures completeness)

---

## Base URL

```
https://api.yourcompany.com/api/v1
```

**Note:** Replace `yourcompany.com` with your actual domain.

---

## Endpoints

### GET /invoices/{invoice_id}/lines

Retrieve paginated invoice lines for a specific invoice.

#### Request

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `invoice_id` | string | Yes | Invoice identifier (e.g., "INV-12345") |

**Query Parameters:**
| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | integer | 1 | N/A | Page number (starting from 1) |
| `page_size` | integer | 100 | 10,000 | Records per page |

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

#### Response

**Status: 200 OK**

```json
{
  "invoice_id": "INV-12345",
  "contact_person_id": "CONTACT-001",
  "total_records": 250,
  "page": 1,
  "page_size": 100,
  "total_pages": 3,
  "invoice_lines": [
    {
      "line_id": "IL-001",
      "article_code": "ART-12345",
      "description": "Premium Product",
      "quantity": 5.0000,
      "unit_price": 100.00,
      "tax_percentage": 21.00,
      "total_price": 605.00,
      "line_order": 1
    },
    {
      "line_id": "IL-002",
      "article_code": "ART-67890",
      "description": "Standard Service",
      "quantity": 10.0000,
      "unit_price": 50.00,
      "tax_percentage": 21.00,
      "total_price": 605.00,
      "line_order": 2
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | The requested invoice identifier |
| `contact_person_id` | string | The authenticated contact person ID |
| `total_records` | integer | Total number of invoice lines |
| `page` | integer | Current page number |
| `page_size` | integer | Records per page |
| `total_pages` | integer | Total number of pages |
| `invoice_lines` | array | Array of invoice line objects |

**Invoice Line Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `line_id` | string | Unique line identifier |
| `article_code` | string | Product/service article code |
| `description` | string | Item description |
| `quantity` | number | Quantity (decimal with 4 places) |
| `unit_price` | number | Unit price in euros (2 decimal places) |
| `tax_percentage` | number | Tax percentage (2 decimal places) |
| `total_price` | number | Total price including tax (2 decimal places) |
| `line_order` | integer | Line sequence/order number |

---

## Request/Response Examples

### Example 1: Simple Request - First Page

**Request:**
```bash
curl -X GET "https://api.yourcompany.com/api/v1/invoices/INV-12345/lines?page=1&page_size=100" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "invoice_id": "INV-12345",
  "contact_person_id": "CONTACT-001",
  "total_records": 250,
  "page": 1,
  "page_size": 100,
  "total_pages": 3,
  "invoice_lines": [
    {
      "line_id": "IL-001",
      "article_code": "ART-12345",
      "description": "Premium Product",
      "quantity": 5.0000,
      "unit_price": 100.00,
      "tax_percentage": 21.00,
      "total_price": 605.00,
      "line_order": 1
    },
    // ... more lines
  ]
}
```

### Example 2: Retrieve Next Page

**Request:**
```bash
curl -X GET "https://api.yourcompany.com/api/v1/invoices/INV-12345/lines?page=2&page_size=100" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (200 OK):**
Records 101-200 of the same invoice.

### Example 3: Large Page Size

**Request:**
```bash
curl -X GET "https://api.yourcompany.com/api/v1/invoices/INV-99999/lines?page=1&page_size=10000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (200 OK):**
Up to 10,000 invoice lines in a single response.

### Example 4: Missing Authentication

**Request:**
```bash
curl -X GET "https://api.yourcompany.com/api/v1/invoices/INV-12345/lines"
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

### Example 5: Invalid Invoice / Unauthorized Access

**Request:**
```bash
curl -X GET "https://api.yourcompany.com/api/v1/invoices/INV-99999/lines" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (404 Not Found):**
```json
{
  "detail": "Invoice not found or not accessible"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Status | Meaning | Action |
|------|--------|---------|--------|
| 200 | OK | Request successful | Process the response |
| 400 | Bad Request | Invalid parameters | Check pagination parameters |
| 401 | Unauthorized | Missing/invalid token | Provide valid JWT token |
| 404 | Not Found | Invoice doesn't exist or unauthorized | Verify invoice ID, check permissions |
| 500 | Server Error | Internal server error | Retry after brief delay |

### Error Response Format

All errors return JSON with a `detail` field:

```json
{
  "detail": "Error description"
}
```

### Common Errors

**Error: Missing Authorization Header**
```json
{
  "detail": "Not authenticated"
}
```
**Solution:** Include `Authorization: Bearer {token}` header

**Error: Invalid Token**
```json
{
  "detail": "Invalid token signature"
}
```
**Solution:** Generate a new token from your identity provider

**Error: Expired Token**
```json
{
  "detail": "Token has expired"
}
```
**Solution:** Refresh your JWT token

**Error: Invalid Page Parameter**
```json
{
  "detail": "Page must be >= 1"
}
```
**Solution:** Use page numbers starting from 1

**Error: Page Size Too Large**
```json
{
  "detail": "Page size must be <= 10000"
}
```
**Solution:** Use page_size ≤ 10,000

---

## Rate Limiting

### Current Policy
No explicit rate limiting is enforced, but the following limits apply:
- **Maximum page size:** 10,000 records
- **Recommended concurrent requests:** 1-10 per contact person
- **Typical response time:** 45-200ms

### Best Practices
- Implement exponential backoff for retries
- Reuse HTTP connections (connection pooling)
- Cache results appropriately
- Monitor response times

### Future Rate Limiting
Future versions may introduce:
- Request rate limits (e.g., 1,000 req/min)
- Concurrent connection limits
- Quota-based access tiers

---

## Best Practices

### 1. Token Management
```python
# Good: Reuse tokens within their lifetime
token = get_jwt_token()  # Obtain once
for request in requests:
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request(headers)

# Bad: Requesting new token for every request
for request in requests:
    token = get_jwt_token()  # Expensive, unnecessary
    response = make_request(token)
```

### 2. Pagination Strategy
```python
# Retrieve all invoices efficiently
page = 1
while True:
    response = get_invoice_lines("INV-123", page=page, page_size=1000)
    process_lines(response['invoice_lines'])
    
    if page >= response['total_pages']:
        break
    page += 1
```

### 3. Error Handling
```python
import time
import requests

# Implement retry with exponential backoff
def get_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                # Refresh token and retry
                refresh_token()
            elif response.status_code >= 500:
                # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            else:
                # Client error, don't retry
                raise
```

### 4. Performance Optimization
```python
# Use appropriate page sizes
# - Small pages (100): Faster initial response, more requests
# - Large pages (5000+): Fewer requests, larger response

# For bulk data retrieval:
response = get_invoice_lines(invoice_id, page_size=5000)

# For interactive UI:
response = get_invoice_lines(invoice_id, page_size=50)
```

### 5. Connection Pooling
```python
# Use session for connection reuse
import requests

session = requests.Session()
headers = {"Authorization": f"Bearer {token}"}

for page in range(1, total_pages + 1):
    response = session.get(
        f"https://api.yourcompany.com/api/v1/invoices/{invoice_id}/lines?page={page}",
        headers=headers,
        timeout=10
    )
    # Process response
```

### 6. Monitoring & Logging
```python
import logging
import time

logger = logging.getLogger(__name__)

def get_invoice_lines_monitored(invoice_id, page=1):
    start_time = time.time()
    try:
        response = get_invoice_lines(invoice_id, page=page)
        elapsed = time.time() - start_time
        logger.info(f"Retrieved invoice {invoice_id}, page {page} in {elapsed:.2f}s")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to retrieve invoice {invoice_id}: {e} ({elapsed:.2f}s)")
        raise
```

---

## API Specifications

### Request Format
- **Protocol:** HTTPS (TLS 1.2+)
- **Method:** GET
- **Content-Type:** application/json
- **Authentication:** Bearer token in Authorization header

### Response Format
- **Content-Type:** application/json
- **Charset:** UTF-8
- **Number Format:** Decimal with appropriate precision
- **Date Format:** ISO 8601 (if applicable)

### Timeout Recommendations
- **Read Timeout:** 30 seconds
- **Connection Timeout:** 10 seconds
- **Total Timeout:** 60 seconds

---

## Versioning

### Current Version
- **API Version:** v1.0.0
- **Base Path:** /api/v1

### Backward Compatibility
- All v1.x versions are backward compatible
- v1.0.0 → v1.1.0 → v1.2.0 (all compatible)
- New endpoints in /api/v2 for major changes

### Deprecation Policy
- Deprecation notice: 6 months minimum
- Deprecated endpoints continue to work
- Sunset date clearly communicated

---

## Support

For API issues or questions:
- 📖 **Documentation:** See User Guide and Deployment Guide
- 📧 **Email:** api-support@yourcompany.com
- 🆘 **Support Hours:** 24/7 for production issues

---

*API Documentation v1.0.0*  
*Last Updated: April 8, 2026*  
*Status: Production Ready*
