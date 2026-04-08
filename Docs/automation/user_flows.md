# USER FLOWS & AUTOMATION SCENARIOS - PIVD-7043

**Document:** Automation Walkthrough  
**Date:** 2026-04-08  
**Story:** Retrieve invoice lines for a specific invoice of a contact person via Public API

---

## OVERVIEW

This document describes the complete user flows and automation scenarios for the Invoice Lines Retrieval API. Each flow maps to one or more functional requirements (REQ001-REQ008).

---

## USER FLOW 1: AUTHENTICATED USER RETRIEVES INVOICE LINES

**Actor:** Contact Person (authenticated with JWT token)  
**Goal:** Retrieve all line items from a specific invoice  
**Requirements:** REQ001, REQ002, REQ003, REQ006

### Flow Steps

1. **User authenticates**
   - User has JWT token (Bearer token issued by authentication system)
   - Token contains `sub` claim with `contact_person_id`
   - Example: `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJDUC01Njc4In0...`

2. **User requests invoice lines**
   - Endpoint: `GET /api/v1/invoices/{invoice_id}/lines`
   - Headers: `Authorization: Bearer <jwt_token>`
   - Example URL: `GET /api/v1/invoices/INV-2026-001234/lines`
   - Query params: `page=1&page_size=100`

3. **System authenticates request**
   - Extracts JWT from Authorization header
   - Validates JWT signature and expiration
   - Extracts `contact_person_id` from token
   - Raises HTTP 401 if token invalid/expired

4. **System authorizes access**
   - Queries database for invoice with given `invoice_id`
   - Checks that invoice belongs to authenticated `contact_person_id`
   - Returns 404 if invoice not found OR doesn't belong to user
   - (Privacy-safe: same response for both cases)

5. **System retrieves paginated lines**
   - Fetches invoice lines from database
   - Validates pagination parameters (page >= 1, page_size between 1-10000)
   - Applies ORDER BY line_order ASC
   - Calculates offset: (page - 1) * page_size
   - Retrieves `page_size` records from offset
   - Gets total count of all lines for pagination metadata

6. **System transforms and returns response**
   - Maps database InvoiceLine objects to InvoiceLineResponse schema
   - Includes all 8 required fields per line item
   - Calculates total_pages: ceil(total_records / page_size)
   - Returns HTTP 200 with InvoiceLinesResponse JSON

7. **User receives data**
   - Parses JSON response
   - Uses invoice_lines array for display/processing
   - Uses pagination metadata (page, page_size, total_records, total_pages) for UI

### Success Response Example

```json
{
  "invoice_id": "INV-2026-001234",
  "contact_person_id": "CP-5678",
  "total_records": 150,
  "page": 1,
  "page_size": 100,
  "total_pages": 2,
  "invoice_lines": [
    {
      "line_id": "IL-001",
      "article_code": "ART-12345",
      "description": "Product X",
      "quantity": "5.00",
      "unit_price": "100.00",
      "tax_percentage": "21.00",
      "total_price": "605.00",
      "line_order": 1
    },
    ...
  ]
}
```

---

## USER FLOW 2: USER ATTEMPTS TO ACCESS ANOTHER USER'S INVOICE

**Actor:** Contact Person (authenticated)  
**Goal:** Access invoice that doesn't belong to them  
**Requirements:** REQ003, REQ005

### Flow Steps

1. User authenticates (same as Flow 1)
2. User requests: `GET /api/v1/invoices/INV-SOMEONE-ELSE/lines`
3. System authenticates (same as Flow 1)
4. System checks authorization
   - Finds invoice in database
   - Checks `invoice.contact_person_id != request.contact_person_id`
   - Authorization fails
5. System returns HTTP 404 with message: "Invoice not found or not accessible"
   - Note: Same response as if invoice didn't exist (privacy protection)

### Response Example

```json
{
  "detail": "Invoice not found or not accessible"
}
```

---

## USER FLOW 3: UNAUTHENTICATED USER ATTEMPTS REQUEST

**Actor:** Anonymous user (no JWT token)  
**Goal:** Access invoice lines without authentication  
**Requirements:** REQ006

### Flow Steps

1. User makes request without Authorization header
   - Request: `GET /api/v1/invoices/INV-2026-001234/lines`
   - Headers: (none)
2. System checks for JWT dependency
3. JWT validation fails (no token provided)
4. System returns HTTP 401 with message: "Not authenticated"

### Response Example

```json
{
  "detail": "Not authenticated"
}
```

---

## USER FLOW 4: USER WITH INVALID TOKEN

**Actor:** Attacker or user with corrupted token  
**Goal:** Access with malformed/invalid JWT  
**Requirements:** REQ006

### Flow Steps

1. User provides invalid Authorization header
   - Example: `Authorization: Bearer invalid_xyz_token`
2. System attempts JWT decoding
3. Decoding fails (invalid signature/format)
4. System returns HTTP 401 with message: "Invalid credentials"

### Response Example

```json
{
  "detail": "Invalid credentials"
}
```

---

## USER FLOW 5: PAGINATION - REQUESTING MULTIPLE PAGES

**Actor:** Contact Person with large invoice (500+ lines)  
**Goal:** Retrieve lines in multiple page requests  
**Requirements:** REQ007, REQ001

### Flow Steps

**Request Page 1:**
- URL: `GET /api/v1/invoices/INV-2026-001234/lines?page=1&page_size=100`
- System returns lines 1-100
- Response includes: `page: 1, total_pages: 5, total_records: 500`

