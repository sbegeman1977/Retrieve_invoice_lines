"""
Data access layer for invoice queries

REQ001, REQ007: Retrieve invoice lines with pagination
REQ004: Order by line_order
Technisch ontwerp: Database queries
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Tuple, List

from src.models.invoice import Invoice, InvoiceLine


class InvoiceRepository:
    """
    Repository for invoice data access

    Handles all database queries for invoices and invoice lines
    """

    def __init__(self, db: Session):
        """Initialize repository with database session"""
        self.db = db

    def invoice_exists_for_contact(self, invoice_id: str, contact_person_id: str) -> bool:
        """
        Check if invoice exists and belongs to contact person

        REQ001, REQ003: Verify invoice ownership
        REQ005: Return False if not found or unauthorized

        Args:
            invoice_id: ID of invoice
            contact_person_id: ID of contact person

        Returns:
            True if invoice exists and belongs to contact, False otherwise
        """
        try:
            result = self.db.query(Invoice).filter(
                and_(
                    Invoice.id == invoice_id,
                    Invoice.contact_person_id == contact_person_id,
                )
            ).first()

            return result is not None

        except Exception as e:
            # Log error and return False (treat as not found)
            return False

    def get_invoice_lines_paginated(
        self, invoice_id: str, offset: int, limit: int
    ) -> Tuple[List[InvoiceLine], int]:
        """
        Retrieve paginated invoice lines for an invoice

        REQ001: Get all lines for invoice
        REQ004: Order by line_order ascending
        REQ007: Support pagination with offset/limit
        REQ008: Optimized query for performance

        Args:
            invoice_id: ID of invoice
            offset: Number of records to skip (pagination offset)
            limit: Maximum number of records to return (page size)

        Returns:
            Tuple of:
            - List of InvoiceLine objects
            - Total count of all invoice lines for invoice

        Raises:
            Exception: Any database error is propagated
        """
        try:
            # Get total count
            total_count = self.db.query(InvoiceLine).filter(
                InvoiceLine.invoice_id == invoice_id
            ).count()

            # Get paginated lines ordered by line_order (REQ004)
            lines = (
                self.db.query(InvoiceLine)
                .filter(InvoiceLine.invoice_id == invoice_id)
                .order_by(InvoiceLine.line_order.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return lines, total_count

        except Exception as e:
            # Log and re-raise
            raise e

    def get_invoice_by_id(self, invoice_id: str) -> Invoice:
        """
        Retrieve invoice by ID

        Args:
            invoice_id: ID of invoice

        Returns:
            Invoice object or None if not found
        """
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
