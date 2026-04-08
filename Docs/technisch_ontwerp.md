# TECHNISCH ONTWERP - PIVD-7043

**Story:** Invoice Lines Retrieval API

**Status:** Approved by Architect  
**Date:** 2026-04-08

**Tech Stack:** FastAPI + PostgreSQL + Python 3.11

---

## 1. MODULES ANALYSE

### WIJZIGINGEN (New/Modified)

| Module | Type | Omschrijving |
|--------|------|-------------|
| **API Layer** | NEW | FastAPI endpoint voor invoice line retrieval |
| **Business Layer (InvoiceService)** | NEW | Retrievelogica voor factuurregels met autorisatie |
| **Data Access Layer (InvoiceRepository)** | NEW | Query voor factuurregels + paginering |
| **Security Layer (AuthorizationService)** | NEW | Contact-person scope validation |
| **Mapping Layer (Schemas)** | NEW | Pydantic models: DB model → API response |

### ONAANGERAAKT

- Existing Invoice entity & table
- InvoiceLine table
- Contact person authentication flow
- Existing API endpoints

---

## 2. INTERFACE CONTRACTEN

### REST API Endpoint

```
Method: GET
Path: /api/v1/invoices/{invoice_id}/lines
Auth: Bearer token (JWT)
```

#### Request Parameters

```python
GET /api/v1/invoices/INV-2026-001234/lines?page=1&page_size=100

Headers:
  Authorization: Bearer <jwt_token>
  Accept: application/json

Query Parameters:
  - page: Integer (default: 1, min: 1)
  - page_size: Integer (default: 100, min: 1, max: 10000)
```

#### Response 200 (Success)

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
      "quantity": 5,
      "unit_price": 100.00,
      "tax_percentage": 21,
      "total_price": 605.00,
      "line_order": 1
    }
  ]
}
```

#### Response 404 (Not Found)

```json
{
  "detail": "Invoice not found or not accessible"
}
```

#### Response 401 (Unauthorized)

```json
{
  "detail": "Not authenticated"
}
```

---

## 3. DATASTROMEN

### Request Flow

```
Client Request (FastAPI)
  ↓
FastAPI Router: GET /invoices/{invoice_id}/lines
  ↓
Parameter Validation (Pydantic)
  ├─ invoice_id: String validation
  ├─ page: Integer validation
  └─ page_size: Integer validation (max 10000)
  ↓
Authentication Check (JWT token)
  └─ Extract contact_person_id from token
  ↓
InvoiceService.get_invoice_lines()
  ├─ Authorization: Verify invoice belongs to contact_person
  │  └─ Query: SELECT 1 FROM invoices WHERE id = ? AND contact_person_id = ?
  │     ├─ FOUND: Continue
  │     └─ NOT FOUND: Raise 404 Exception
  │
  └─ Retrieve invoice lines with pagination
     └─ Query: SELECT * FROM invoice_lines 
              WHERE invoice_id = ?
              ORDER BY line_order ASC
              LIMIT ? OFFSET ?
  ↓
Mapping Layer (Pydantic Schema)
  └─ Convert ORM objects to API DTOs
  ↓
Response (200 OK with JSON)
```

---

## 4. TECHNISCHE RISICO'S

| Risico | Severity | Mitigatie | Status |
|--------|----------|-----------|--------|
| **N+1 Query Problem** | HIGH | Single JOIN query, avoid loops | ✅ Mitigated |
| **Authorization Bypass** | CRITICAL | Dual-check: token scope + DB row-level security | ✅ Mitigated |
| **Performance: Large Invoices** | HIGH | Index on (invoice_id, contact_person_id), paginering | ✅ Mitigated |
| **Data Consistency** | MEDIUM | Invoice state could change during multi-page retrieval | ⚠️ KNOWN |
| **JSON Response Size** | MEDIUM | Pagination limits (max 10000 records) | ✅ Mitigated |
| **Backward Compatibility** | LOW | New endpoint, no existing API changes | ✅ N/A |

---

## 5. DATABASE SCHEMA

### Assumed Tables

```sql
-- Invoices table (existing)
CREATE TABLE invoices (
  id VARCHAR PRIMARY KEY,
  contact_person_id VARCHAR NOT NULL,
  invoice_date DATE,
  due_date DATE,
  total_amount DECIMAL(10,2),
  status VARCHAR,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_contact_invoice (contact_person_id, id)
);

