import requests
import json

# ── Example 1: Remove valid invoice ──
def remove_valid_invoice():
    url = "http://localhost:8900/data_analysis/api/remove-invoice/"
    
    headers = {
        "X-API-KEY": "SECRET123",
        "Content-Type": "application/json"
    }
    
    data = {
        "invoice_number": "10989"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    print("✅ Valid Invoice Removal:")
    print(f"Status: {response.status_code}")
    # print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response

# ── Example 2: Remove non-existent invoice ──
def remove_invalid_invoice():
    url = "http://localhost:8900/data_analysis/api/remove-invoice/"
    
    headers = {
        "X-API-KEY": "SECRET123",
        "Content-Type": "application/json"
    }
    
    data = {
        "invoice_number": "99999"  # Invoice that doesn't exist
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    print("\n❌ Invalid Invoice Removal:")
    print(f"Status: {response.status_code}")
    # print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response

# ── Run examples ──
if __name__ == "__main__":
    remove_valid_invoice()
    remove_invalid_invoice()