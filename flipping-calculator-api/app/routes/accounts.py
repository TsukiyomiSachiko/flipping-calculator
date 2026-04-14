from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.utils.database import get_db
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
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM accounts ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]

@router.delete("/{account_id}")
async def delete_account(account_id: int, current_user: dict = Depends(get_current_user)):
    """Delete an account (Authenticated)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        conn.commit()
        return {"message": "Account deleted"}
