"""
Custom exceptions for the invoice lines API

REQ005, REQ006: Custom exception classes for error handling
"""


class InvoiceAPIException(Exception):
    """Base exception for invoice API"""

    def __init__(self, detail: str, status_code: int = 500):
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.detail)


class InvoiceNotFoundException(InvoiceAPIException):
    """
    Raised when invoice is not found or not accessible

    REQ005: Invoice not found error handling
    """

    def __init__(self, detail: str = "Invoice not found or not accessible"):
        super().__init__(detail, status_code=404)


class UnauthorizedException(InvoiceAPIException):
    """
    Raised when contact person is not authorized to access invoice

    REQ003, REQ006: Authorization & authentication checks
    """

    def __init__(self, detail: str = "Not authorized"):
        super().__init__(detail, status_code=403)


class AuthenticationException(InvoiceAPIException):
    """
    Raised when authentication is invalid or missing

    REQ006: Authentication required
    """

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(detail, status_code=401)


class InvalidPaginationException(InvoiceAPIException):
    """
    Raised when pagination parameters are invalid

    REQ007: Pagination validation
    """

    def __init__(self, detail: str = "Invalid pagination parameters"):
        super().__init__(detail, status_code=400)
