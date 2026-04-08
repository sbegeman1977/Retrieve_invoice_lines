# Invoice Lines Retrieval API

**Story:** PIVD-7043  
**Status:** Implementation Complete  
**Tech Stack:** FastAPI + PostgreSQL + Python 3.11

## Overview

Public API for retrieving detailed invoice lines for a specific invoice of a contact person. Allows external applications to fetch invoice breakdowns via a secure REST endpoint.

## Features

- ✅ REQ001: Retrieve all invoice lines for a specific invoice
- ✅ REQ002: Complete invoice line data structure (article, quantity, prices, tax)
- ✅ REQ003: Authorization - contact persons can only access their own invoices
- ✅ REQ004: Invoice lines properly ordered by line_order
- ✅ REQ005: 404 error handling for non-existent/inaccessible invoices
- ✅ REQ006: JWT authentication required (Bearer token)
- ✅ REQ007: Pagination support (limit-offset, max 10,000 records per page)
- ✅ REQ008: Optimized performance (P95 < 500ms for standard invoices)

## Project Structure

```
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database connection & session management
│   ├── security.py             # JWT authentication
│   ├── exceptions.py           # Custom exceptions
│   ├── models/
│   │   └── invoice.py          # SQLAlchemy models (Invoice, InvoiceLine)
│   ├── schemas/
│   │   └── invoice.py          # Pydantic request/response schemas
│   ├── services/
│   │   └── invoice_service.py  # Business logic layer
│   ├── repositories/
│   │   └── invoice_repository.py # Data access layer
│   └── routers/
│       └── invoices.py         # API endpoints
├── tests/
│   ├── test_invoice_service.py # 21 unit tests
│   └── test_invoice_api.py     # 18 API integration tests
├── Docs/
│   ├── functioneel_ontwerp.md  # Functional design (8 requirements)
│   ├── technisch_ontwerp.md    # Technical design (architecture, schemas)
│   └── test_strategy.md        # Test strategy (39 test cases)
├── requirements.txt            # Production dependencies
├── pyproject.toml              # Project configuration
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- pip & virtualenv

### Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/sbegeman1977/Retrieve_invoice_lines.git
   cd Retrieve_invoice_lines
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python -c "from src.database import init_db; init_db()"
   ```

## Running the API

### Development

```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

### Production

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app
```

## API Usage

### Endpoint

```
GET /api/v1/invoices/{invoice_id}/lines
```

### Authentication

Include JWT Bearer token in Authorization header:

```bash
Authorization: Bearer <your_jwt_token>
```

### Query Parameters

- `page` (integer, default=1): Page number (1-indexed)
- `page_size` (integer, default=100): Records per page (max 10,000)

### Example Request

```bash
curl -X GET "http://localhost:8000/api/v1/invoices/INV-2026-001234/lines?page=1&page_size=100" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Example Response

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

### Status Codes

- **200 OK**: Successfully retrieved invoice lines
- **400 Bad Request**: Invalid pagination parameters
- **401 Unauthorized**: Missing or invalid authentication
- **404 Not Found**: Invoice not found or not accessible
- **500 Internal Server Error**: Server error

## Testing

### Run All Tests

```bash
pytest tests/ -v --cov=src
```

### Run Unit Tests

```bash
pytest tests/test_invoice_service.py -v --cov=src.services
```

### Run API Tests

```bash
pytest tests/test_invoice_api.py -v
```

### Test Coverage

- **Unit Tests:** 21 tests covering service layer
- **API Tests:** 18 tests covering endpoint behavior
- **Coverage:** 98% of requirements (39 test cases)

## Database Schema

### Invoices Table

```sql
CREATE TABLE invoices (
  id VARCHAR PRIMARY KEY,
  contact_person_id VARCHAR NOT NULL,
  invoice_date TIMESTAMP,
  due_date TIMESTAMP,
  total_amount DECIMAL(10,2),
  status VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_contact_invoice (contact_person_id, id)
);
```

### Invoice Lines Table

```sql
CREATE TABLE invoice_lines (
  id VARCHAR PRIMARY KEY,
  invoice_id VARCHAR NOT NULL REFERENCES invoices(id),
  article_code VARCHAR(50),
  description VARCHAR(500),
  quantity DECIMAL(10,4),
  unit_price DECIMAL(10,2),
  tax_percentage DECIMAL(5,2),
  total_price DECIMAL(10,2),
  line_order INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_invoice_lines (invoice_id, line_order)
);
```

## Architecture

### Layered Architecture

```
FastAPI Router (API Layer - PIVD-8320)
       ↓
InvoiceService (Business Layer - PIVD-8312)
       ↓
InvoiceRepository (Data Access Layer)
       ↓
SQLAlchemy ORM → PostgreSQL Database
```

### Security

- **Authentication:** JWT Bearer token validation
- **Authorization:** Row-level security (contact person isolation)
- **Input Validation:** Pydantic models on all inputs
- **SQL Injection Prevention:** Parameterized queries via SQLAlchemy ORM

## Performance

### Optimizations

- Database indexes on (invoice_id, contact_person_id) and (invoice_id, line_order)
- Pagination to limit result set size (max 10,000 records)
- Connection pooling (pool_size=10, max_overflow=20)
- Query optimization (single JOIN query, no N+1 problems)

### Expected Performance

- Standard invoice (< 100 lines): P95 < 500ms
- Large invoice (up to 10,000 lines): < 2 seconds

## Configuration

### Environment Variables

```
DATABASE_URL=postgresql://user:password@host:5432/database
JWT_SECRET_KEY=your-secret-key (change in production!)
JWT_ALGORITHM=HS256
API_HOST=0.0.0.0
API_PORT=8000
ENV=development
LOG_LEVEL=INFO
SQL_ECHO=False
```

## Error Handling

### Exception Hierarchy

```
InvoiceAPIException (base)
├── InvoiceNotFoundException (404)
├── UnauthorizedException (403)
├── AuthenticationException (401)
└── InvalidPaginationException (400)
```

## Documentation

- **Functional Design:** `Docs/functioneel_ontwerp.md`
- **Technical Design:** `Docs/technisch_ontwerp.md`
- **Test Strategy:** `Docs/test_strategy.md`
- **API Docs:** http://localhost:8000/docs (Swagger)

## Development

### Code Style

- Black code formatter
- isort import sorting
- flake8 linting
- mypy type checking

### Format Code

```bash
black src/ tests/
isort src/ tests/
```

### Lint Code

```bash
flake8 src/ tests/
mypy src/
```

## Troubleshooting

### Database Connection Error

1. Verify PostgreSQL is running
2. Check DATABASE_URL in .env
3. Verify credentials are correct

### Authentication Error

1. Ensure JWT token is valid and not expired
2. Check JWT_SECRET_KEY matches token generation
3. Verify Authorization header format: `Bearer <token>`

### Pagination Error

1. Ensure page >= 1
2. Ensure page_size >= 1 and <= 10,000
3. Check total_pages calculation

## Future Enhancements

- [ ] Rate limiting per contact person
- [ ] Caching layer (Redis)
- [ ] Filtering and sorting options
- [ ] GraphQL endpoint
- [ ] Webhook notifications for invoice changes
- [ ] Audit logging

## License

Proprietary - Zvoove

## Contact

**Team:** RTteam - Green  
**Project Manager:** Ewout Spit  
**QICS Project:** SA.2650
