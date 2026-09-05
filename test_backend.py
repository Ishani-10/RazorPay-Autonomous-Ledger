import os
import sys

# Ensure imports work headlessly
sys.path.append(os.path.abspath("/home/user/Ishani/RazorPay"))

from data.generator import generate_synthetic_data
from core.engine import run_reconciliation

def test_backend_logic():
    print("--- INITIATING BACKEND LOGIC TEST ---")
    DATA_DIR = "/home/user/Ishani/RazorPay/data"
    
    # 1. Test Data Generation
    print("1. Testing Synthetic Data Generation...")
    generate_synthetic_data(DATA_DIR)
    
    assert os.path.exists(os.path.join(DATA_DIR, "orders.csv")), "orders.csv missing!"
    assert os.path.exists(os.path.join(DATA_DIR, "settlements.csv")), "settlements.csv missing!"
    assert os.path.exists(os.path.join(DATA_DIR, "bank.csv")), "bank.csv missing!"
    print("✅ Data Generation: PASSED")
    
    # 2. Test Reconciliation Engine
    print("\n2. Testing Core Engine Pipeline (Deterministic -> AI -> Verifier)...")
    results = run_reconciliation(DATA_DIR)
    
    total = len(results)
    deterministic = len([r for r in results if r.match_type == "DETERMINISTIC"])
    ai_resolved = len([r for r in results if r.match_type == "AI_RESOLVED"])
    exceptions = len([r for r in results if r.match_type == "EXCEPTION"])
    
    print(f"Total Processed: {total}")
    print(f"Deterministic Exact Matches: {deterministic}")
    print(f"AI Resolved (Fuzzy) Matches: {ai_resolved}")
    print(f"Math Exceptions Caught: {exceptions}")
    
    assert total > 0, "No results returned!"
    assert deterministic > 0, "Deterministic engine failed to match clean records."
    assert ai_resolved > 0, "AI Agent (Simulator) failed to reverse-engineer fuzzy matches."
    assert exceptions > 0, "Math Verifier failed to catch corrupted data exceptions."
    
    print("✅ Core Logic & Guardrails: PASSED")
    print("--- BACKEND TEST COMPLETE ---")

if __name__ == "__main__":
    test_backend_logic()
