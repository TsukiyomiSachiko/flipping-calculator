"""
User Settings Service

Manages user preferences and state like available flipping cash
"""

from typing import Dict
from datetime import datetime, timezone
from app.utils.database import get_db


class SettingsService:
    
    @staticmethod
    def get_settings(account_id: int) -> Dict:
        """Get user settings for a specific account"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_settings WHERE account_id = ?', (account_id,))
            row = cursor.fetchone()
            
            if not row:
                # Initialize if missing
                cursor.execute('''
                    INSERT INTO user_settings (account_id, available_cash) 
                    VALUES (?, 0)
                ''', (account_id,))
                conn.commit()
                return {"account_id": account_id, "available_cash": 0, "last_updated": datetime.now(timezone.utc).isoformat()}
            
            return dict(row)
    
    @staticmethod
    def set_available_cash(account_id: int, amount: int) -> Dict:
        """
        Set available cash for flipping for a specific account
        
        Args:
            account_id: ID of the account
            amount: New cash amount in GP
        
        Returns:
            Updated settings
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_settings 
                SET available_cash = ?, last_updated = ?
                WHERE account_id = ?
            ''', (amount, datetime.now(timezone.utc), account_id))
            conn.commit()
        
        return SettingsService.get_settings(account_id)
    
    @staticmethod
    def adjust_cash(account_id: int, delta: int, reason: str = None) -> Dict:
        """
        Adjust available cash by a delta amount for a specific account
        
        Args:
            account_id: ID of the account
            delta: Amount to add (positive) or subtract (negative)
            reason: Optional reason for adjustment (for logging)
        
        Returns:
            Updated settings with new available_cash
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get current cash
            cursor.execute('SELECT available_cash FROM user_settings WHERE account_id = ?', (account_id,))
            row = cursor.fetchone()
            current = row['available_cash'] if row else 0
            
            new_amount = current + delta
            
            cursor.execute('''
                UPDATE user_settings 
                SET available_cash = ?, last_updated = ?
                WHERE account_id = ?
            ''', (new_amount, datetime.now(timezone.utc), account_id))
            
            conn.commit()
            
            return {
                "account_id": account_id,
                "available_cash": new_amount,
                "delta": delta,
                "reason": reason
            }
