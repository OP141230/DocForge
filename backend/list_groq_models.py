"""List available Groq models for your API key."""
import asyncio
from openai import AsyncOpenAI
from app.core.config import get_settings

async def list_models():
    settings = get_settings()
    
    print(f"Testing API key: {settings.GROQ_API_KEY[:20]}...")
    print(f"Base URL: https://api.groq.com/openai/v1\n")
    
    client = AsyncOpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )
    
    try:
        models = await client.models.list()
        print(f"✅ API Key is valid! Found {len(models.data)} models:\n")
        for model in models.data:
            print(f"  • {model.id}")
        
        print("\n💡 Update GROQ_MODEL in .env to one of the above model IDs")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
