import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
import requests
import re

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = 'https://ffcdoxneybkdmeeokddy.supabase.co'
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or "your-supabase-key-here"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat-v3.1:free"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def parse_warranty(warranty_str):
    if not warranty_str:
        return 0
    match = re.match(r"(\d+)\s*(year|month|day)s?", warranty_str.lower())
    if not match:
        return 0
    value, unit = match.groups()
    value = int(value)
    return value * 365 if unit == "year" else value * 30 if unit == "month" else value

def generate_replacement_report(item, vendor, lot, supply_date, warranty, warranty_end, status, location):
    """Generate a replacement report for an expired item"""
    agentic_prompt = f"""
    The following railway fitting has expired warranty. Generate a replacement report.

    Product: {item}
    Vendor: {vendor}
    Lot: {lot}
    Supply Date: {supply_date}
    Warranty: {warranty}
    Expired On: {warranty_end}
    Inspection Status: {status}
    Location: {location}

    Please generate a professional replacement report explaining the situation and recommending next steps.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "AI-Driven QR Code System"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for warranty validation and railway fittings inspection."},
            {"role": "user", "content": agentic_prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.3
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Could not generate replacement report: {e}"

try:
    # Get an expired item
    response = supabase.table('track_fittings').select('*').eq('lot', 'RP2022-001').execute()
    
    if not response.data:
        print("No expired item found with lot RP2022-001")
        exit(1)
        
    record = response.data[0]
    print(f"Found expired item: {record.get('item')} (Lot: {record.get('lot')})")
    
    # Generate replacement report
    replacement_report = generate_replacement_report(
        item=record['item'],
        vendor=record['vendor'],
        lot=record['lot'],
        supply_date=record['supply_date'],
        warranty=record['warranty'],
        warranty_end="2024-07-31",  # We know this is expired
        status=record['inspection_status'],
        location=record['location']
    )
    
    print("Generated replacement report:")
    print(replacement_report)
    
    # Save to database
    try:
        result = supabase.table('replacement_reports').insert({
            'lot': record['lot'],
            'item': record['item'],
            'vendor': record['vendor'],
            'expired_on': "2024-07-31",
            'report': replacement_report,
            'status': 'Pending'
        }).execute()
        
        print(f"Successfully saved replacement report with ID: {result.data[0]['id']}")
    except Exception as e:
        print(f"Error saving replacement report: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()