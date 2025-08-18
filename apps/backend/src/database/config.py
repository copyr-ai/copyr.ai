import os
from dotenv import load_dotenv
from supabase import create_client, Client
# from supabase.client import ClientOptions  # Commented out due to version compatibility

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

# Create client with basic configuration for compatibility
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("Supabase client created successfully")
except Exception as e:
    print(f"Error creating Supabase client: {e}")
    raise

# Create a service client for admin operations (if service key is available)
try:
    if SUPABASE_SERVICE_KEY:
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("Supabase admin client created successfully")
    else:
        supabase_admin = supabase  # Fallback to regular client
        print("Using regular client for admin operations (no service key)")
except Exception as e:
    print(f"Warning: Service client creation failed ({e}), using regular client")
    supabase_admin = supabase