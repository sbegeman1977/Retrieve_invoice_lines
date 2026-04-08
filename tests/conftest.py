"""
Test configuration and fixtures for PIVD-7043

Mocks database dependencies to allow unit tests to run without PostgreSQL.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal


# Patch create_engine BEFORE any imports of src modules
with patch('sqlalchemy.create_engine') as mock_create_engine:
    mock_engine = MagicMock()
    mock_session_factory = MagicMock()
    mock_session = MagicMock()

    mock_create_engine.return_value = mock_engine
    mock_session_factory.return_value = mock_session

    # Now imports of src.database will use the mocked engine
    import sqlalchemy.orm


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """
    Configure test environment.

    Sets DATABASE_URL to a valid format (won't actually connect due to mocking).
    Overrides FastAPI security dependencies for API tests.
    """
    os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost/test')
    os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key')
    os.environ.setdefault('JWT_ALGORITHM', 'HS256')
    yield


@pytest.fixture
def client_with_mocked_auth():
    """Test client with mocked authentication and database"""
    from fastapi.testclient import TestClient
    from src.main import app
    from src.security import get_current_contact_person
    from src.database import SessionLocal
    from src.repositories.invoice_repository import InvoiceRepository
    from src.services.invoice_service import InvoiceService

    # Mock security dependency
    def mock_get_current_contact_person():
        return "CP-5678"

    # Mock database session with invoice repository
    def mock_get_db():
        # Return a mock session
        mock_session = MagicMock()
        mock_repository = MagicMock(spec=InvoiceRepository)
        # Set up default returns
        mock_repository.invoice_exists_for_contact.return_value = True
        mock_repository.get_invoice_lines_paginated.return_value = ([], 0)
        yield mock_session

    # Override dependencies
    app.dependency_overrides[get_current_contact_person] = mock_get_current_contact_person
    from src.database import get_db
    app.dependency_overrides[get_db] = mock_get_db

    yield TestClient(app)

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_repository():
    """Create a mock InvoiceRepository for unit tests"""
    from src.repositories.invoice_repository import InvoiceRepository
    return Mock(spec=InvoiceRepository)


@pytest.fixture
def mock_invoice_line():
    """Create a mock InvoiceLine ORM object"""
    mock_line = Mock()
    mock_line.id = "IL-001"
    mock_line.invoice_id = "INV-2026-001234"
    mock_line.article_code = "ART-12345"
    mock_line.description = "Test Product"
    mock_line.quantity = Decimal("5")
    mock_line.unit_price = Decimal("100.00")
    mock_line.tax_percentage = Decimal("21")
    mock_line.total_price = Decimal("605.00")
    mock_line.line_order = 1

    return mock_line
