"""
Pydantic schemas for request/response validation

REQ002: Invoice line data structure
Technisch ontwerp: API response contracts
"""

from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal


class InvoiceLineResponse(BaseModel):
    """
    Single invoice line in response

    REQ002: Contains all required fields for invoice line
    """

    line_id: str = Field(..., alias="id", description="Unique line identifier")
    article_code: str = Field(..., description="Article/product code")
    description: str = Field(..., description="Line item description")
    quantity: Decimal = Field(..., description="Quantity ordered")
    unit_price: Decimal = Field(..., description="Price per unit")
    tax_percentage: Decimal = Field(..., description="Tax percentage")
    total_price: Decimal = Field(..., description="Total price including tax")
    line_order: int = Field(..., description="Order of line in invoice")

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}


class InvoiceLinesResponse(BaseModel):
    """
    Paginated invoice lines response

    REQ001: Complete response with pagination metadata
    REQ007: Pagination information
    """

    invoice_id: str = Field(..., description="Invoice ID")
    contact_person_id: str = Field(..., description="Contact person ID")
    total_records: int = Field(..., ge=0, description="Total number of records")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=10000, description="Records per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    invoice_lines: List[InvoiceLineResponse] = Field(
        default_factory=list, description="List of invoice lines"
    )

    class Config:
        json_encoders = {Decimal: float}


class PaginationParams(BaseModel):
    """
    Pagination parameters from query string

    REQ007: Pagination validation
    """

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=100, ge=1, le=10000, description="Records per page (max 10000)"
    )

    class Config:
        json_encoders = {Decimal: float}
