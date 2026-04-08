"""
SQLAlchemy models for Invoice and InvoiceLine

REQ002: Data structure for invoice lines
Technisch ontwerp: Database schema
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Invoice(Base):
    """
    Invoice model

    REQ001: Represents a single invoice for a contact person
    """

    __tablename__ = "invoices"

    id = Column(String(50), primary_key=True, index=True)
    contact_person_id = Column(String(50), nullable=False, index=True)
    invoice_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)
    status = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    lines = relationship("InvoiceLine", back_populates="invoice", lazy="select")

    # Indexes for performance (REQ008)
    __table_args__ = (
        Index("idx_contact_invoice", "contact_person_id", "id"),
        Index("idx_invoice_id", "id"),
    )


class InvoiceLine(Base):
    """
    InvoiceLine model

    REQ001, REQ002: Individual line item of an invoice
    REQ004: Lines maintain order via line_order field
    """

    __tablename__ = "invoice_lines"

    id = Column(String(50), primary_key=True, index=True)
    invoice_id = Column(String(50), ForeignKey("invoices.id"), nullable=False, index=True)
    article_code = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    quantity = Column(Numeric(10, 4), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    tax_percentage = Column(Numeric(5, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    line_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")

    # Indexes for performance (REQ007, REQ008)
    __table_args__ = (
        Index("idx_invoice_lines", "invoice_id", "line_order"),
        Index("idx_invoice_id_only", "invoice_id"),
    )
