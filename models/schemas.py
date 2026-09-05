from pydantic import BaseModel, Field
from typing import Optional
from typing_extensions import Literal
from enum import Enum

class MatchConfidence(str, Enum):
    HIGH = "HIGH"         # 100% Deterministic match
    MEDIUM = "MEDIUM"     # AI confidently matched it
    LOW = "LOW"           # AI is unsure or Math Guardrail blocked it

# ---------------------------------------------------------
# INPUT SCHEMAS: The raw data structures from our 3 sources
# ---------------------------------------------------------

class OrderRecord(BaseModel):
    order_id: str
    customer_name: str
    amount: float
    order_date: str

class SettlementRecord(BaseModel):
    payment_id: str
    order_id: Optional[str] = None
    gross_amount: float
    fee: float
    settled_amount: float
    settlement_date: str

class BankRecord(BaseModel):
    transaction_id: str
    description: str
    deposit_amount: float
    transaction_date: str

# ---------------------------------------------------------
# OUTPUT SCHEMAS: The structure of our final matched ledger
# ---------------------------------------------------------

class ReconciliationResult(BaseModel):
    """Represents a finalized decision on a single transaction."""
    order_id: Optional[str]
    payment_id: Optional[str]
    bank_transaction_id: Optional[str]
    
    match_type: Literal["DETERMINISTIC", "AI_RESOLVED", "EXCEPTION"]
    confidence: MatchConfidence
    
    # Financial Validation
    order_amount: float
    settled_amount: float
    bank_deposit_amount: float
    is_math_valid: bool = False
    
    # Audit Trail
    reasoning: str
    
# ---------------------------------------------------------
# AI COMMUNICATION SCHEMAS: Enforcing strict LLM output
# ---------------------------------------------------------

class AIResolutionResponse(BaseModel):
    """
    This is the strict JSON schema we force OpenAI to return.
    It prevents the LLM from outputting conversational text.
    """
    matched_payment_id: str = Field(description="The payment_id from the settlement dataset that belongs to this bank transaction.")
    matched_order_id: str = Field(description="The order_id from the orders dataset that belongs to this bank transaction.")
    confidence: MatchConfidence = Field(description="How confident the AI is in this fuzzy match.")
    reasoning: str = Field(description="A one-sentence explanation of exactly how the AI figured out this match (e.g. reverse fee calculation, fuzzy name matching).")
