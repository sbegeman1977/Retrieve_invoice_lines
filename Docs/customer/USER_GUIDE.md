# User Guide - Invoice Lines Retrieval API v1.0.0

**Version:** 1.0.0  
**Last Updated:** April 8, 2026  
**Audience:** Developers, Integration Engineers, End Users

---

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Concepts](#basic-concepts)
3. [Authentication](#authentication)
4. [Making Your First Request](#making-your-first-request)
5. [Common Use Cases](#common-use-cases)
6. [Pagination Strategies](#pagination-strategies)
7. [Error Handling](#error-handling)
8. [Code Examples](#code-examples)
9. [Best Practices](#best-practices)
10. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Getting Started

### What Is This API?

The Invoice Lines Retrieval API allows you to programmatically access detailed line-item information from invoices. Each invoice can contain multiple line items (products, services), and this API lets you retrieve all of them in a structured, paginated format.

**Example Use Cases:**
- 📊 Automated invoice reconciliation
- 💰 Financial reporting and analytics
- 📦 Inventory tracking
- 🧾 Accounting software integration
- 📈 Business intelligence dashboards

### 5-Minute Quick Start

1. **Get a JWT Token** (from your administrator)
2. **Make a Simple Request:**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.yourcompany.com/api/v1/invoices/INV-12345/lines?page=1&page_size=100
   ```
3. **Parse the JSON Response** and use the data
4. **Implement Pagination** to handle larger invoices
5. **Add Error Handling** for production robustness

---

## Basic Concepts

### Invoice vs. Invoice Line

**Invoice:**
- Represents a complete billing document
- Has one invoice ID (e.g., "INV-12345")
- Contains multiple line items

**Invoice Line:**
- Represents a single item on an invoice
- Has quantity, unit price, tax, and total
- Ordered by line_order for proper sequencing

### Example: Breaking Down an Invoice

```
Invoice: INV-12345
├─ Line 1: Premium Product (Qty: 5, Price: 100.00 each)
├─ Line 2: Standard Service (Qty: 10, Price: 50.00 each)
├─ Line 3: Shipping Fee (Qty: 1, Price: 25.00)
└─ Line 4: Discount (Qty: 1, Price: -10.00)
```

### Key Terms

| Term | Meaning | Example |
|------|---------|---------|
| **Invoice ID** | Unique identifier for an invoice | "INV-12345" |
| **Line ID** | Unique identifier for a line item | "IL-001" |
| **Article Code** | Product/service code | "ART-12345" |
| **Page** | Current page in paginated results | Page 2 of 10 |
| **Page Size** | Records per page (1-10,000) | 100 records |

---

## Authentication

### Obtaining a JWT Token

JWT (JSON Web Token) is a secure way to authenticate API requests. Your token proves you are who you say you are.

**How to get a token:**

1. **Contact Your Administrator**
   - Request API access
   - Provide your contact person ID
   - Receive authentication credentials

2. **Generate Token via Your Identity Provider**
   - Use provided client ID and secret
   - Request a JWT token
   - Token is valid for 1-24 hours (depends on your settings)

3. **Store Safely**
   - Never hardcode tokens in source code
   - Use environment variables or secrets management
   - Regenerate periodically (monthly recommended)

### Using Your Token

**Always Include in Authorization Header:**
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Examples:**

Using cURL:
```bash
curl -H "Authorization: Bearer TOKEN" https://api.yourcompany.com/api/v1/invoices/INV-001/lines
```

Using Python:
```python
import requests

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
response = requests.get(url, headers=headers)
```

Using JavaScript:
```javascript
const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};
fetch(url, { headers })
    .then(response => response.json())
    .then(data => console.log(data));
```

---

## Making Your First Request

### Step 1: Prepare Your Request

**Gather Information:**
- ✅ Invoice ID (e.g., "INV-12345")
- ✅ JWT Token (from authentication)
- ✅ API URL (https://api.yourcompany.com)

### Step 2: Construct the URL

**Format:**
```
https://api.yourcompany.com/api/v1/invoices/{invoice_id}/lines?page={page}&page_size={page_size}
```

**Example:**
```
https://api.yourcompany.com/api/v1/invoices/INV-12345/lines?page=1&page_size=100
```

### Step 3: Send the Request

**Using cURL (command-line):**
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "https://api.yourcompany.com/api/v1/invoices/INV-12345/lines?page=1&page_size=100"
```

**Using Postman (GUI):**
1. Create new GET request
2. Enter URL: `https://api.yourcompany.com/api/v1/invoices/INV-12345/lines?page=1`
3. Go to Headers tab
4. Add: `Authorization: Bearer YOUR_JWT_TOKEN`
5. Click Send

### Step 4: Review the Response

**Success Response (200 OK):**
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
    }
  ]
}
```

**What This Means:**
- `total_records: 250` - Invoice has 250 lines total
- `total_pages: 3` - Need 3 requests (page 1, 2, 3) to get all lines
- `invoice_lines` - Array with the actual line data
- `line_order: 1` - This is the first item on the invoice

---

## Common Use Cases

### Use Case 1: Get All Invoice Lines

**Scenario:** You want to download all 250 lines from invoice INV-12345.

**Solution:**
```python
import requests

def get_all_invoice_lines(invoice_id, token):
    all_lines = []
    page = 1
    page_size = 1000  # Large page size for efficiency
    
    while True:
        # Request current page
        url = f"https://api.yourcompany.com/api/v1/invoices/{invoice_id}/lines"
        params = {"page": page, "page_size": page_size}
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        
        # Add lines from this page
        all_lines.extend(data['invoice_lines'])
        
        # Check if we have all pages
        if page >= data['total_pages']:
            break
        
        page += 1
    
    return all_lines

# Usage
lines = get_all_invoice_lines("INV-12345", token)
print(f"Retrieved {len(lines)} invoice lines")
```

### Use Case 2: Export Invoice to CSV

**Scenario:** Export invoice lines to a CSV file for spreadsheet analysis.

**Solution:**
```python
import csv
import requests

def export_invoice_to_csv(invoice_id, token, filename):
    # Get all lines
    lines = get_all_invoice_lines(invoice_id, token)
    
    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['line_id', 'article_code', 'description', 'quantity', 
                     'unit_price', 'tax_percentage', 'total_price', 'line_order']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for line in lines:
            writer.writerow({
                'line_id': line['line_id'],
                'article_code': line['article_code'],
                'description': line['description'],
                'quantity': line['quantity'],
                'unit_price': line['unit_price'],
                'tax_percentage': line['tax_percentage'],
                'total_price': line['total_price'],
                'line_order': line['line_order']
            })
    
    print(f"Exported {len(lines)} lines to {filename}")

# Usage
export_invoice_to_csv("INV-12345", token, "invoice_lines.csv")
```

### Use Case 3: Verify Invoice Totals

**Scenario:** Calculate invoice totals from line items and verify accuracy.

**Solution:**
```python
from decimal import Decimal

def calculate_invoice_total(invoice_id, token):
    lines = get_all_invoice_lines(invoice_id, token)
    
    subtotal = Decimal('0.00')
    total_tax = Decimal('0.00')
    grand_total = Decimal('0.00')
    
    for line in lines:
        line_subtotal = Decimal(str(line['unit_price'])) * Decimal(str(line['quantity']))
        line_tax = line_subtotal * (Decimal(str(line['tax_percentage'])) / 100)
        line_total = line_subtotal + line_tax
        
        subtotal += line_subtotal
        total_tax += line_tax
        grand_total += line_total
    
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Total Tax: ${total_tax:.2f}")
    print(f"Grand Total: ${grand_total:.2f}")
    
    return {
        'subtotal': subtotal,
        'tax': total_tax,
        'total': grand_total
    }

# Usage
totals = calculate_invoice_total("INV-12345", token)
```

### Use Case 4: Display Invoice in Dashboard

**Scenario:** Show invoice lines in a web dashboard with pagination.

**Solution:**
```python
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/invoice/<invoice_id>')
def show_invoice(invoice_id):
    # Get page number from URL (default 1)
    page = request.args.get('page', 1, type=int)
    page_size = 50  # Smaller page size for interactive UI
    
    # Fetch data from API
    url = f"https://api.yourcompany.com/api/v1/invoices/{invoice_id}/lines"
    params = {"page": page, "page_size": page_size}
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    # Render template with data and pagination info
    return render_template('invoice.html',
        invoice_id=invoice_id,
        lines=data['invoice_lines'],
        page=data['page'],
        total_pages=data['total_pages'],
        total_records=data['total_records']
    )

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Pagination Strategies

### Strategy 1: Small Pages (Interactive UI)

**Use When:** Displaying data in web dashboards or mobile apps

```python
# Get first 50 records for fast initial load
page_size = 50
page = 1

# User clicks "Next" button
page += 1

# Fetch next 50 records
```

**Pros:** Fast initial load, smooth navigation  
**Cons:** More API calls for complete data

### Strategy 2: Large Pages (Bulk Data Export)

**Use When:** Exporting all data, batch processing

```python
# Get all 10,000 records in one call (if needed)
page_size = 10000
page = 1

# Process all records
for line in response['invoice_lines']:
    process(line)
```

**Pros:** Minimal API calls, efficient bulk processing  
**Cons:** Larger response, slower initial load

### Strategy 3: Smart Pagination

**Use When:** You don't know the data size in advance

```python
def fetch_all_data(invoice_id, token):
    page = 1
    page_size = 1000  # Balance between speed and size
    all_lines = []
    
    while True:
        # Fetch page
        response = fetch_page(invoice_id, page, page_size, token)
        lines = response['invoice_lines']
        
        if not lines:
            break
        
        all_lines.extend(lines)
        
        # Stop if we've fetched everything
        if len(all_lines) >= response['total_records']:
            break
        
        page += 1
    
    return all_lines
```

---

## Error Handling

### Common Errors

#### Error 1: Missing Token (401 Unauthorized)

**What You See:**
```json
{"detail": "Not authenticated"}
```

**Why:** Authorization header is missing or invalid

**Fix:**
```python
# ❌ Wrong - no auth header
response = requests.get(url)

# ✅ Correct - include auth header
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(url, headers=headers)
```

#### Error 2: Invalid Invoice (404 Not Found)

**What You See:**
```json
{"detail": "Invoice not found or not accessible"}
```

**Why:** 
- Invoice doesn't exist
- You don't have permission to access it

**Fix:**
```python
# Verify invoice ID
print(f"Looking for invoice: {invoice_id}")

# Check if error is due to permissions
# Contact your administrator for access
```

#### Error 3: Invalid Page (400 Bad Request)

**What You See:**
```json
{"detail": "Page must be >= 1"}
```

**Why:** Invalid page number (0, negative, or non-numeric)

**Fix:**
```python
# ❌ Wrong - page 0
url = f"...?page=0"

# ✅ Correct - pages start at 1
url = f"...?page=1"
```

#### Error 4: Page Size Too Large (400 Bad Request)

**What You See:**
```json
{"detail": "Page size must be <= 10000"}
```

**Why:** Requesting more than 10,000 records per page

**Fix:**
```python
# ❌ Wrong
page_size = 50000

# ✅ Correct
page_size = 10000  # Maximum allowed
```

### Implementing Error Handling

```python
import requests
import time

def fetch_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            # Check for HTTP errors
            if response.status_code == 401:
                print("❌ Unauthorized - check your token")
                raise Exception("Invalid authentication token")
            
            elif response.status_code == 404:
                print("❌ Invoice not found - check invoice ID")
                raise Exception("Invoice not found or not accessible")
            
            elif response.status_code == 400:
                print("❌ Bad request - check parameters")
                print(f"Details: {response.json()}")
                raise Exception("Invalid request parameters")
            
            elif response.status_code >= 500:
                print(f"⚠️ Server error - retrying (attempt {attempt + 1})")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            
            # Success
            return response.json()
        
        except requests.exceptions.ConnectionError:
            print(f"⚠️ Connection error - retrying (attempt {attempt + 1})")
            time.sleep(2 ** attempt)
        
        except Exception as e:
            print(f"❌ Error: {e}")
            raise
    
    raise Exception("Failed after maximum retries")

# Usage
try:
    data = fetch_with_retry(url, headers)
    print(f"✅ Successfully retrieved {len(data['invoice_lines'])} lines")
except Exception as e:
    print(f"Failed: {e}")
```

---

## Code Examples

### Example 1: Python with Requests

```python
import requests
import json

# Configuration
TOKEN = "your-jwt-token-here"
API_URL = "https://api.yourcompany.com/api/v1"
INVOICE_ID = "INV-12345"

# Make request
headers = {"Authorization": f"Bearer {TOKEN}"}
url = f"{API_URL}/invoices/{INVOICE_ID}/lines?page=1&page_size=100"

response = requests.get(url, headers=headers)

# Check status
if response.status_code == 200:
    data = response.json()
    print(f"Invoice: {data['invoice_id']}")
    print(f"Total lines: {data['total_records']}")
    
    for line in data['invoice_lines']:
        print(f"  - {line['article_code']}: {line['description']} x{line['quantity']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### Example 2: JavaScript/Node.js

```javascript
const fetch = require('node-fetch');

const TOKEN = "your-jwt-token-here";
const API_URL = "https://api.yourcompany.com/api/v1";
const INVOICE_ID = "INV-12345";

async function getInvoiceLines() {
    const headers = {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
    };
    
    const url = `${API_URL}/invoices/${INVOICE_ID}/lines?page=1&page_size=100`;
    
    try {
        const response = await fetch(url, { headers });
        
        if (response.ok) {
            const data = await response.json();
            console.log(`Invoice: ${data.invoice_id}`);
            console.log(`Total lines: ${data.total_records}`);
            
            data.invoice_lines.forEach(line => {
                console.log(`  - ${line.article_code}: ${line.description} x${line.quantity}`);
            });
        } else {
            console.error(`Error: ${response.status}`);
            console.error(await response.json());
        }
    } catch (error) {
        console.error(`Request failed: ${error}`);
    }
}

getInvoiceLines();
```

### Example 3: cURL (Command-Line)

```bash
# Set variables
TOKEN="your-jwt-token-here"
API_URL="https://api.yourcompany.com/api/v1"
INVOICE_ID="INV-12345"

# Make request
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$API_URL/invoices/$INVOICE_ID/lines?page=1&page_size=100" \
  | jq '.'  # Pretty-print JSON

# Extract just the line items
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "$API_URL/invoices/$INVOICE_ID/lines?page=1&page_size=100" \
  | jq '.invoice_lines[] | {code: .article_code, qty: .quantity, total: .total_price}'
```

---

## Best Practices

### 1. Token Management

```python
# ❌ Bad: Hardcoded token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# ✅ Good: Load from environment
import os
TOKEN = os.getenv('API_TOKEN')

# ✅ Better: Use secrets manager
from aws_secretsmanager_caching import SecretCache
cache = SecretCache()
TOKEN = cache.get_secret_string('api-token')
```

### 2. Request Timeout

```python
# ❌ Bad: No timeout (can hang forever)
response = requests.get(url)

# ✅ Good: Set reasonable timeout
response = requests.get(url, timeout=30)  # 30 second timeout
```

### 3. Connection Reuse

```python
# ❌ Bad: Creating new session for each request (slow)
for page in range(1, 10):
    response = requests.get(url)

# ✅ Good: Reuse session (faster)
session = requests.Session()
for page in range(1, 10):
    response = session.get(url)
```

### 4. Logging & Monitoring

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_invoice_lines(invoice_id):
    start_time = time.time()
    try:
        response = requests.get(url, timeout=10)
        elapsed = time.time() - start_time
        logger.info(f"Successfully retrieved invoice {invoice_id} in {elapsed:.2f}s")
        return response.json()
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to retrieve invoice {invoice_id}: {e} ({elapsed:.2f}s)")
        raise
```

### 5. Data Validation

```python
from decimal import Decimal

def validate_line(line):
    # Type checking
    assert isinstance(line['line_id'], str)
    assert isinstance(line['quantity'], (int, float, Decimal))
    
    # Business logic validation
    assert Decimal(str(line['quantity'])) > 0, "Quantity must be > 0"
    assert Decimal(str(line['unit_price'])) > 0, "Price must be > 0"
    assert Decimal(str(line['tax_percentage'])) >= 0, "Tax % must be >= 0"
    
    return True

# Usage
for line in response['invoice_lines']:
    if validate_line(line):
        process_line(line)
```

---

## FAQ & Troubleshooting

### Q1: How do I get a JWT token?

**A:** Contact your system administrator and request API access. They will either:
1. Provide you with a token directly, or
2. Give you credentials to generate tokens from your identity provider

### Q2: How long does a token last?

**A:** Token lifetime depends on your organization's settings (typically 1-24 hours). Check with your administrator.

### Q3: Can I retrieve all invoice lines in one request?

**A:** Yes, use `page_size=10000` to get up to 10,000 lines per request. If invoice has fewer lines, all will be returned.

### Q4: What's the maximum number of invoice lines I can request?

**A:** Maximum page size is 10,000 records. Larger invoices require multiple requests (pagination).

### Q5: How do I calculate invoice totals correctly?

**A:** Use the `total_price` field from each line item. Sum all `total_price` values to get the invoice total.

### Q6: Are responses cached?

**A:** No, every request retrieves current data from the database. Implement your own caching if needed.

### Q7: What should I do if the API is down?

**A:** The API targets 99.9% availability. If you experience outages:
1. Check status page: https://status.yourcompany.com
2. Wait 5-10 minutes and retry
3. Contact support if issue persists

### Q8: Can I filter invoice lines?

**A:** No, the API returns all lines. Filter results in your application after retrieval.

### Q9: Is there a rate limit?

**A:** No explicit rate limit currently. Use reasonable request patterns (1-10 requests per second recommended).

### Q10: How do I know if a request failed?

**A:** Check the HTTP status code:
- 200-299: Success
- 400-499: Client error (check your request)
- 500-599: Server error (retry with backoff)

---

## Getting Help

**Documentation:**
- Read the [API Documentation](API_DOCUMENTATION.md) for detailed endpoint specs
- Review the [Deployment Guide](DEPLOYMENT_GUIDE.md) for setup help
- Check [Release Notes](RELEASE_NOTES_v1.0.0.md) for what's new

**Support:**
- 📧 Email: support@yourcompany.com
- 📞 Phone: +1-XXX-XXX-XXXX
- 🆘 Emergency: On-call engineer (24/7)

---

*User Guide v1.0.0*  
*Last Updated: April 8, 2026*  
*Status: Production Ready*
