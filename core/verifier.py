def verify_math(order_amount: float, settled_amount: float, bank_amount: float, fee: float) -> bool:
    """
    Layer 3: The Mathematical Guardrail.
    No matter what the AI says, if the accounting does not balance to the exact cent,
    we block the match. This is the ultimate "Trust" factor.
    """
    # 1. Did the bank receive exactly what Razorpay says they settled?
    if bank_amount != settled_amount:
        return False
        
    # 2. Is the settled amount exactly equal to the Order amount minus the Gateway fee?
    expected_settlement = round(order_amount - fee, 2)
    if expected_settlement != settled_amount:
        return False
        
    return True