**Request Page 2:**
- URL: `GET /api/v1/invoices/INV-2026-001234/lines?page=2&page_size=100`
- System calculates offset: (2-1) * 100 = 100
- System returns lines 101-200
- Response includes: `page: 2, total_pages: 5, total_records: 500`

**Request Page 5 (last):**
- URL: `GET /api/v1/invoices/INV-2026-001234/lines?page=5&page_size=100`
- System calculates offset: (5-1) * 100 = 400
- System returns lines 401-500 (only 100 records)
- Response includes: `page: 5, total_pages: 5`

**Request Page 6 (beyond end):**
- URL: `GET /api/v1/invoices/INV-2026-001234/lines?page=6&page_size=100`
- System calculates offset: (6-1) * 100 = 500
- System returns empty array
- Response includes: `page: 6, invoice_lines: [], total_pages: 5`

### Pagination Validation

**Invalid page=0:**
- System validates: page < 1
- Returns HTTP 400: "Page must be >= 1"

**Invalid page_size=0:**
- System validates: page_size < 1
- Returns HTTP 400: "Page size must be >= 1"

**Oversized page_size=50000:**
- System validates: page_size > 10000
- System caps: page_size = 10000
- Returns data with page_size=10000 in response

---

## USER FLOW 6: INVOICE WITH NO LINES

**Actor:** Contact Person  
**Goal:** Request invoice that exists but has zero line items  
**Requirements:** REQ001, REQ002, REQ005

### Flow Steps

1. User requests: `GET /api/v1/invoices/INV-EMPTY-001/lines?page=1&page_size=100`
2. System authenticates (success)
3. System authorizes (invoice belongs to user)
4. System queries lines (returns empty result set, total_count=0)
5. System returns HTTP 200 with empty response

### Response Example

```json
{
  "invoice_id": "INV-EMPTY-001",
  "contact_person_id": "CP-5678",
  "total_records": 0,
  "page": 1,
  "page_size": 100,
  "total_pages": 0,
  "invoice_lines": []
}
```

---

## USER FLOW 7: PERFORMANCE - LARGE INVOICE RETRIEVAL

**Actor:** Contact Person  
**Goal:** Retrieve max-size page (10,000 lines)  
**Requirements:** REQ008

### Flow Steps

1. User requests: `GET /api/v1/invoices/INV-LARGE-001/lines?page=1&page_size=10000`
2. System processes:
   - Validates page_size (10000 <= max 10000) ✓
   - Executes optimized query with indexes
   - Database indexes: (invoice_id, line_order)
   - Returns 10,000 records
3. System response time: < 500ms (REQ008 SLA)
4. User receives response with all 10,000 lines

---

## AUTOMATION TEST SCENARIOS

### Scenario 1: Happy Path - Complete User Journey
```
GIVEN: Authenticated user with valid token
WHEN: User requests first page of invoice lines
THEN: Response is 200 OK with 100 lines ordered by line_order
AND: Response includes pagination metadata
AND: All 8 required fields present in each line
```

### Scenario 2: Authorization - Cross-User Isolation
```
GIVEN: Authenticated user CP-5678
WHEN: User requests invoice owned by CP-9999
THEN: Response is 404 "Not found or not accessible"
AND: No information about existence/authorization status leaked
```

### Scenario 3: Authentication - Missing Token
```
GIVEN: User without JWT token
WHEN: User makes request without Authorization header
THEN: Response is 401 "Not authenticated"
```

### Scenario 4: Pagination - Page Navigation
```
GIVEN: Invoice with 250 lines, page_size=100
WHEN: User requests page 1, page 2, page 3
THEN: Page 1 returns lines 1-100
AND: Page 2 returns lines 101-200
AND: Page 3 returns lines 201-250 (only 50 lines)
```

### Scenario 5: Pagination - Invalid Parameters
```
GIVEN: User requests page=0
WHEN: System validates pagination
THEN: Response is 400 with "Page must be >= 1"

GIVEN: User requests page_size=50001
WHEN: System validates page_size
THEN: System caps to 10000 and returns page_size=10000
```

### Scenario 6: Ordering - Line Sequence
```
GIVEN: Invoice with 5 lines having line_order: 3, 1, 5, 2, 4
WHEN: System retrieves lines
THEN: Response includes lines in order: 1, 2, 3, 4, 5
AND: line_order field in response matches sequence
```

### Scenario 7: Error Handling - Nonexistent Invoice
```
GIVEN: Invoice ID that doesn't exist
WHEN: System authorization check runs
THEN: Response is 404 "Invoice not found or not accessible"
AND: No database error exposed to user
```

---

## INTEGRATION TESTING CHECKLIST

- [ ] Happy path: Authenticated user retrieves first page
- [ ] Authorization: Same user cannot access other user's invoice
- [ ] Authentication: Requests without token return 401
- [ ] Token validation: Invalid tokens return 401
- [ ] Pagination: Page 1 returns correct records
- [ ] Pagination: Page 2 continues from offset
- [ ] Pagination: Beyond last page returns empty array
- [ ] Pagination: Page < 1 returns validation error
- [ ] Pagination: Page size > 10000 is capped
- [ ] Ordering: Lines returned in ascending line_order
- [ ] Empty invoice: Zero lines returns empty array with count=0
- [ ] Response schema: All required fields present
- [ ] Response schema: Decimal values formatted correctly
- [ ] Performance: Large page (10K lines) responds in < 500ms
- [ ] Error messages: No sensitive data in error responses

---

## CONCLUSION

All user flows map directly to requirements and are fully automatable through API testing. The service provides clear, deterministic behavior for all scenarios: success paths, error handling, authorization, pagination, and performance constraints.

