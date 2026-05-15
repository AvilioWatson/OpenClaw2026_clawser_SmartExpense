import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

def test_claude_connection():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    
    print(f"--- TESTING CLAUDE CONNECTION ---")
    print(f"Base URL: {base_url}")
    print(f"API Key: {api_key[:10]}...{api_key[-5:] if api_key else ''}")
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY tidak ditemukan di .env")
        return

    try:
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url if base_url else None
        )
        
        print("\nMengirim pesan tes ke Claude...")
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Halo Claude, jika kamu menerima pesan ini, balas dengan 'Koneksi Berhasil!'"}
            ]
        )
        
        print(f"\nRespon dari Claude: {message.content[0].text}")
        print("\n✅ KONEKSI API BERHASIL!")
        
    except Exception as e:
        print(f"\n❌ KONEKSI GAGAL!")
        print(f"Error Detail: {str(e)}")
        print("\nTips: Pastikan Base URL Sumopod sudah benar (apakah butuh /v1 atau tidak).")

if __name__ == "__main__":
    test_claude_connection()
