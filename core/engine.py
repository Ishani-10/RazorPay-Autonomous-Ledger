import csv
import os
from typing import List

from models.schemas import OrderRecord, SettlementRecord, BankRecord, ReconciliationResult, MatchConfidence
from core.deterministic import match_deterministic
from core.llm_agent import resolve_with_ai
from core.verifier import verify_math
from core.database import init_db, insert_pending_records, update_ledger_record

def run_reconciliation(data_dir: str) -> List[ReconciliationResult]:
    """
    The Master Orchestrator.
    Pipes data through Layer 1 (Deterministic) -> Layer 2 (AI) -> Layer 3 (Guardrail) -> SQLite DB.
    """
    orders = []
    settlements = []
    bank_records = []

    # 1. Load the messy data
    if os.path.exists(os.path.join(data_dir, 'orders.csv')):
        with open(os.path.join(data_dir, 'orders.csv'), 'r') as f:
            for row in csv.DictReader(f):
                row['amount'] = float(row['amount'])
                orders.append(OrderRecord(**row))
                
    if os.path.exists(os.path.join(data_dir, 'settlements.csv')):
        with open(os.path.join(data_dir, 'settlements.csv'), 'r') as f:
            for row in csv.DictReader(f):
                row['gross_amount'] = float(row['gross_amount'])
                row['fee'] = float(row['fee'])
                row['settled_amount'] = float(row['settled_amount'])
                if not row['order_id']:
                    row['order_id'] = None
                settlements.append(SettlementRecord(**row))
                
    if os.path.exists(os.path.join(data_dir, 'bank.csv')):
        with open(os.path.join(data_dir, 'bank.csv'), 'r') as f:
            for row in csv.DictReader(f):
                row['deposit_amount'] = float(row['deposit_amount'])
                bank_records.append(BankRecord(**row))
                
    # --- ENTERPRISE UPGRADE: INITIALIZE SQLite DATABASE ---
    db_path = os.path.join(data_dir, "ledger.db")
    init_db(db_path)
    
    # ENTERPRISE: Event-Driven Simulation & Idempotency
    # Instead of wiping the DB, we act like a webhook endpoint receiving events.
    # The DB will reject duplicate transaction_ids.
    new_records_added = insert_pending_records(db_path, bank_records)
    print(f"[WEBHOOK SIMULATOR] Received {len(bank_records)} bank events. {new_records_added} new records queued for processing. {len(bank_records) - new_records_added} duplicate events ignored.")
                
    # 2. Layer 1: Deterministic Engine (Filters out the easy ones)
    results, orphan_orders, orphan_settlements, orphan_bank = match_deterministic(
        orders, settlements, bank_records
    )
    
    # Save perfectly matched records to the database instantly
    for r in results:
        update_ledger_record(db_path, r)
    
    # 3. Layer 2: AI Agent (Handles the messy orphans)
    for bank in list(orphan_bank):
        
        # We pass the remaining orphans to the AI
        ai_decision = resolve_with_ai(bank, orphan_orders, orphan_settlements)
        
        # Look up the actual records the AI claimed to have matched
        selected_order = next((o for o in orphan_orders if o.order_id == ai_decision.matched_order_id), None)
        selected_settlement = next((s for s in orphan_settlements if s.payment_id == ai_decision.matched_payment_id), None)
        
        if selected_order and selected_settlement:
            # 4. Layer 3: Math Guardrail (Do we trust the AI?)
            is_valid = verify_math(
                order_amount=selected_order.amount,
                settled_amount=selected_settlement.settled_amount,
                bank_amount=bank.deposit_amount,
                fee=selected_settlement.fee
            )
            
            if is_valid:
                res = ReconciliationResult(
                    order_id=selected_order.order_id,
                    payment_id=selected_settlement.payment_id,
                    bank_transaction_id=bank.transaction_id,
                    match_type="AI_RESOLVED",
                    confidence=ai_decision.confidence,
                    order_amount=selected_order.amount,
                    settled_amount=selected_settlement.settled_amount,
                    bank_deposit_amount=bank.deposit_amount,
                    is_math_valid=True,
                    reasoning=ai_decision.reasoning
                )
                results.append(res)
                update_ledger_record(db_path, res)
                
                orphan_orders.remove(selected_order)
                orphan_settlements.remove(selected_settlement)
            else:
                res = ReconciliationResult(
                    order_id=selected_order.order_id,
                    payment_id=selected_settlement.payment_id,
                    bank_transaction_id=bank.transaction_id,
                    match_type="EXCEPTION",
                    confidence=MatchConfidence.LOW,
                    order_amount=selected_order.amount,
                    settled_amount=selected_settlement.settled_amount,
                    bank_deposit_amount=bank.deposit_amount,
                    is_math_valid=False,
                    reasoning=f"AI attempted match, but Math Guardrail blocked it. Bank received ₹{bank.deposit_amount} but expected ₹{selected_settlement.settled_amount}."
                )
                results.append(res)
                update_ledger_record(db_path, res)
        else:
            # AI could not figure it out at all.
            res = ReconciliationResult(
                order_id=None,
                payment_id=None,
                bank_transaction_id=bank.transaction_id,
                match_type="EXCEPTION",
                confidence=MatchConfidence.LOW,
                order_amount=0.0,
                settled_amount=0.0,
                bank_deposit_amount=bank.deposit_amount,
                is_math_valid=False,
                reasoning="AI could not confidently link this to any available records."
            )
            results.append(res)
            update_ledger_record(db_path, res)
            
    return results
