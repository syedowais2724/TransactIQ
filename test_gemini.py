"""
Quick test script to verify Gemini API is working.
"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key: {api_key[:20]}..." if api_key else "NO API KEY FOUND!")

if not api_key:
    print("ERROR: GEMINI_API_KEY not set in .env file")
    exit(1)

# Try NEW API first
try:
    print("\n=== TESTING NEW google.genai API ===")
    from google import genai
    
    print("✓ Configuring client...")
    client = genai.Client(api_key=api_key)
    
    print("✓ Sending test request (gemini-2.0-flash-exp)...")
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents="Classify: merchant=Starbucks, amount=45. Reply with just the category (Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, or Other)."
    )
    
    print("\n✓ SUCCESS! New Gemini API is working!")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"\n✗ NEW API ERROR: {type(e).__name__}: {str(e)}")
    
    # Try OLD API as fallback
    try:
        print("\n=== TESTING OLD google.generativeai API (fallback) ===")
        import google.generativeai as genai_old
        
        print("✓ Configuring...")
        genai_old.configure(api_key=api_key)
        
        print("✓ Creating model (gemini-1.5-flash)...")
        model = genai_old.GenerativeModel('gemini-1.5-flash')
        
        print("✓ Sending test request...")
        response = model.generate_content("Classify: merchant=Starbucks, amount=45. Reply with category.")
        
        print("\n✓ SUCCESS! Old Gemini API is working!")
        print(f"Response: {response.text}")
        
    except Exception as e2:
        print(f"\n✗ OLD API ALSO FAILED: {type(e2).__name__}: {str(e2)}")
        print("\nPossible issues:")
        print("1. Invalid API key format or expired")
        print("2. API key not enabled for Gemini")
        print("3. Network/firewall blocking Google APIs")
        print("4. Quota exceeded")
        print("\nPlease verify your API key at: https://aistudio.google.com/apikey")
