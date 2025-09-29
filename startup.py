#!/usr/bin/env python3
"""
Startup script for production deployment
Handles database initialization and environment checks
"""
import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    load_dotenv()
    
    required_vars = [
        'SUPABASE_KEY',
        'FLASK_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def test_database_connection():
    """Test database connection"""
    try:
        from supabase import create_client
        
        supabase_url = 'https://ffcdoxneybkdmeeokddy.supabase.co'
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_key or supabase_key == "your-supabase-key-here":
            print("❌ Invalid Supabase key")
            return False
            
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection
        response = supabase.table('users').select('*').limit(1).execute()
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main startup check"""
    print("🚀 Starting Railway QR Management System...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Test database
    if not test_database_connection():
        print("⚠️  Database connection failed, but continuing startup...")
    
    print("✅ Pre-flight checks completed")
    print("🌐 Starting web server...")

if __name__ == "__main__":
    main()