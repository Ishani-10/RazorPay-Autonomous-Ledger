from typing import Tuple, List
from models.schemas import OrderRecord, SettlementRecord, BankRecord, ReconciliationResult, MatchConfidence

def match_deterministic(
    orders: List[OrderRecord],
    settlements: List[SettlementRecord],
    bank_records: List[BankRecord]
) -> Tuple[List[ReconciliationResult], List[OrderRecord], List[SettlementRecord], List[BankRecord]]:
    """
    Layer 1: High-speed, rule-based exact matching (No AI).
    Clears out 100% perfect matches instantly to save LLM tokens and compute.
    """
    results = []
    
    # We will use copies to keep track of orphans
    unmatched_orders = orders.copy()
    unmatched_settlements = settlements.copy()
    unmatched_bank = bank_records.copy()
    
    for bank in list(unmatched_bank):
        # Look for the exact payment_id in the bank description
        # e.g. "NEFT-RZRPY-SETTLEMENT-pay_xyz123"
        if "NEFT-RZRPY-SETTLEMENT-" in bank.description:
            # Extract payment ID
            payment_id_extracted = bank.description.split("NEFT-RZRPY-SETTLEMENT-")[-1].strip()
            
            # Find exact match in settlements
            matching_settlement = next((s for s in unmatched_settlements if s.payment_id == payment_id_extracted), None)
            
            if matching_settlement and matching_settlement.order_id:
                # Find exact match in orders
                matching_order = next((o for o in unmatched_orders if o.order_id == matching_settlement.order_id), None)
                
                if matching_order:
                    # Deterministic match successful!
                    # Check if math is perfectly valid
                    expected_settlement = round(matching_order.amount - matching_settlement.fee, 2)
                    math_valid = (
                        matching_settlement.settled_amount == bank.deposit_amount and 
                        expected_settlement == matching_settlement.settled_amount
                    )
                    
                    if math_valid:
                        results.append(
                            ReconciliationResult(
                                order_id=matching_order.order_id,
                                payment_id=matching_settlement.payment_id,
                                bank_transaction_id=bank.transaction_id,
                                match_type="DETERMINISTIC",
                                confidence=MatchConfidence.HIGH,
                                order_amount=matching_order.amount,
                                settled_amount=matching_settlement.settled_amount,
                                bank_deposit_amount=bank.deposit_amount,
                                is_math_valid=True,
                                reasoning="Exact ID match across all three systems and mathematical validation passed."
                            )
                        )
                        
                        unmatched_bank.remove(bank)
                        unmatched_settlements.remove(matching_settlement)
                        unmatched_orders.remove(matching_order)

    return results, unmatched_orders, unmatched_settlements, unmatched_bank
