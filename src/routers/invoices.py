"""
API endpoint for invoice operations

REQ001-REQ008: FastAPI endpoint implementation
Technisch ontwerp: API Layer (PIVD-8320)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.services.invoice_service import InvoiceService
from src.schemas.invoice import InvoiceLinesResponse
from src.exceptions import (
    InvoiceNotFoundException,
    InvalidPaginationException,
)
from src.security import get_current_contact_person
from src.database import get_db

router = APIRouter(
    prefix="/api/v1/invoices",
    tags=["invoices"],
)


@router.get(
    "/{invoice_id}/lines",
    response_model=InvoiceLinesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get invoice lines",
    description="Retrieve all invoice lines for a specific invoice of a contact person",
)
async def get_invoice_lines(
    invoice_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(100, ge=1, le=10000, description="Records per page"),
    contact_person_id: str = Depends(get_current_contact_person),
    db: Session = Depends(get_db),
):
    """
    Get invoice lines for a specific invoice

    REQ001: Retrieve all invoice lines for specific invoice
    REQ002: Return complete invoice line data structure
    REQ003: Only allow access to own invoices
    REQ004: Return lines in correct order
    REQ005: Return 404 if invoice not found/accessible
    REQ006: Require authentication (JWT token)
    REQ007: Support pagination
    REQ008: Optimized for performance

    Parameters:
    - invoice_id: Invoice ID (path parameter)
    - page: Page number, default 1
    - page_size: Records per page, default 100, max 10000
    - Authorization: Bearer <JWT token> (in header)

    Returns:
    - 200: InvoiceLinesResponse with paginated invoice lines
    - 400: Invalid pagination parameters
    - 401: Missing or invalid authentication
    - 404: Invoice not found or not accessible
    - 500: Internal server error

    Example:
    ```
    GET /api/v1/invoices/INV-2026-001234/lines?page=1&page_size=100
    Authorization: Bearer <jwt_token>
    ```
    """
    try:
        # Create service instance
        service = InvoiceService(db)

        # Call business logic
        result = service.get_invoice_lines(
            invoice_id=invoice_id,
            contact_person_id=contact_person_id,
            page=page,
            page_size=page_size,
        )

        return result

    except InvoiceNotFoundException as e:
        # REQ005: Return 404 for not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )

    except InvalidPaginationException as e:
        # REQ007: Return 400 for invalid pagination
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail,
        )

    except Exception as e:
        # Generic error handling
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
