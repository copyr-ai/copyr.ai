import os
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

# Create client with minimal options to avoid compatibility issues
try:
    # Try with basic configuration first
    supabase: Client = create_client(
        SUPABASE_URL, 
        SUPABASE_ANON_KEY,
        options=ClientOptions(
            # Remove any proxy configurations that might cause issues
            auto_refresh_token=True,
            persist_session=False  # Disable session persistence for server environments
        )
    )
except Exception as e:
    # Fallback to basic client creation if advanced options fail
    print(f"Warning: Advanced Supabase configuration failed ({e}), using basic client")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Create a service client for admin operations (if service key is available)
try:
    if SUPABASE_SERVICE_KEY:
        supabase_admin: Client = create_client(
            SUPABASE_URL, 
            SUPABASE_SERVICE_KEY,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False
            )
        )
    else:
        supabase_admin = supabase  # Fallback to regular client
except Exception as e:
    print(f"Warning: Service client creation failed ({e}), using regular client")
    supabase_admin = supabase