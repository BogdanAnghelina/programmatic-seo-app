from supabase import create_client, Client

def test_supabase_connection(url: str, api_key: str, table_name: str) -> None:
    try:
        supabase: Client = create_client(url, api_key)
        response = supabase.table(table_name).select('*').execute()
        print("Connection successful!")
        print("Response data:", response.data)
    except Exception as e:
        print("Connection failed!")
        print("Error:", e)

if __name__ == "__main__":
    SUPABASE_URL = "https://ogwekmdhhbuiekbpndsv.supabase.co"
    SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nd2VrbWRoaGJ1aWVrYnBuZHN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTE3NDE2MjgsImV4cCI6MjAyNzMxNzYyOH0.LdZE4bQU1s0pLG-tuKP4--uZpjX9sg5AXhDnkmJG_ck"
    TABLE_NAME = "users"  # Replace with your actual table name

    test_supabase_connection(SUPABASE_URL, SUPABASE_API_KEY, TABLE_NAME)