-- Invoice lines table (existing or new)
CREATE TABLE invoice_lines (
  id VARCHAR PRIMARY KEY,
  invoice_id VARCHAR NOT NULL,
  article_code VARCHAR,
  description TEXT,
  quantity DECIMAL(10,4),
  unit_price DECIMAL(10,2),
  tax_percentage DECIMAL(5,2),
  total_price DECIMAL(10,2),
  line_order INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (invoice_id) REFERENCES invoices(id),
  INDEX idx_invoice_lines (invoice_id, line_order)
);
```

---

## 6. MINIMALE IMPLEMENTATIEROUTE

### Fase 1: API Layer (PIVD-8320)

- [ ] Create FastAPI router file: `routers/invoices.py`
- [ ] Define endpoint: GET `/invoices/{invoice_id}/lines`
- [ ] Parameter parsing & validation (Pydantic models)
- [ ] Response schemas
- [ ] Basic error handling (400, 401, 404)
- [ ] Stub service layer calls

### Fase 2: Business Layer (PIVD-8312)

- [ ] Create service: `services/invoice_service.py`
- [ ] Method: `get_invoice_lines(invoice_id, contact_person_id, page, page_size)`
- [ ] Authorization logic: Invoice ownership check
- [ ] Call repository for data
- [ ] Exception handling (NotFoundException, UnauthorizedException)
- [ ] Response DTO mapping

### Fase 3: Data Access

- [ ] Create repository: `repositories/invoice_repository.py`
- [ ] Method: `find_lines_by_invoice(invoice_id, offset, limit)`
- [ ] SQL query optimization
- [ ] Index validation/creation if needed
- [ ] Connection pooling configuration

### Fase 4: Testing (PIVD-8334)

- [ ] Unit tests per layer (see Unit Test Engineer output)
- [ ] Integration tests (API + database)
- [ ] Load/performance tests
- [ ] Security tests (authorization bypass attempts)

---

## 7. AFHANKELIJKHEDEN

### Python Package Dependencies

```
FastAPI 0.104.1         - API framework
SQLAlchemy 2.0.23       - ORM
psycopg 3.1.12          - PostgreSQL driver
pydantic 2.5.0          - Data validation
python-jose 3.3.0       - JWT handling
pytest 7.4.3            - Testing
```

See `requirements.txt` for complete list.

---

## 8. TESTBAARHEID IMPACT

### Unit Test Coverage

- ✓ Authorization service (token validation)
- ✓ Invoice service (business logic)
- ✓ Repository layer (database queries)
- ✓ API endpoint (request/response)
- ✓ Error handling (all exception paths)

### Integration Tests

- ✓ End-to-end API + database
- ✓ JWT token validation
- ✓ Pagination correctness
- ✓ Authorization enforcement

---

## 9. DEPLOYMENT STRATEGY

### Docker Container (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
```

### Environment Variables

```
DATABASE_URL=postgresql://user:pass@localhost:5432/invoice_db
JWT_SECRET_KEY=<secret>
JWT_ALGORITHM=HS256
API_PORT=8000
LOG_LEVEL=INFO
```

---

## 10. OPEN ARCHITECTUURVRAGEN

- [ ] Database indices: Zijn er indexes op (invoice_id, contact_person_id)?
- [ ] JWT implementation: Welke token format (HS256, RS256)?
- [ ] Caching: Redis caching nodig voor high traffic?
- [ ] Rate limiting: Implementeren per contact_person?
- [ ] Audit logging: Request/response logging nodig?

