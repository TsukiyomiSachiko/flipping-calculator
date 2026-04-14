from fastapi import Header, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional
from app.utils.database import get_db
from app.utils.security import SECRET_KEY, ALGORITHM

# Update tokenUrl to match the mount path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        account_id: int = payload.get("id")
        if username is None or account_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    return {"id": account_id, "name": username}

async def get_account_id(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the account ID of the authenticated user.
    Enforces authentication for all endpoints using this dependency.
    """
    return current_user["id"]
