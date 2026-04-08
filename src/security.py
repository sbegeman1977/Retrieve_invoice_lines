"""
Security and authentication utilities

REQ006: JWT token validation and authentication
REQ003: Authorization checks
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt
from typing import Optional
import os

# Security scheme for FastAPI
security = HTTPBearer()

# JWT configuration
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")


async def get_current_contact_person(
    credentials: HTTPAuthCredentials = Depends(security),
) -> str:
    """
    Extract and validate JWT token, return contact person ID

    REQ006: Authentication required
    Returns: contact_person_id from token

    Raises: AuthenticationException (401) if token invalid
    """
    token = credentials.credentials

    try:
        # In production, use proper JWT validation
        # This is a simplified example
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        contact_person_id: str = payload.get("sub")

        if contact_person_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return contact_person_id

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )
