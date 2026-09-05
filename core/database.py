import sqlite3
from typing import List
from models.schemas import BankRecord, ReconciliationResult

def init_db(db_path: str):
    """Initializes the SQLite database and creates the ledger table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ledger (
            bank_transaction_id TEXT PRIMARY KEY,
            deposit_amount REAL,
            status TEXT,
            order_id TEXT,
            payment_id TEXT,
            match_type TEXT,
            confidence TEXT,
            reasoning TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_pending_records(db_path: str, bank_records: List[BankRecord]) -> int:
    """Loads all new bank deposits into the database with a PENDING state.
       ENTERPRISE: IDEMPOTENCY. If a webhook fires twice, it ignores duplicates.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    new_inserts = 0
    for record in bank_records:
        # 1. Idempotency Check: Does this transaction already exist?
        cursor.execute("SELECT status FROM ledger WHERE bank_transaction_id = ?", (record.transaction_id,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('''
                INSERT INTO ledger (bank_transaction_id, deposit_amount, status)
                VALUES (?, ?, 'PENDING')
            ''', (record.transaction_id, record.deposit_amount))
            new_inserts += 1
            
    conn.commit()
    conn.close()
    return new_inserts

def update_ledger_record(db_path: str, result: ReconciliationResult):
    """Updates a PENDING row using strict ACID transactions."""
    conn = sqlite3.connect(db_path)
    # ENTERPRISE: ACID TRANSACTION
    # We use SQLite's context manager so if the update fails, it rolls back automatically
    # preventing silent data corruption.
    try:
        with conn:
            cursor = conn.cursor()
            status = "RECONCILED" if result.is_math_valid else "EXCEPTION"
            
            cursor.execute('''
                UPDATE ledger 
                SET status = ?, 
                    order_id = ?, 
                    payment_id = ?, 
                    match_type = ?, 
                    confidence = ?, 
                    reasoning = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE bank_transaction_id = ? AND status = 'PENDING'
            ''', (
                status,
                result.order_id,
                result.payment_id,
                result.match_type,
                result.confidence.value,
                result.reasoning,
                result.bank_transaction_id
            ))
    except sqlite3.Error as e:
        print(f"ACID Transaction Failed, rolling back: {e}")
    finally:
        conn.close()
