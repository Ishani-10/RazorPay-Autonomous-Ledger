import re

def mask_customer_name(name: str) -> str:
    """
    Masks a customer name for privacy before sending to LLMs.
    E.g. "Customer_42_Fuzzy" -> "C***_42_Fuzzy"
    Real banks cannot send raw PII (Personally Identifiable Information) to OpenAI.
    """
    if not name or len(name) <= 2:
        return "***"
    
    # We keep the first character and the last few characters (useful for fuzzy matching digits)
    # E.g. Customer_10 => C***_10
    
    # For synthetic names like "Customer_42_Fuzzy"
    if "_" in name:
        parts = name.split("_")
        masked_first = parts[0][0] + "***" + parts[0][-1] if len(parts[0]) > 2 else "***"
        return "_".join([masked_first] + parts[1:])
        
    return name[0] + "***" + name[-2:]

def redact_orders_pii(orders: list) -> list:
    """Returns a copy of the orders list with all PII masked."""
    redacted = []
    for order in orders:
        # Pydantic model_copy allows us to duplicate and update safely
        redacted_order = order.model_copy(update={
            "customer_name": mask_customer_name(order.customer_name)
        })
        redacted.append(redacted_order)
    return redacted

def redact_bank_pii(bank_record):
    """
    Bank descriptions often contain the raw name in the text 
    (e.g., IMPS/P2A/CUSTOMER_42/RAZORPAY). We use a basic regex substitution.
    """
    desc = bank_record.description
    
    # We look for the "Customer_X" pattern we generated and mask it
    # In a real enterprise system, this would use a heavy NLP NER (Named Entity Recognition) model like Presidio
    redacted_desc = re.sub(r'(Customer_[0-9a-zA-Z_]+)', lambda m: mask_customer_name(m.group(1)), desc, flags=re.IGNORECASE)
    
    return bank_record.model_copy(update={"description": redacted_desc})
