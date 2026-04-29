from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.database import get_db, execute_query, executemany_query
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from pydantic import BaseModel

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str
    account_id: int
    name: str

class AccountRegister(BaseModel):
    name: str
    password: str

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_db() as session:
        _res = execute_query(session, "SELECT id, name, password_hash FROM accounts WHERE name = ?", (form_data.username,))
        user = _res.mappings().fetchone()
        
    if not user or not user["password_hash"] or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["name"], "id": user["id"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "account_id": user["id"], "name": user["name"]}

@router.post("/register", response_model=Token)
async def register(account: AccountRegister):
    hashed_password = get_password_hash(account.password)
    
    with get_db() as session:
        try:
            _res = execute_query(session,
                "INSERT INTO accounts (name, password_hash) VALUES (?, ?)", 
                (account.name, hashed_password)
            )
            account_id = _res.scalar()
            
            # If lastrowid is None (e.g. Postgres sometimes needs explicit RETURNING fetch), check cursor implementation
            # The CursorWrapper implementation handles RETURNING id, but let's be safe
            if not account_id:
                _res = execute_query(session, "SELECT id FROM accounts WHERE name = ?", (account.name,))
                account_id = _res.mappings().fetchone()['id']

            session.commit()
            
            # Initialize settings
            _res = execute_query(session, "INSERT INTO user_settings (account_id) VALUES (?)", (account_id,))
            session.commit()

        except Exception as e:
            if "UNIQUE" in str(e).upper():
                raise HTTPException(status_code=400, detail="Account with this name already exists")
            raise HTTPException(status_code=500, detail=str(e))
            
    # Auto-login after registration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": account.name, "id": account_id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "account_id": account_id, "name": account.name}
