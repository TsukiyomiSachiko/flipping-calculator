from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.utils.database import get_db, execute_query, executemany_query
from app.utils.dependencies import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class AccountResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

@router.get("", response_model=List[AccountResponse])
async def get_accounts(current_user: dict = Depends(get_current_user)):
    """List all accounts (Authenticated)"""
    with get_db() as session:
        _res = execute_query(session, "SELECT id, name, created_at FROM accounts ORDER BY name ASC")
        return [dict(row) for row in _res.mappings().fetchall()]

@router.delete("/{account_id}")
async def delete_account(account_id: int, current_user: dict = Depends(get_current_user)):
    """Delete an account (Authenticated)"""
    with get_db() as session:
        _res = execute_query(session, "DELETE FROM accounts WHERE id = ?", (account_id,))
        if _res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        session.commit()
        return {"message": "Account deleted"}
