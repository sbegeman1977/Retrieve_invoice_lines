"""
Business logic layer for invoice operations

REQ001-REQ008: Business rules and authorization logic
Technisch ontwerp: Service layer
"""

from sqlalchemy.orm import Session
from typing import Optional
import math

from src.repositories.invoice_repository import InvoiceRepository
from src.schemas.invoice import InvoiceLinesResponse, InvoiceLineResponse
from src.exceptions import (
    InvoiceNotFoundException,
    UnauthorizedException,
    InvalidPaginationException,
)
from src.models.invoice import InvoiceLine


class InvoiceService:
    """
    Service for invoice operations

    Handles business logic, authorization, and pagination
    """

    def __init__(self, db: Session):
        """Initialize service with database session and repository"""
        self.repository = InvoiceRepository(db)
        self.db = db

    def get_invoice_lines(
        self,
        invoice_id: str,
        contact_person_id: str,
        page: int = 1,
        page_size: int = 100,
    ) -> InvoiceLinesResponse:
        """
        Retrieve paginated invoice lines for an invoice

        REQ001: Get all invoice lines for specific invoice
        REQ002: Return complete data structure
        REQ003: Authorize contact person
        REQ004: Order by line_order
        REQ005: Raise exception if not found
        REQ006: (Caller handles authentication)
        REQ007: Support pagination with validation
        REQ008: Optimized for performance

        Args:
            invoice_id: ID of invoice
            contact_person_id: ID of authenticated contact person
            page: Page number (default 1)
            page_size: Records per page (default 100, max 10000)

        Returns:
            InvoiceLinesResponse with paginated invoice lines

        Raises:
            InvoiceNotFoundException: If invoice not found or not accessible
            InvalidPaginationException: If pagination params invalid
        """
        # Validate pagination parameters (REQ007)
        if page < 1:
            raise InvalidPaginationException("Page must be >= 1")

        if page_size < 1:
            raise InvalidPaginationException("Page size must be >= 1")

        # Cap page_size to maximum (REQ007)
        if page_size > 10000:
            page_size = 10000

        # REQ003: Authorization check - verify invoice belongs to contact person
        if not self.repository.invoice_exists_for_contact(invoice_id, contact_person_id):
            # REQ005: Return 404 (privacy-safe, don't reveal if exists but unauthorized)
            raise InvoiceNotFoundException(
                "Invoice not found or not accessible"
            )

        # Calculate pagination offset
        offset = (page - 1) * page_size

        # REQ001, REQ007: Get paginated lines
        lines, total_count = self.repository.get_invoice_lines_paginated(
            invoice_id, offset, page_size
        )

        # Calculate total pages
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

        # REQ002: Map to response schema
        invoice_lines = [
            InvoiceLineResponse(
                id=line.id,
                article_code=line.article_code,
                description=line.description or "",
                quantity=line.quantity,
                unit_price=line.unit_price,
                tax_percentage=line.tax_percentage,
                total_price=line.total_price,
                line_order=line.line_order,
            )
            for line in lines
        ]

        # Return paginated response
        return InvoiceLinesResponse(
            invoice_id=invoice_id,
            contact_person_id=contact_person_id,
            total_records=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            invoice_lines=invoice_lines,
        )
