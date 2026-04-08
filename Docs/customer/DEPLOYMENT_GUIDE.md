# Deployment Guide - Invoice Lines Retrieval API v1.0.0

**Version:** 1.0.0  
**Last Updated:** April 8, 2026  
**Audience:** DevOps, System Administrators, IT Operations

---

## Table of Contents
1. [Pre-Deployment Requirements](#pre-deployment-requirements)
2. [Environment Setup](#environment-setup)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Security Hardening](#security-hardening)
6. [Deployment Procedure](#deployment-procedure)
7. [Verification & Testing](#verification--testing)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Troubleshooting](#troubleshooting)
10. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Requirements

### Hardware Requirements

**Minimum (Single Instance):**
- CPU: 2 vCPU cores
- RAM: 2 GB
- Storage: 20 GB (for application + logs)
- Network: 100 Mbps connection

**Recommended (Production - 2 Instances):**
- CPU: 4 vCPU cores per instance
- RAM: 4 GB per instance
- Storage: 50 GB per instance
- Network: Gigabit connection

**High-Scale (100+ concurrent users):**
- CPU: 8+ vCPU cores per instance
- RAM: 8+ GB per instance
- Storage: 100+ GB per instance
- Multiple instances behind load balancer

### Software Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.9+ | Runtime environment |
| PostgreSQL | 12+ | Database |
| Docker | 20.10+ (optional) | Containerization |
| nginx | 1.18+ (optional) | Reverse proxy |

### Network Requirements
- ✅ HTTPS/TLS support (port 443)
- ✅ Database connectivity to PostgreSQL
- ✅ Outbound DNS (for token validation)
- ✅ No firewall restrictions between API and database

### Access Requirements
- Database administrator credentials
- System-level access to deployment server
- SSL/TLS certificate (valid domain certificate)
- Git access to code repository

---

## Environment Setup

### 1. Python Environment

**Install Python 3.9+:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.9 python3.9-venv python3.9-dev

# Verify installation
python3.9 --version
```

**Create Virtual Environment:**
```bash
python3.9 -m venv /opt/invoice-api/venv
source /opt/invoice-api/venv/bin/activate
```

### 2. Database Setup

**Create PostgreSQL Database:**
```bash
# Connect to PostgreSQL as admin
sudo -u postgres psql

# Create database
CREATE DATABASE invoice_lines_api;

# Create user with limited permissions
CREATE USER api_user WITH PASSWORD 'strong_password_here';
GRANT CONNECT ON DATABASE invoice_lines_api TO api_user;

# Grant table permissions
\c invoice_lines_api
GRANT USAGE ON SCHEMA public TO api_user;
GRANT CREATE ON SCHEMA public TO api_user;
```

**Verify Connection:**
```bash
psql -h localhost -U api_user -d invoice_lines_api -c "SELECT version();"
```

### 3. System User

**Create Dedicated Application User:**
```bash
# Create unprivileged user for application
sudo useradd -r -s /bin/bash -d /opt/invoice-api invoice-app

# Set ownership
sudo chown -R invoice-app:invoice-app /opt/invoice-api
```

---

## Installation

### 1. Clone Repository

```bash
cd /opt/invoice-api
git clone https://github.com/yourcompany/invoice-api.git .
git checkout v1.0.0  # Check out release tag
```

### 2. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
# Test imports
python -c "import fastapi; import sqlalchemy; import psycopg; print('✅ All dependencies installed')"
```

---

## Configuration

### 1. Environment Variables

Create `.env` file (do not commit to version control):

```bash
# Database Configuration
DATABASE_URL=postgresql://api_user:strong_password@localhost:5432/invoice_lines_api

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-min-32-characters-long-recommended
JWT_ALGORITHM=HS256

# Application Configuration
API_HOST=0.0.0.0
API_PORT=8000
SQL_ECHO=False  # Set to True only for debugging

# CORS Configuration
ALLOWED_ORIGINS=["https://yourcompany.com", "https://app.yourcompany.com"]
```

**Security Notes:**
- 🔐 Keep `JWT_SECRET_KEY` secret (rotate regularly)
- 🔐 Use strong database password
- 🔐 Never commit `.env` to version control
- 🔐 Limit file permissions: `chmod 600 .env`

### 2. Generate JWT Secret

```bash
# Generate cryptographically secure secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Database Initialization

```bash
# Create tables (if not using migrations)
python -c "from src.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 4. SSL/TLS Certificate

**Using Let's Encrypt (Recommended):**
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d api.yourcompany.com

# Certificate locations:
# - Public key: /etc/letsencrypt/live/api.yourcompany.com/fullchain.pem
# - Private key: /etc/letsencrypt/live/api.yourcompany.com/privkey.pem
```

---

## Security Hardening

### 1. Database Security

```sql
-- Limit api_user privileges
REVOKE ALL PRIVILEGES ON DATABASE invoice_lines_api FROM api_user;
GRANT CONNECT ON DATABASE invoice_lines_api TO api_user;

-- Grant table-specific permissions only
GRANT SELECT ON invoices TO api_user;
GRANT SELECT ON invoice_lines TO api_user;

-- Enforce SSL connections
ALTER SYSTEM SET ssl = on;
-- Reload PostgreSQL
sudo systemctl reload postgresql
```

### 2. Application Security

```bash
# Run application as unprivileged user
sudo -u invoice-app python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Restrict file permissions
chmod 700 /opt/invoice-api
chmod 600 /opt/invoice-api/.env
chmod 600 /opt/invoice-api/config/*
```

### 3. Network Security

**Firewall Configuration (UFW):**
```bash
# Allow HTTPS only (no HTTP)
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH for admin

# Block direct database access
sudo ufw deny 5432/tcp
```

**nginx Reverse Proxy Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name api.yourcompany.com;

    ssl_certificate /etc/letsencrypt/live/api.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourcompany.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Proxy to application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourcompany.com;
    return 301 https://$server_name$request_uri;
}
```

### 4. Secrets Management

```bash
# Option 1: Environment variables (simple)
export DATABASE_URL=postgresql://...
export JWT_SECRET_KEY=...

# Option 2: HashiCorp Vault (enterprise)
# Option 3: AWS Secrets Manager (cloud)
# Option 4: Kubernetes Secrets (container)

# Never hardcode secrets!
# ❌ Bad: password = "secret123"
# ✅ Good: password = os.getenv("DATABASE_PASSWORD")
```

---

## Deployment Procedure

### Staging Deployment (Day 0)

**1. Deploy to Staging:**
```bash
# Pull latest code
cd /opt/invoice-api-staging
git pull origin main
git checkout v1.0.0

# Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.staging .env

# Test application
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001

# Verify: http://localhost:8001/docs
```

**2. Run Smoke Tests:**
```bash
# Test database connection
python -c "from src.database import SessionLocal; db = SessionLocal(); print('✅ Database connection OK')"

# Test API endpoint
curl -H "Authorization: Bearer TEST_TOKEN" \
  http://localhost:8001/api/v1/invoices/TEST-001/lines

# Expected: 401 (missing/invalid token is expected in test)
```

### Load Testing (Day 0 PM)

**1. Performance Validation:**
```bash
# Using Apache Bench (ab)
ab -n 1000 -c 100 -H "Authorization: Bearer VALID_TOKEN" \
  http://staging.api.yourcompany.com/api/v1/invoices/INV-001/lines?page=1&page_size=100

# Expected results:
# - Requests per second: > 100
# - Mean response time: < 200ms
# - Error rate: < 0.1%
```

**2. Database Load Test:**
```bash
# Monitor connection pool usage
watch -n 1 'psql -U postgres -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"'

# Expected: Connection usage < 60% of pool
```

### Production Deployment (Day 1+)

**Step 1: Pre-Deployment Checklist:**
- [ ] Code review completed
- [ ] Security review approved
- [ ] Load testing passed
- [ ] SSL certificate valid
- [ ] Database backups current
- [ ] Rollback plan documented
- [ ] Monitoring configured

**Step 2: Deploy to First Instance:**
```bash
# On production server 1
cd /opt/invoice-api
git pull origin main
git checkout v1.0.0

source venv/bin/activate
pip install -r requirements.txt

# Start application
systemctl restart invoice-api
```

**Step 3: Health Check:**
```bash
# Verify application is running
curl -I https://api.yourcompany.com/docs

# Expected: HTTP 200
```

**Step 4: Monitor for Issues:**
```bash
# Watch logs in real-time
tail -f /var/log/invoice-api/application.log

# Monitor metrics
watch -n 5 'curl https://api.yourcompany.com/health'

# Expected: No errors for 30 minutes
```

**Step 5: Deploy to Additional Instances:**
```bash
# Repeat steps 2-4 for second instance
# Then configure load balancer to distribute traffic
```

---

## Verification & Testing

### 1. Endpoint Testing

```bash
# Test without authentication (should fail)
curl -X GET https://api.yourcompany.com/api/v1/invoices/INV-001/lines
# Expected: 401 Unauthorized

# Test with valid token
curl -X GET https://api.yourcompany.com/api/v1/invoices/INV-001/lines \
  -H "Authorization: Bearer VALID_JWT_TOKEN"
# Expected: 200 OK with invoice lines

# Test pagination
curl -X GET https://api.yourcompany.com/api/v1/invoices/INV-001/lines?page=1&page_size=100 \
  -H "Authorization: Bearer VALID_JWT_TOKEN"
# Expected: JSON response with pagination metadata

# Test invalid pagination
curl -X GET https://api.yourcompany.com/api/v1/invoices/INV-001/lines?page=0 \
  -H "Authorization: Bearer VALID_JWT_TOKEN"
# Expected: 400 Bad Request
```

### 2. Performance Testing

```bash
# Response time for single request
time curl -X GET https://api.yourcompany.com/api/v1/invoices/INV-001/lines?page_size=1000 \
  -H "Authorization: Bearer VALID_JWT_TOKEN" \
  -o /dev/null -s -w "%{time_total}\n"
# Expected: < 100ms

# Throughput test (100 concurrent requests)
ab -n 100 -c 100 -H "Authorization: Bearer VALID_JWT_TOKEN" \
  https://api.yourcompany.com/api/v1/invoices/INV-001/lines
# Expected: > 100 requests/second, < 1% error rate
```

### 3. Database Connection Test

```bash
# Verify database is reachable
psql -h db.yourcompany.com -U api_user -d invoice_lines_api -c "SELECT COUNT(*) FROM invoices;"

# Check connection pool
psql -U postgres -c "SELECT datname, count(*) as connections FROM pg_stat_activity GROUP BY datname;"
```

---

## Monitoring & Alerts

### 1. Application Monitoring

**Key Metrics:**
```
- API response time (p50, p95, p99)
- Request volume (requests/second)
- Error rate (4xx, 5xx)
- Database query latency
- Connection pool utilization
```

**Monitor Setup:**
```bash
# Using standard system tools
# Option 1: Custom logging
tail -f /var/log/invoice-api/access.log | grep "response_time"

# Option 2: Prometheus (if available)
curl http://localhost:9090/api/v1/query?query=api_request_duration_seconds

# Option 3: ELK Stack (if available)
# Query recent logs in Kibana dashboard
```

### 2. Alert Configuration

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| p95 latency | > 150ms | > 200ms | Investigate / Scale |
| Error rate | > 0.5% | > 1% | Investigate immediately |
| Connection pool | > 70% | > 90% | Scale up database |
| Disk space | > 80% | > 90% | Expand storage |
| CPU usage | > 70% | > 85% | Scale up instances |

### 3. Health Check Endpoint

```bash
# Check application health
curl https://api.yourcompany.com/health
# Returns: {"status": "healthy", "version": "1.0.0"}
```

---

## Troubleshooting

### Issue 1: Database Connection Refused

**Symptoms:**
```
Error: could not connect to server: Connection refused
```

**Diagnosis:**
```bash
# Check if PostgreSQL is running
systemctl status postgresql

# Verify connection string
echo "postgresql://api_user:password@localhost:5432/invoice_lines_api"

# Test connection manually
psql -h localhost -U api_user -d invoice_lines_api -c "SELECT 1"
```

**Solution:**
```bash
# Start PostgreSQL if stopped
sudo systemctl start postgresql

# Verify firewall allows access
sudo ufw allow 5432/tcp

# Check database exists
psql -U postgres -c "\l"
```

### Issue 2: 401 Unauthorized Errors

**Symptoms:**
```
{"detail": "Not authenticated"}
```

**Diagnosis:**
```bash
# Verify JWT token is included
curl -v https://api.yourcompany.com/api/v1/invoices/INV-001/lines

# Check token validity
python -c "import jwt; jwt.decode('TOKEN', 'SECRET_KEY', algorithms=['HS256'])"
```

**Solution:**
```bash
# Generate new token from identity provider
# Verify JWT_SECRET_KEY in environment matches signing key
# Check token expiration hasn't passed
```

### Issue 3: Connection Pool Exhaustion

**Symptoms:**
```
QueuePool limit exceeded
ERROR: current transaction is aborted
```

**Diagnosis:**
```bash
# Check connection count
psql -U postgres -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Monitor pool usage
tail -f /var/log/invoice-api/application.log | grep "pool"
```

**Solution:**
```bash
# Increase pool_size in database.py
# pool_size=20 (was 10)

# Restart application
systemctl restart invoice-api

# Monitor improvement
watch -n 2 "psql -U postgres -c 'SELECT count(*) FROM pg_stat_activity;'"
```

### Issue 4: Slow Response Times

**Symptoms:**
```
Response time > 500ms
```

**Diagnosis:**
```bash
# Check database query time
EXPLAIN ANALYZE SELECT * FROM invoice_lines WHERE invoice_id = 'INV-001' ORDER BY line_order LIMIT 100;

# Check database indices
\d invoice_lines  -- in psql

# Check connection pool saturation
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
```

**Solution:**
```bash
# Verify indices are created
CREATE INDEX IF NOT EXISTS idx_invoice_lines ON invoice_lines(invoice_id, line_order);

# Vacuum database
VACUUM ANALYZE;

# Scale to multiple instances if needed
```

---

## Rollback Procedures

### Automatic Rollback (Health Check Failed)

```bash
# If 5xx errors exceed threshold, automatically roll back
if [ "$(curl -s -o /dev/null -w '%{http_code}' https://api.yourcompany.com/api/v1/invoices/TEST/lines)" != "401" ]; then
  echo "Health check failed, rolling back..."
  git checkout v1.0.0  # Previous version
  pip install -r requirements.txt
  systemctl restart invoice-api
fi
```

### Manual Rollback (< 5 minutes)

**Step 1: Stop New Version**
```bash
# Stop current (broken) deployment
systemctl stop invoice-api

# Route traffic to previous version
# (update load balancer configuration)
```

**Step 2: Restore Previous Version**
```bash
cd /opt/invoice-api
git checkout v0.9.0  # Previous working version
source venv/bin/activate
pip install -r requirements.txt
```

**Step 3: Start Previous Version**
```bash
systemctl start invoice-api

# Verify health
curl https://api.yourcompany.com/health
```

**Step 4: Investigate Root Cause**
```bash
# Save logs for analysis
cp /var/log/invoice-api/application.log /var/log/invoice-api/app.log.broken

# Review git diff
git diff v0.9.0 v1.0.0

# Determine what went wrong
```

---

## Maintenance

### Regular Tasks

**Daily:**
- [ ] Monitor error rates (< 0.1% expected)
- [ ] Check disk space (> 20% free)
- [ ] Verify backup completion

**Weekly:**
- [ ] Review performance metrics
- [ ] Update security patches
- [ ] Test failover procedures

**Monthly:**
- [ ] Performance optimization review
- [ ] Database maintenance (VACUUM, ANALYZE)
- [ ] Capacity planning

**Quarterly:**
- [ ] Security audit
- [ ] Load testing
- [ ] Documentation updates

---

## Support & Contact

For deployment issues:
- 📧 Email: devops@yourcompany.com
- 📞 Phone: +1-XXX-XXX-XXXX (24/7)
- 🆘 Escalation: On-call engineer (via PagerDuty)

---

*Deployment Guide v1.0.0*  
*Last Updated: April 8, 2026*  
*Status: Production Ready*
