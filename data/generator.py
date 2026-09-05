import csv
import random
import uuid
from datetime import datetime, timedelta
import os

def generate_synthetic_data(output_dir: str):
    """
    Generates synthetic, highly realistic messy data for The Autonomous Ledger.
    Creates three files:
      - orders.csv (Internal Shopify/ERP data)
      - settlements.csv (Razorpay Payment Gateway data)
      - bank.csv (Messy HDFC/ICICI bank statement)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    orders = []
    settlements = []
    bank = []

    start_date = datetime(2026, 8, 1)
    
    # CASE 1: 35 Deterministic (Clean) Matches
    # These should be matched instantly by Layer 1 (Python logic)
    for i in range(1, 36):
        order_date = start_date + timedelta(days=random.randint(0, 10))
        settlement_date = order_date + timedelta(days=2) # T+2 settlement
        
        order_id = f"ORD-{1000+i}"
        payment_id = f"pay_{uuid.uuid4().hex[:8]}"
        customer_name = f"Customer_{i}"
        amount = round(random.uniform(500.0, 5000.0), 2)
        fee = round(amount * 0.02, 2) # 2% gateway fee
        settled = round(amount - fee, 2)
        
        # 1. Order Record
        orders.append([order_id, customer_name, amount, order_date.strftime("%Y-%m-%d")])
        
        # 2. Razorpay Record
        settlements.append([payment_id, order_id, amount, fee, settled, settlement_date.strftime("%Y-%m-%d")])
        
        # 3. Bank Record (Clean Description)
        bank_tx_id = f"TXN{uuid.uuid4().hex[:10].upper()}"
        desc = f"NEFT-RZRPY-SETTLEMENT-{payment_id}"
        bank.append([bank_tx_id, desc, settled, settlement_date.strftime("%Y-%m-%d")])

    # CASE 2: 10 Fuzzy Matches (For Layer 2 AI)
    # Missing IDs, combined settlements, messy text.
    for i in range(36, 46):
        order_date = start_date + timedelta(days=random.randint(11, 20))
        settlement_date = order_date + timedelta(days=2)
        
        order_id = f"ORD-{1000+i}"
        payment_id = f"pay_{uuid.uuid4().hex[:8]}"
        customer_name = f"Customer_{i}_Fuzzy"
        amount = round(random.uniform(1000.0, 8000.0), 2)
        fee = round(amount * 0.02, 2)
        settled = round(amount - fee, 2)
        
        orders.append([order_id, customer_name, amount, order_date.strftime("%Y-%m-%d")])
        
        # Razorpay record is missing the Order ID (Data loss simulation)
        settlements.append([payment_id, "", amount, fee, settled, settlement_date.strftime("%Y-%m-%d")])
        
        # Bank record has absolute garbage description, no payment ID
        bank_tx_id = f"TXN{uuid.uuid4().hex[:10].upper()}"
        desc = f"IMPS/P2A/{customer_name[:5].upper()}/RAZORPAY/FUNDS"
        bank.append([bank_tx_id, desc, settled, settlement_date.strftime("%Y-%m-%d")])
        
    # CASE 3: 5 Exceptions (For Layer 3 Math Guardrail)
    # These should be rejected by the AI/Math rule and pushed to human review.
    for i in range(46, 51):
        order_date = start_date + timedelta(days=random.randint(21, 25))
        settlement_date = order_date + timedelta(days=2)
        
        order_id = f"ORD-{1000+i}"
        payment_id = f"pay_{uuid.uuid4().hex[:8]}"
        customer_name = f"Customer_{i}_Exception"
        amount = round(random.uniform(2000.0, 9000.0), 2)
        fee = round(amount * 0.02, 2)
        settled = round(amount - fee, 2)
        
        orders.append([order_id, customer_name, amount, order_date.strftime("%Y-%m-%d")])
        
        # Razorpay settles correctly
        settlements.append([payment_id, order_id, amount, fee, settled, settlement_date.strftime("%Y-%m-%d")])
        
        # Bank receives a different amount! (Simulating a chargeback or partial block)
        bank_tx_id = f"TXN{uuid.uuid4().hex[:10].upper()}"
        corrupted_amount = round(settled - 500.0, 2) # Missing ₹500
        desc = f"NEFT-RZRPY-SETTLEMENT-{payment_id}"
        bank.append([bank_tx_id, desc, corrupted_amount, settlement_date.strftime("%Y-%m-%d")])

    # Shuffle the datasets to simulate real-world disorder
    random.shuffle(orders)
    random.shuffle(settlements)
    random.shuffle(bank)

    # Write CSVs
    with open(os.path.join(output_dir, 'orders.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'customer_name', 'amount', 'order_date'])
        writer.writerows(orders)

    with open(os.path.join(output_dir, 'settlements.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['payment_id', 'order_id', 'gross_amount', 'fee', 'settled_amount', 'settlement_date'])
        writer.writerows(settlements)

    with open(os.path.join(output_dir, 'bank.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'description', 'deposit_amount', 'transaction_date'])
        writer.writerows(bank)
        
    print(f"✅ Successfully generated 50 synthetic records across 3 sources in {output_dir}")

if __name__ == "__main__":
    generate_synthetic_data(".")
