from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Test query 
result = supabase.table("babies").select("*").execute()
print(f"Connected to Supabase! Found {len(result.data)} babies in database.")