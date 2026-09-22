from typing import Annotated
from datetime import datetime, timedelta, timezone
import secrets

from dotenv import dotenv_values
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from jose import JWTError, jwt




config = dotenv_values(".env")

AUTH_TYPE = config.get("AUTH_TYPE", "basic").lower()

EXPECTED_USERNAME = config.get("BASIC_AUTH_USERNAME")
EXPECTED_PASSWORD = config.get("BASIC_AUTH_PASSWORD")

JWT_SECRET_KEY = config.get("JWT_SECRET_KEY")
JWT_ALGORITHM = config.get("JWT_ALGORITHM", "HS256")

JWT_EXPIRE_MINUTES = int(
    config.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)




basic_security = HTTPBasic()


def get_username(
    credentials: Annotated[
        HTTPBasicCredentials,
        Depends(basic_security)
    ]
):
    if not EXPECTED_USERNAME or not EXPECTED_PASSWORD:
        raise RuntimeError(
            "BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD "
            "must be defined in .env"
        )

    username_correct = secrets.compare_digest(
        credentials.username,
        EXPECTED_USERNAME
    )

    password_correct = secrets.compare_digest(
        credentials.password,
        EXPECTED_PASSWORD
    )

    if not username_correct or not password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={
                "WWW-Authenticate": "Basic"
            },
        )

    return credentials.username


jwt_security = HTTPBearer()


def create_access_token(username: str) -> str:

    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY must be defined in .env"
        )

    expire = (
        datetime.now(timezone.utc)
        + timedelta(minutes=JWT_EXPIRE_MINUTES)
    )

    payload = {
        "sub": username,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(jwt_security)
    ]
):
    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY must be defined in .env"
        )

    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

        return username

    except JWTError:
        raise credentials_exception



if AUTH_TYPE == "basic":

    auth_dependency = get_username

elif AUTH_TYPE == "jwt":

    auth_dependency = get_current_user

else:

    raise RuntimeError(
        "AUTH_TYPE must be either 'basic' or 'jwt'"
    )

