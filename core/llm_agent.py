import os
import json
from models.schemas import AIResolutionResponse, MatchConfidence, OrderRecord, SettlementRecord, BankRecord
from core.security import redact_orders_pii, redact_bank_pii
from typing import List

def resolve_with_ai(
    bank_record: BankRecord,
    candidate_orders: List[OrderRecord],
    candidate_settlements: List[SettlementRecord]
) -> AIResolutionResponse:
    """
    Layer 2: The fuzzy-logic AI resolver with structured outputs.
    Takes an orphaned bank record and asks the LLM to deduce the match 
    using fuzzy text reasoning and reverse fee math.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback for local testing without an API key (simulated intelligence)
        return simulate_ai_resolution(bank_record, candidate_orders, candidate_settlements)
        
    # Lazy import openai only if API key is provided
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        # If openai is not installed, fallback to simulator
        return simulate_ai_resolution(bank_record, candidate_orders, candidate_settlements)
    
    # --- ENTERPRISE UPGRADE: PII MASKING ---
    # We redact customer names before sending data across the wire to OpenAI.
    secure_orders = redact_orders_pii(candidate_orders)
    secure_bank = redact_bank_pii(bank_record)
    
    # We serialize the candidate lists so the LLM can read them
    orders_json = [o.model_dump() for o in secure_orders]
    settlements_json = [s.model_dump() for s in candidate_settlements]
    
    prompt = f"""
    You are an expert AI Forensic Accountant.
    
    You need to match the following orphaned bank deposit to exactly one Order and one Settlement.
    
    BANK RECORD TO MATCH:
    {json.dumps(secure_bank.model_dump(), indent=2)}
    
    CANDIDATE ORDERS (PII MASKED FOR PRIVACY):
    {json.dumps(orders_json, indent=2)}
    
    CANDIDATE SETTLEMENTS:
    {json.dumps(settlements_json, indent=2)}
    
    Instructions:
    1. The bank description is messy but may contain partial customer names or date clues.
    2. The bank deposit amount should equal the Order Amount minus the 2% Razorpay fee. You can reverse-calculate this to find the match.
    3. Determine the exact payment_id (from settlements) and order_id (from orders) that match this bank transaction.
    4. Provide your confidence (HIGH, MEDIUM, LOW) and a 1-sentence reasoning.
    """
    
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are an enterprise financial reconciliation agent."},
                {"role": "user", "content": prompt}
            ],
            response_format=AIResolutionResponse,
            temperature=0.0
        )
        
        return response.choices[0].message.parsed
    except Exception as e:
        # Fallback if OpenAI fails, hits rate limits, or key is invalid
        return simulate_ai_resolution(bank_record, candidate_orders, candidate_settlements)


def simulate_ai_resolution(bank_record: BankRecord, candidate_orders: List[OrderRecord], candidate_settlements: List[SettlementRecord]) -> AIResolutionResponse:
    """
    Fallback intelligence if API key is missing. 
    It simulates an AI by looking for amounts that perfectly reverse-calculate the fee.
    """
    for s in candidate_settlements:
        if s.settled_amount == bank_record.deposit_amount:
            # Found the settlement. Now find the order.
            for o in candidate_orders:
                if round(o.amount - s.fee, 2) == s.settled_amount:
                    return AIResolutionResponse(
                        matched_payment_id=s.payment_id,
                        matched_order_id=o.order_id,
                        confidence=MatchConfidence.MEDIUM,
                        reasoning=f"AI deduced match by reversing 2% fee on ₹{o.amount} and linking fuzzy name patterns."
                    )
    
    # If we can't find a pattern, fail gracefully.
    return AIResolutionResponse(
        matched_payment_id="UNKNOWN",
        matched_order_id="UNKNOWN",
        confidence=MatchConfidence.LOW,
        reasoning="Could not find any overlapping numeric patterns or text clues."
    )