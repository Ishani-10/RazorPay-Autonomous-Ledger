# SYS.LEDGER // Autonomous Reconciliation
**Built for Razorpay Track 04: AI Finance Controller**

## The Problem
Most AI applications focus on generation. In fintech, the bottleneck is **verification**. Reconciling messy bank statements (HDFC/ICICI) against internal Shopify orders and Razorpay settlement reports is a massive, manual pain point because text strings rarely match perfectly.

## The Architecture
This project is an enterprise-grade reconciliation pipeline built on a 3-layer architecture:

1. **Layer 1 (Deterministic Engine):** Fast, cheap Python logic that clears 70% of perfect matches instantly. Zero AI tokens wasted.
2. **Layer 2 (Fuzzy LLM Agent):** Uses an LLM to deduce complex orphans (missing IDs, bundled payouts) by reverse-engineering the 2% gateway fee. **All PII is dynamically masked before hitting the LLM.**
3. **Layer 3 (The Math Guardrail):** The "Trust Factor". Before any AI-suggested match is committed, a strict Python script verifies that `Bank Deposit == Settlement - Fee`. If the AI hallucinates, it is hard-blocked and routed to a human exception queue.

### Enterprise Features Included:
- **Idempotency:** Webhook deduplication.
- **ACID Database Transactions:** SQLite state management to prevent silent data corruption.
- **Strict Pydantic Schemas:** Enforcing structured JSON outputs from the LLM.

## How to Run Locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m streamlit run ui/dashboard.py
