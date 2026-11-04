"""Test script for conversation and message management API."""
import requests
import json
import uuid

BASE_URL = "http://localhost:8000"


def print_response(title, response):
    """Print formatted response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def main():
    """Test conversation and message endpoints."""
    print("\n🚀 DocForge Conversation & Message API Test Script")
    print("="*60)
    
    # Test data
    test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePass123!"
    test_email2 = f"testuser2_{uuid.uuid4().hex[:8]}@example.com"
    
    session = requests.Session()
    
    # 1. Register first user
    print("\n📝 Step 1: Registering first test user...")
    response = session.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": "Test User",
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    })
    print_response("Register User 1", response)
    
    if response.status_code != 201:
        print("❌ Registration failed. Exiting.")
        return
    
    # 2. Login first user
    print("\n🔐 Step 2: Logging in first user...")
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    print_response("Login User 1", response)
    
    if response.status_code != 200:
        print("❌ Login failed. Exiting.")
        return
    
    # Session cookie is automatically stored in session object
    print("✅ User 1 logged in successfully")
    
    # 3. Create a conversation
    print("\n💬 Step 3: Creating a conversation...")
    response = session.post(f"{BASE_URL}/api/conversations", json={
        "title": "My First Conversation"
    })
    print_response("Create Conversation", response)
    
    if response.status_code != 201:
        print("❌ Failed to create conversation. Exiting.")
        return
    
    conversation_id = response.json()["id"]
    print(f"✅ Conversation created with ID: {conversation_id}")
    
    # 4. List conversations
    print("\n📋 Step 4: Listing conversations...")
    response = session.get(f"{BASE_URL}/api/conversations")
    print_response("List Conversations", response)
    
    # 5. Get conversation by ID
    print("\n🔍 Step 5: Getting conversation by ID...")
    response = session.get(f"{BASE_URL}/api/conversations/{conversation_id}")
    print_response("Get Conversation", response)
    
    # 6. Add messages to conversation
    print("\n✉️ Step 6: Adding messages to conversation...")
    
    # User message
    response = session.post(
        f"{BASE_URL}/api/conversations/{conversation_id}/messages",
        json={"role": "user", "content": "Hello, I need help with documentation"}
    )
    print_response("Create Message 1 (User)", response)
    
    if response.status_code != 201:
        print("❌ Failed to create message. Continuing...")
    else:
        print(f"✅ Message created with sequence: {response.json()['sequence_number']}")
    
    # Assistant message
    response = session.post(
        f"{BASE_URL}/api/conversations/{conversation_id}/messages",
        json={"role": "assistant", "content": "I'd be happy to help! What kind of documentation do you need?"}
    )
    print_response("Create Message 2 (Assistant)", response)
    
    if response.status_code == 201:
        print(f"✅ Message created with sequence: {response.json()['sequence_number']}")
    
    # Another user message
    response = session.post(
        f"{BASE_URL}/api/conversations/{conversation_id}/messages",
        json={"role": "user", "content": "Can you help me generate a technical specification?"}
    )
    print_response("Create Message 3 (User)", response)
    
    if response.status_code == 201:
        print(f"✅ Message created with sequence: {response.json()['sequence_number']}")
    
    # 7. List messages
    print("\n📨 Step 7: Listing messages in conversation...")
    response = session.get(f"{BASE_URL}/api/conversations/{conversation_id}/messages")
    print_response("List Messages", response)
    
    # 8. Update conversation title
    print("\n✏️ Step 8: Updating conversation title...")
    response = session.put(
        f"{BASE_URL}/api/conversations/{conversation_id}",
        json={"title": "Documentation Help - Updated"}
    )
    print_response("Update Conversation Title", response)
    
    # 9. Register and login second user
    print("\n👤 Step 9: Testing access control with second user...")
    session2 = requests.Session()
    
    response = session2.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": "Test User 2",
        "email": test_email2,
        "password": test_password,
        "confirm_password": test_password
    })
    print_response("Register User 2", response)
    
    response = session2.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_email2,
        "password": test_password
    })
    print_response("Login User 2", response)
    
    # Try to access first user's conversation
    print("\n🔒 Step 10: Verifying User 2 cannot access User 1's conversation...")
    response = session2.get(f"{BASE_URL}/api/conversations/{conversation_id}")
    print_response("User 2 Trying to Access User 1's Conversation", response)
    
    if response.status_code == 404:
        print("✅ Access control working correctly - User 2 cannot access User 1's conversation")
    else:
        print("⚠️ Access control issue - User 2 should not be able to access this conversation")
    
    # 11. Delete conversation (as User 1)
    print("\n🗑️ Step 11: Deleting conversation (as User 1)...")
    response = session.delete(f"{BASE_URL}/api/conversations/{conversation_id}")
    print_response("Delete Conversation", response)
    
    if response.status_code == 204:
        print("✅ Conversation deleted successfully")
    
    # Verify deletion
    print("\n✔️ Step 12: Verifying conversation was deleted...")
    response = session.get(f"{BASE_URL}/api/conversations/{conversation_id}")
    print_response("Verify Deletion", response)
    
    if response.status_code == 404:
        print("✅ Conversation successfully deleted - not found")
    
    # 12. Create conversation with default title
    print("\n💬 Step 13: Creating conversation with default title...")
    response = session.post(f"{BASE_URL}/api/conversations", json={})
    print_response("Create Conversation with Default Title", response)
    
    print("\n" + "="*60)
    print("✅ Test script completed!")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to backend server.")
        print("Make sure the backend is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
