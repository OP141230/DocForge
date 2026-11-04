"""Quick test script for Groq provider setup."""
import asyncio
from app.core.config import get_settings
from app.providers.groq_provider import GroqProvider


async def test_groq():
    """Test Groq provider connection and generation."""
    settings = get_settings()
    
    print("🔍 Checking Groq configuration...")
    print(f"   AI_PROVIDER: {settings.AI_PROVIDER}")
    print(f"   GROQ_MODEL: {settings.GROQ_MODEL}")
    print(f"   GROQ_API_KEY: {'✅ Set' if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith('gsk_your') else '❌ Missing or placeholder'}")
    print()
    
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith('gsk_your'):
        print("❌ Error: GROQ_API_KEY not set properly in .env")
        print("   Please get a free key from: https://console.groq.com/keys")
        print("   Then update .env with your actual key")
        return
    
    print("🤖 Testing Groq provider...")
    provider = GroqProvider()
    
    # Test outline generation
    print("📝 Generating outline for: 'Python development guide'")
    try:
        from app.models.generation import DocumentRequirements
        requirements = DocumentRequirements(
            title="Python Development Environment Setup",
            topic="Create a technical guide for Python development environment setup",
            document_type="Technical Documentation",
            audience="developers",
            tone="professional",
            length="medium"
        )
        outline = await provider.generate_outline(requirements)
        print(f"✅ Success! Generated {len(outline.outline)} sections:")
        for i, section in enumerate(outline.outline[:3], 1):
            print(f"   {i}. {section.title}")
        if len(outline.outline) > 3:
            print(f"   ... and {len(outline.outline) - 3} more")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print()
    
    # Test content generation
    print("📄 Generating content for first section...")
    try:
        content = await provider.generate_content(
            outline,
            requirements
        )
        print(f"✅ Success! Generated content:")
        preview = content.content[0].blocks[0].content[0].text[:200].replace('\n', ' ')
        print(f"   {preview}...")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print()
    print("🎉 Groq provider is working correctly!")
    print("   You can now use DocForge with free AI generation.")


if __name__ == "__main__":
    asyncio.run(test_groq())
