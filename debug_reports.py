import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = 'https://ffcdoxneybkdmeeokddy.supabase.co'
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or "your-supabase-key-here"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    # Check if there are any replacement reports
    response = supabase.table('replacement_reports').select('*').execute()
    print(f"Total replacement reports: {len(response.data)}")
    
    if response.data:
        print("Sample reports:")
        for i, report in enumerate(response.data[:3]):
            print(f"  {i+1}. ID: {report.get('id')}, Lot: {report.get('lot')}, Status: {report.get('status')}, Created: {report.get('created_at')}")
    else:
        print("No replacement reports found.")
        
    # Check if there are any track fittings
    response2 = supabase.table('track_fittings').select('*').execute()
    print(f"\nTotal track fittings: {len(response2.data)}")
    
    if response2.data:
        print("Sample track fittings:")
        for i, fitting in enumerate(response2.data[:3]):
            print(f"  {i+1}. ID: {fitting.get('id')}, Lot: {fitting.get('lot')}, Warranty: {fitting.get('warranty')}, Supply Date: {fitting.get('supply_date')}")
    else:
        print("No track fittings found.")
        
except Exception as e:
    print(f"Error connecting to database: {e}")