"""
Integration Tests - Invoice API Endpoints
Tests REQ001-REQ008 at API level

Tests the complete request/response cycle including:
- HTTP status codes (REQ005, REQ006)
- JSON schema validation (REQ002)
- Authorization checks (REQ003, REQ006)
- Pagination (REQ007)
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from src.main import app
from src.schemas.invoice import InvoiceLineResponse, InvoiceLinesResponse


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def valid_jwt_token():
    """Mock JWT token for authenticated requests"""
    return "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."


@pytest.fixture
def invalid_jwt_token():
    """Invalid JWT token"""
    return "Bearer invalid_token_xyz"


class TestInvoiceLineEndpoint:
    """Test GET /api/v1/invoices/{invoice_id}/lines"""

    # ========================================
    # REQ001: Happy Path - Successful Retrieval
    # ========================================

    def test_get_invoice_lines_success_200(self, client, valid_jwt_token):
        """
        REQ001 [POSITIVE]: Endpoint should return 200 with invoice lines

        Given: Valid invoice_id, valid JWT token, page=1
        When: GET /invoices/{invoice_id}/lines
        Then: Should return 200 OK with InvoiceLinesResponse
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "invoice_lines" in data
        assert "total_records" in data
        assert "page" in data
        assert "page_size" in data

    def test_get_invoice_lines_empty_response_200(self, client, valid_jwt_token):
        """
        REQ001 [POSITIVE]: Endpoint should return 200 even with empty lines

        Given: Valid invoice_id with no lines
        When: GET /invoices/{invoice_id}/lines
        Then: Should return 200 OK with empty invoice_lines array
        """
        # Arrange
        invoice_id = "INV-2026-001234"  # Invoice with 0 lines
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["invoice_lines"] == []
        assert data["total_records"] == 0

    # ========================================
    # REQ002: Response Schema Validation
    # ========================================

    def test_get_invoice_lines_response_schema_valid(self, client, valid_jwt_token):
        """
        REQ002 [POSITIVE]: Response should match InvoiceLinesResponse schema

        Given: Valid invoice request
        When: GET /invoices/{invoice_id}/lines
        Then: Response JSON should match schema exactly
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Validate required response fields
        required_fields = [
            "invoice_id",
            "contact_person_id",
            "total_records",
            "page",
            "page_size",
            "total_pages",
            "invoice_lines",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_get_invoice_line_item_schema_valid(self, client, valid_jwt_token):
        """
        REQ002 [POSITIVE]: Each invoice line must have all required fields

        Given: Invoice with lines
        When: GET /invoices/{invoice_id}/lines
        Then: Each line item should contain all required fields
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        if len(data["invoice_lines"]) > 0:
            line = data["invoice_lines"][0]

            required_line_fields = [
                "line_id",
                "article_code",
                "description",
                "quantity",
                "unit_price",
                "tax_percentage",
                "total_price",
                "line_order",
            ]
            for field in required_line_fields:
                assert field in line, f"Missing required line field: {field}"
                assert line[field] is not None

    # ========================================
    # REQ005: Not Found Error (404)
    # ========================================

    def test_get_invoice_lines_not_found_404(self, client, valid_jwt_token):
        """
        REQ005 [NEGATIVE]: Should return 404 for non-existent invoice

        Given: Non-existent invoice_id
        When: GET /invoices/{invoice_id}/lines
        Then: Should return 404 Not Found
        """
        # Arrange
        invoice_id = "INV-NONEXISTENT"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_invoice_lines_unauthorized_invoice_403(self, client, valid_jwt_token):
        """
        REQ003 & REQ005 [NEGATIVE]: Should return 403/404 for invoice not owned by contact person

        Given: Invoice belongs to different contact person
        When: GET /invoices/{invoice_id}/lines
        Then: Should return 403 Forbidden or 404 Not Found (privacy-safe)
        """
        # Arrange
        invoice_id = "INV-ANOTHER-CONTACT"  # Belongs to different contact person
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100",
            headers=headers,
        )

        # Assert
        # Should be 403 or 404 (both are acceptable for privacy)
        assert response.status_code in [403, 404]
        data = response.json()
        assert "detail" in data

    # ========================================
    # REQ006: Authentication Required (401)
    # ========================================

    def test_get_invoice_lines_no_auth_401(self, client):
        """
        REQ006 [NEGATIVE]: Should return 401 if no authentication provided

        Given: No Authorization header
        When: GET /invoices/{invoice_id}/lines
        Then: Should return 401 Unauthorized
        """
        # Arrange
        invoice_id = "INV-2026-001234"

        # Act
        response = client.get(f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_invoice_lines_invalid_token_401(self, client, invalid_jwt_token):
        """
        REQ006 [NEGATIVE]: Should return 401 for invalid JWT token

        Given: Invalid JWT token
        When: GET /invoices/{invoice_id}/lines
        Then: Should return 401 Unauthorized
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": invalid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100",
            headers=headers,
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_invoice_lines_malformed_token_401(self, client):
        """
        REQ006 [NEGATIVE]: Should return 401 for malformed Authorization header

        Given: Malformed Authorization header
        When: GET /invoices/{invoice_id}/lines
        Then: Should return 401 Unauthorized
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": "InvalidBearerFormat"}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100",
            headers=headers,
        )

        # Assert
        assert response.status_code == 401

    # ========================================
    # REQ004: Line Ordering Verification
    # ========================================

    def test_get_invoice_lines_ordering_correct(self, client, valid_jwt_token):
        """
        REQ004 [POSITIVE]: Invoice lines should be ordered by line_order

        Given: Invoice with multiple lines
        When: GET /invoices/{invoice_id}/lines
        Then: Lines should be sorted by line_order ascending
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=100",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        lines = data["invoice_lines"]

        if len(lines) > 1:
            orders = [line["line_order"] for line in lines]
            assert orders == sorted(orders), "Lines not sorted by line_order"

    # ========================================
    # REQ007: Pagination
    # ========================================

    def test_get_invoice_lines_pagination_page_1(self, client, valid_jwt_token):
        """
        REQ007 [POSITIVE]: Pagination should return correct page

        Given: page=1, page_size=50
        When: GET /invoices/{invoice_id}/lines?page=1&page_size=50
        Then: Should return first 50 records
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=50",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 50
        assert len(data["invoice_lines"]) <= 50

    def test_get_invoice_lines_pagination_page_2(self, client, valid_jwt_token):
        """
        REQ007 [POSITIVE]: Pagination should work for page 2

        Given: page=2, page_size=50
        When: GET /invoices/{invoice_id}/lines?page=2&page_size=50
        Then: Should return records 51-100
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=2&page_size=50",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 50

    def test_get_invoice_lines_pagination_default_values(self, client, valid_jwt_token):
        """
        REQ007 [POSITIVE]: Pagination should use defaults if not specified

        Given: No pagination parameters
        When: GET /invoices/{invoice_id}/lines
        Then: Should use default page=1, page_size=100
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(f"/api/v1/invoices/{invoice_id}/lines", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 100

    def test_get_invoice_lines_pagination_max_page_size(self, client, valid_jwt_token):
        """
        REQ007 [NEGATIVE]: page_size should be capped at 10,000

        Given: page_size=20000
        When: GET /invoices/{invoice_id}/lines?page_size=20000
        Then: Should cap page_size to 10,000
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page_size=20000",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] <= 10000

    def test_get_invoice_lines_pagination_invalid_page_zero(self, client, valid_jwt_token):
        """
        REQ007 [NEGATIVE]: page must be >= 1

        Given: page=0
        When: GET /invoices/{invoice_id}/lines?page=0
        Then: Should return 400 Bad Request
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=0&page_size=100",
            headers=headers,
        )

        # Assert
        assert response.status_code == 400

    def test_get_invoice_lines_pagination_invalid_page_size_zero(self, client, valid_jwt_token):
        """
        REQ007 [NEGATIVE]: page_size must be >= 1

        Given: page_size=0
        When: GET /invoices/{invoice_id}/lines?page_size=0
        Then: Should return 400 Bad Request
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        headers = {"Authorization": valid_jwt_token}

        # Act
        response = client.get(
            f"/api/v1/invoices/{invoice_id}/lines?page=1&page_size=0",
            headers=headers,
        )

        # Assert
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
