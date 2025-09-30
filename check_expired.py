import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
import re

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = 'https://ffcdoxneybkdmeeokddy.supabase.co'
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or "your-supabase-key-here"

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

try:
    # Get all track fittings
    response = supabase.table('track_fittings').select('*').execute()
    print(f"Total track fittings: {len(response.data)}")
    
    today = datetime.now().date()
    expired_items = []
    
    for fitting in response.data:
        supply_date = fitting.get('supply_date')
        warranty = fitting.get('warranty', '')
        
        # Parse supply date
        if isinstance(supply_date, str):
            try:
                supply_date = datetime.strptime(supply_date, "%Y-%m-%d").date()
            except ValueError:
                print(f"Invalid date format for fitting ID {fitting.get('id')}: {supply_date}")
                continue
        
        # Calculate warranty end date
        warranty_days = parse_warranty(warranty)
        if warranty_days > 0 and supply_date is not None:
            warranty_end = supply_date + timedelta(days=warranty_days)
            if today > warranty_end:
                expired_items.append({
                    'id': fitting.get('id'),
                    'lot': fitting.get('lot'),
                    'item': fitting.get('item'),
                    'vendor': fitting.get('vendor'),
                    'supply_date': supply_date,
                    'warranty': warranty,
                    'expired_days': (today - warranty_end).days
                })
                print(f"EXPIRED: Lot {fitting.get('lot')} expired {warranty_end} ({(today - warranty_end).days} days ago)")
            else:
                print(f"VALID: Lot {fitting.get('lot')} expires {warranty_end} ({(warranty_end - today).days} days left)")
        else:
            print(f"INVALID WARRANTY: Lot {fitting.get('lot')} has invalid warranty: {warranty}")
    
    print(f"\nTotal expired items: {len(expired_items)}")
    
    if expired_items:
        print("\nExpired items that should generate reports:")
        for item in expired_items:
            print(f"  - Lot: {item['lot']}, Expired: {item['expired_days']} days ago")
    else:
        print("\nNo expired items found.")
        
except Exception as e:
    print(f"Error checking expired items: {e}")
    import traceback
    traceback.print_exc()