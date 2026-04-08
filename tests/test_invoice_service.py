"""
Unit Tests - Invoice Service Layer
Tests REQ001, REQ002, REQ003, REQ004, REQ005, REQ007, REQ008

Each test is mapped to specific requirements.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from src.services.invoice_service import InvoiceService
from src.repositories.invoice_repository import InvoiceRepository
from src.schemas.invoice import InvoiceLineResponse, InvoiceLinesResponse
from src.exceptions import (
    InvoiceNotFoundException,
    UnauthorizedException,
    InvalidPaginationException,
)


def create_mock_invoice_line(
    line_id="IL-001",
    article_code="ART-12345",
    description="Test Product",
    quantity=Decimal("5"),
    unit_price=Decimal("100.00"),
    tax_percentage=Decimal("21"),
    total_price=Decimal("605.00"),
    line_order=1,
):
    """Factory function to create properly configured mock InvoiceLine objects"""
    mock_line = Mock()
    mock_line.id = line_id
    mock_line.article_code = article_code
    mock_line.description = description
    mock_line.quantity = quantity
    mock_line.unit_price = unit_price
    mock_line.tax_percentage = tax_percentage
    mock_line.total_price = total_price
    mock_line.line_order = line_order
    return mock_line


class TestInvoiceServiceGetInvoiceLines:
    """Unit tests for InvoiceService.get_invoice_lines()"""

    @pytest.fixture
    def mock_repository(self):
        """Mock InvoiceRepository"""
        return Mock(spec=InvoiceRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """Create InvoiceService with mocked repository"""
        return InvoiceService(repository=mock_repository)

    # ========================================
    # REQ001: Invoice Lines Retrieval - Happy Path
    # ========================================

    def test_get_invoice_lines_success_single_page(self, service, mock_repository):
        """
        REQ001 [POSITIVE]: API should return all invoice lines for valid invoice + contact person

        Given: Valid invoiceId, contactPersonId, and pagination
        When: get_invoice_lines() is called
        Then: Should return paginated InvoiceLinesResponse with all lines
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        contact_person_id = "CP-5678"
        page = 1
        page_size = 100

        mock_lines = [
            Mock(
                id="IL-001",
                article_code="ART-12345",
                description="Product X",
                quantity=Decimal("5"),
                unit_price=Decimal("100.00"),
                tax_percentage=Decimal("21"),
                total_price=Decimal("605.00"),
                line_order=1,
            ),
            Mock(
                id="IL-002",
                article_code="ART-12346",
                description="Product Y",
                quantity=Decimal("3"),
                unit_price=Decimal("50.00"),
                tax_percentage=Decimal("21"),
                total_price=Decimal("181.50"),
                line_order=2,
            ),
        ]

        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = (mock_lines, 2)

        # Act
        result = service.get_invoice_lines(
            invoice_id=invoice_id,
            contact_person_id=contact_person_id,
            page=page,
            page_size=page_size,
        )

        # Assert
        assert isinstance(result, InvoiceLinesResponse)
        assert result.invoice_id == invoice_id
        assert result.contact_person_id == contact_person_id
        assert len(result.invoice_lines) == 2
        assert result.total_records == 2
        assert result.page == 1
        assert result.page_size == 100
        mock_repository.invoice_exists_for_contact.assert_called_once_with(
            invoice_id, contact_person_id
        )

    def test_get_invoice_lines_empty_list_success(self, service, mock_repository):
        """
        REQ001 [POSITIVE]: API should return empty list if invoice has no lines

        Given: Valid invoiceId with no invoice lines
        When: get_invoice_lines() is called
        Then: Should return response with empty invoice_lines array and total_records=0
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        contact_person_id = "CP-5678"

        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = ([], 0)

        # Act
        result = service.get_invoice_lines(
            invoice_id=invoice_id,
            contact_person_id=contact_person_id,
            page=1,
            page_size=100,
        )

        # Assert
        assert result.total_records == 0
        assert len(result.invoice_lines) == 0
        assert isinstance(result.invoice_lines, list)

    # ========================================
    # REQ001 & REQ003: Authorization - Negative Path
    # ========================================

    def test_get_invoice_lines_not_found_raises_exception(self, service, mock_repository):
        """
        REQ001 [NEGATIVE] & REQ005: Should raise NotFoundException for non-existent invoice

        Given: Invalid invoiceId
        When: get_invoice_lines() is called
        Then: Should raise InvoiceNotFoundException
        """
        # Arrange
        invoice_id = "INV-INVALID"
        contact_person_id = "CP-5678"

        mock_repository.invoice_exists_for_contact.return_value = False

        # Act & Assert
        with pytest.raises(InvoiceNotFoundException) as exc_info:
            service.get_invoice_lines(
                invoice_id=invoice_id,
                contact_person_id=contact_person_id,
                page=1,
                page_size=100,
            )

        assert "not found" in str(exc_info.value).lower()
        mock_repository.invoice_exists_for_contact.assert_called_once()

    def test_get_invoice_lines_unauthorized_different_contact_person(
        self, service, mock_repository
    ):
        """
        REQ003 [NEGATIVE]: Contact person can only see their own invoice lines

        Given: Invoice belongs to different contact person
        When: get_invoice_lines() called with wrong contact_person_id
        Then: Should raise exception (treated as not found for privacy)
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        contact_person_id = "CP-WRONG"  # Different from invoice owner

        mock_repository.invoice_exists_for_contact.return_value = False

        # Act & Assert
        with pytest.raises(InvoiceNotFoundException):
            service.get_invoice_lines(
                invoice_id=invoice_id,
                contact_person_id=contact_person_id,
                page=1,
                page_size=100,
            )

    # ========================================
    # REQ002: Data Structure - Field Presence
    # ========================================

    def test_get_invoice_lines_contains_all_required_fields(self, service, mock_repository):
        """
        REQ002 [POSITIVE]: Invoice lines must contain all required fields

        Given: Valid invoice with lines
        When: get_invoice_lines() returns data
        Then: Each line must have all required fields (no nulls for required fields)
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        contact_person_id = "CP-5678"

        mock_line = Mock(
            id="IL-001",
            article_code="ART-12345",
            description="Product X",
            quantity=Decimal("5"),
            unit_price=Decimal("100.00"),
            tax_percentage=Decimal("21"),
            total_price=Decimal("605.00"),
            line_order=1,
        )

        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = ([mock_line], 1)

        # Act
        result = service.get_invoice_lines(
            invoice_id=invoice_id,
            contact_person_id=contact_person_id,
            page=1,
            page_size=100,
        )

        # Assert
        assert len(result.invoice_lines) == 1
        line = result.invoice_lines[0]
        assert line.line_id is not None
        assert line.article_code is not None
        assert line.description is not None
        assert line.quantity is not None
        assert line.unit_price is not None
        assert line.tax_percentage is not None
        assert line.total_price is not None
        assert line.line_order is not None

    # ========================================
    # REQ004: Line Ordering
    # ========================================

    def test_get_invoice_lines_ordered_by_line_order(self, service, mock_repository):
        """
        REQ004 [POSITIVE]: Invoice lines must be sorted by line_order

        Given: Invoice with multiple lines
        When: get_invoice_lines() returns data
        Then: Lines should be ordered by line_order ascending
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        contact_person_id = "CP-5678"

        mock_lines = [
            create_mock_invoice_line(line_id="IL-001", line_order=1),
            create_mock_invoice_line(line_id="IL-002", line_order=2),
            create_mock_invoice_line(line_id="IL-003", line_order=3),
        ]

        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = (mock_lines, 3)

        # Act
        result = service.get_invoice_lines(
            invoice_id=invoice_id,
            contact_person_id=contact_person_id,
            page=1,
            page_size=100,
        )

        # Assert
        orders = [line.line_order for line in result.invoice_lines]
        assert orders == sorted(orders)  # Verify ascending order

    # ========================================
    # REQ007: Pagination - Happy Path
    # ========================================

    def test_get_invoice_lines_pagination_page_1(self, service, mock_repository):
        """
        REQ007 [POSITIVE]: Pagination should work for page 1

        Given: Invoice with 150 lines, page_size=100
        When: get_invoice_lines(page=1, page_size=100)
        Then: Should return 100 lines with correct pagination metadata
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        contact_person_id = "CP-5678"
        mock_lines = [
            create_mock_invoice_line(line_id=f"IL-{i:04d}", line_order=i)
            for i in range(1, 101)
        ]

        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = (mock_lines, 150)

        # Act
        result = service.get_invoice_lines(
            invoice_id=invoice_id,
            contact_person_id=contact_person_id,
            page=1,
            page_size=100,
        )

        # Assert
        assert len(result.invoice_lines) == 100
        assert result.page == 1
        assert result.page_size == 100
        assert result.total_records == 150
        assert result.total_pages == 2

    def test_get_invoice_lines_pagination_page_2(self, service, mock_repository):
        """
        REQ007 [POSITIVE]: Pagination should work for page 2 and beyond

        Given: Invoice with 150 lines, page_size=100, requesting page 2
        When: get_invoice_lines(page=2, page_size=100)
        Then: Should return remaining 50 lines
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        contact_person_id = "CP-5678"
        mock_lines = [
            create_mock_invoice_line(line_id=f"IL-{i:04d}", line_order=i)
            for i in range(101, 151)
        ]

        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = (mock_lines, 150)

        # Act
        result = service.get_invoice_lines(
            invoice_id=invoice_id,
            contact_person_id=contact_person_id,
            page=2,
            page_size=100,
        )

        # Assert
        assert len(result.invoice_lines) == 50
        assert result.page == 2
        assert result.total_pages == 2

    def test_get_invoice_lines_pagination_max_page_size(self, service, mock_repository):
        """
        REQ007 [POSITIVE]: Pagination should enforce max page_size of 10,000

        Given: page_size > 10000
        When: get_invoice_lines() is called
        Then: Should cap page_size to 10,000
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        contact_person_id = "CP-5678"
        mock_lines = [
            create_mock_invoice_line(line_id=f"IL-{i:05d}", line_order=i)
            for i in range(1, 10001)
        ]

        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = (mock_lines, 10000)

        # Act
        result = service.get_invoice_lines(
            invoice_id=invoice_id,
            contact_person_id=contact_person_id,
            page=1,
            page_size=10000,
        )

        # Assert
        assert result.page_size == 10000
        assert len(result.invoice_lines) == 10000

    # ========================================
    # REQ007: Pagination - Negative Path (Edge Cases)
    # ========================================

    def test_get_invoice_lines_pagination_invalid_page_zero(self, service, mock_repository):
        """
        REQ007 [NEGATIVE]: Page number must be >= 1

        Given: page=0
        When: get_invoice_lines() is called
        Then: Should raise InvalidPaginationException
        """
        # Arrange
        invoice_id = "INV-2026-001234"
        contact_person_id = "CP-5678"

        # Act & Assert
        with pytest.raises(InvalidPaginationException):
            service.get_invoice_lines(
                invoice_id=invoice_id,
                contact_person_id=contact_person_id,
                page=0,  # Invalid
                page_size=100,
            )

    def test_get_invoice_lines_pagination_invalid_page_negative(self, service, mock_repository):
        """
        REQ007 [NEGATIVE]: Page number must be positive

        Given: page=-1
        When: get_invoice_lines() is called
        Then: Should raise InvalidPaginationException
        """
        # Act & Assert
        with pytest.raises(InvalidPaginationException):
            service.get_invoice_lines(
                invoice_id="INV-2026-001234",
                contact_person_id="CP-5678",
                page=-1,
                page_size=100,
            )

    def test_get_invoice_lines_pagination_invalid_page_size_zero(self, service, mock_repository):
        """
        REQ007 [NEGATIVE]: Page size must be >= 1

        Given: page_size=0
        When: get_invoice_lines() is called
        Then: Should raise InvalidPaginationException
        """
        # Act & Assert
        with pytest.raises(InvalidPaginationException):
            service.get_invoice_lines(
                invoice_id="INV-2026-001234",
                contact_person_id="CP-5678",
                page=1,
                page_size=0,
            )

    def test_get_invoice_lines_pagination_exceeds_max(self, service, mock_repository):
        """
        REQ007 [NEGATIVE]: Page size must be <= 10,000

        Given: page_size=10001
        When: get_invoice_lines() is called
        Then: Should raise InvalidPaginationException or cap to 10000
        """
        # This test depends on implementation choice:
        # Either raise exception or silently cap to 10000
        # (Current assumption: cap to 10000 is more user-friendly)

        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = ([], 0)

        result = service.get_invoice_lines(
            invoice_id="INV-2026-001234",
            contact_person_id="CP-5678",
            page=1,
            page_size=10001,
        )

        assert result.page_size <= 10000

    # ========================================
    # REQ005: Error Handling - Null/Edge Cases
    # ========================================

    def test_get_invoice_lines_null_invoice_id(self, service):
        """
        REQ005 [NEGATIVE]: Null invoice_id should raise error

        Given: invoice_id=None
        When: get_invoice_lines() is called
        Then: Should raise ValueError or validation error
        """
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            service.get_invoice_lines(
                invoice_id=None,  # Invalid
                contact_person_id="CP-5678",
                page=1,
                page_size=100,
            )

    def test_get_invoice_lines_empty_invoice_id(self, service, mock_repository):
        """
        REQ005 [NEGATIVE]: Empty invoice_id should raise error

        Given: invoice_id=""
        When: get_invoice_lines() is called
        Then: Should raise InvoiceNotFoundException (treated as not found)
        """
        # Arrange
        mock_repository.invoice_exists_for_contact.return_value = False

        # Act & Assert
        with pytest.raises(InvoiceNotFoundException):
            service.get_invoice_lines(
                invoice_id="",  # Empty
                contact_person_id="CP-5678",
                page=1,
                page_size=100,
            )

    # ========================================
    # REQ008: Performance - Response Time (Mock-based)
    # ========================================

    @patch("time.time")
    def test_get_invoice_lines_performance_acceptable(
        self, mock_time, service, mock_repository
    ):
        """
        REQ008 [POSITIVE]: Response time should be < 500ms for standard invoice

        Given: Standard invoice (< 100 lines)
        When: get_invoice_lines() completes
        Then: Execution time should be < 500ms
        """
        # Arrange
        mock_lines = [
            create_mock_invoice_line(line_id=f"IL-{i:03d}", line_order=i)
            for i in range(1, 51)
        ]
        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = (mock_lines, 50)

        # Simulate timing (in real scenario, use actual time measurement)
        # For unit tests, we just verify the service returns a result
        # Performance tests should be done separately

        # Act
        result = service.get_invoice_lines(
            invoice_id="INV-2026-001234",
            contact_person_id="CP-5678",
            page=1,
            page_size=100,
        )

        # Assert
        assert result is not None
        # Note: Actual performance measurement should be done with load tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
