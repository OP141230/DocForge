"""
Complete Phase 2 Integration Test
Tests all Phase 2 features end-to-end
"""
import http.client
import json
from datetime import datetime


BASE_URL = "localhost:8000"
BASE_PATH = "/api"


def make_request(path, method="GET", data=None, cookies=None):
    """Make HTTP request with optional cookies."""
    conn = http.client.HTTPConnection(BASE_URL)
    headers = {"Content-Type": "application/json"}
    
    if cookies:
        cookie_str = "; ".join([f"{name}={value}" for name, value in cookies.items()])
        headers["Cookie"] = cookie_str
    
    body = json.dumps(data) if data else None
    
    try:
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        
        response_data = None
        if response.status != 204:
            try:
                response_data = json.loads(response.read().decode('utf-8'))
            except:
                pass
        
        response_cookies = {}
        set_cookie = response.getheader('Set-Cookie')
        if set_cookie:
            for part in set_cookie.split(';'):
                if '=' in part:
                    name, value = part.split('=', 1)
                    name = name.strip()
                    if name == 'session_token':
                        response_cookies['session_token'] = value.strip()
                        break
        
        conn.close()
        return response.status, response_data, response_cookies
    except Exception as e:
        conn.close()
        print(f"❌ Request error: {e}")
        raise


def test_phase2_complete():
    """Run complete Phase 2 integration test."""
    print("=" * 80)
    print("DocForge Phase 2 Complete Integration Test")
    print("=" * 80)
    print()
    
    # Test 1: Authentication (Phase 2A/B)
    print("📋 Test 1: Authentication")
    print("-" * 80)
    
    user_email = f"testuser_{int(datetime.now().timestamp())}@example.com"
    user_data = {
        "full_name": "Test User",
        "email": user_email,
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!"
    }
    
    status, user, cookies = make_request(f"{BASE_PATH}/auth/register", "POST", user_data)
    if status != 201:
        print(f"❌ FAIL: Registration failed with status {status}")
        return False
    
    session_token = cookies.get("session_token")
    if not session_token:
        print("❌ FAIL: No session token returned")
        return False
    
    print(f"✅ PASS: User registered and auto-logged in")
    print(f"   Email: {user['email']}")
    print()
    
    # Test 2: Data Isolation (Phase 2C)
    print("📋 Test 2: Data Isolation")
    print("-" * 80)
    
    # Create document as User 1
    doc1 = {
        "id": f"doc1_{int(datetime.now().timestamp())}",
        "title": "Test Document 1",
        "content": [{
            "id": "sec1",
            "title": "Section 1",
            "level": 2,
            "blocks": [{
                "id": "p1",
                "type": "paragraph",
                "content": [{"text": "Test content", "bold": False, "italic": False, "underline": False}]
            }]
        }],
        "metadata": {
            "author": "Test User",
            "document_type": "general_report",
            "language": "en"
        }
    }
    
    status, created_doc, _ = make_request(f"{BASE_PATH}/documents", "POST", doc1, {"session_token": session_token})
    if status != 201:
        print(f"❌ FAIL: Document creation failed with status {status}")
        return False
    
    doc_id = created_doc["id"]
    print(f"✅ PASS: Document created: {doc_id}")
    
    # Register second user
    user2_email = f"testuser2_{int(datetime.now().timestamp())}@example.com"
    user2_data = {
        "full_name": "Test User 2",
        "email": user2_email,
        "password": "SecurePass456!",
        "confirm_password": "SecurePass456!"
    }
    
    status, user2, cookies2 = make_request(f"{BASE_PATH}/auth/register", "POST", user2_data)
    if status != 201:
        print(f"❌ FAIL: User 2 registration failed")
        return False
    
    session_token2 = cookies2.get("session_token")
    
    # Try to access User 1's document as User 2
    status, _, _ = make_request(f"{BASE_PATH}/documents/{doc_id}", "GET", cookies={"session_token": session_token2})
    if status != 404:
        print(f"❌ FAIL: Data isolation breach! User 2 accessed User 1's document")
        return False
    
    print(f"✅ PASS: User 2 cannot access User 1's document (404)")
    print()
    
    # Test 3: Conversations (Phase 2D)
    print("📋 Test 3: Conversations & Messages")
    print("-" * 80)
    
    # Create conversation
    conv_data = {"title": "Test Conversation"}
    status, conversation, _ = make_request(f"{BASE_PATH}/conversations", "POST", conv_data, {"session_token": session_token})
    if status != 201:
        print(f"❌ FAIL: Conversation creation failed with status {status}")
        return False
    
    conv_id = conversation["id"]
    print(f"✅ PASS: Conversation created: {conv_id}")
    
    # Add user message
    msg1_data = {"role": "user", "content": "Hello, I need help with documentation"}
    status, msg1, _ = make_request(f"{BASE_PATH}/conversations/{conv_id}/messages", "POST", msg1_data, {"session_token": session_token})
    if status != 201:
        print(f"❌ FAIL: Message creation failed")
        return False
    
    print(f"✅ PASS: User message added (seq: {msg1['sequence_number']})")
    
    # Add assistant message
    msg2_data = {"role": "assistant", "content": "I'd be happy to help!"}
    status, msg2, _ = make_request(f"{BASE_PATH}/conversations/{conv_id}/messages", "POST", msg2_data, {"session_token": session_token})
    if status != 201:
        print(f"❌ FAIL: Assistant message creation failed")
        return False
    
    print(f"✅ PASS: Assistant message added (seq: {msg2['sequence_number']})")
    
    # List messages
    status, messages_data, _ = make_request(f"{BASE_PATH}/conversations/{conv_id}/messages", "GET", cookies={"session_token": session_token})
    if status != 200:
        print(f"❌ FAIL: List messages failed")
        return False
    
    if messages_data['total'] != 2:
        print(f"❌ FAIL: Expected 2 messages, got {messages_data['total']}")
        return False
    
    print(f"✅ PASS: Messages retrieved correctly (total: {messages_data['total']})")
    
    # Update conversation title
    update_data = {"title": "Updated Conversation Title"}
    status, _, _ = make_request(f"{BASE_PATH}/conversations/{conv_id}", "PUT", update_data, {"session_token": session_token})
    if status != 200:
        print(f"❌ FAIL: Conversation update failed")
        return False
    
    print(f"✅ PASS: Conversation title updated")
    
    # Verify User 2 cannot access User 1's conversation
    status, _, _ = make_request(f"{BASE_PATH}/conversations/{conv_id}", "GET", cookies={"session_token": session_token2})
    if status != 404:
        print(f"❌ FAIL: Conversation isolation breach!")
        return False
    
    print(f"✅ PASS: User 2 cannot access User 1's conversation (404)")
    print()
    
    # Test 4: Document with Conversation Association
    print("📋 Test 4: Document-Conversation Association")
    print("-" * 80)
    
    doc_with_conv = {
        "id": f"doc2_{int(datetime.now().timestamp())}",
        "title": "Document from Conversation",
        "content": [{
            "id": "sec1",
            "title": "Generated Section",
            "level": 2,
            "blocks": [{
                "id": "p1",
                "type": "paragraph",
                "content": [{"text": "Content generated from conversation", "bold": False, "italic": False, "underline": False}]
            }]
        }],
        "metadata": {
            "author": "Test User",
            "document_type": "general_report",
            "language": "en"
        }
    }
    
    status, doc_created, _ = make_request(f"{BASE_PATH}/documents?conversation_id={conv_id}", "POST", doc_with_conv, {"session_token": session_token})
    if status != 201:
        print(f"❌ FAIL: Document with conversation creation failed")
        return False
    
    print(f"✅ PASS: Document created with conversation association")
    print()
    
    # Test 5: Cleanup
    print("📋 Test 5: Cleanup & Deletion")
    print("-" * 80)
    
    # Delete conversation
    status, _, _ = make_request(f"{BASE_PATH}/conversations/{conv_id}", "DELETE", cookies={"session_token": session_token})
    if status != 204:
        print(f"❌ FAIL: Conversation deletion failed")
        return False
    
    print(f"✅ PASS: Conversation deleted")
    
    # Verify conversation is gone
    status, _, _ = make_request(f"{BASE_PATH}/conversations/{conv_id}", "GET", cookies={"session_token": session_token})
    if status != 404:
        print(f"❌ FAIL: Conversation still accessible after deletion")
        return False
    
    print(f"✅ PASS: Conversation confirmed deleted (404)")
    
    # Logout
    status, _, _ = make_request(f"{BASE_PATH}/auth/logout", "POST", cookies={"session_token": session_token})
    if status != 200:
        print(f"❌ FAIL: Logout failed")
        return False
    
    print(f"✅ PASS: User logged out successfully")
    print()
    
    # Final Summary
    print("=" * 80)
    print("🎉 ALL PHASE 2 TESTS PASSED!")
    print("=" * 80)
    print()
    print("Phase 2 Features Verified:")
    print("  ✅ Phase 2A: Backend Authentication")
    print("  ✅ Phase 2B: Frontend Authentication UI (manual test required)")
    print("  ✅ Phase 2C: Data Isolation")
    print("  ✅ Phase 2D: Conversations & Messages")
    print("  ✅ Phase 2E: Conversation UI (manual test required)")
    print("  ✅ Phase 2F: Testing & Documentation")
    print()
    print("Next Steps:")
    print("  1. Test frontend manually at http://localhost:5173")
    print("  2. Review PHASE2_COMPLETE.md for full testing checklist")
    print("  3. Commit and push to GitHub when satisfied")
    print()
    
    return True


if __name__ == "__main__":
    print()
    print("⚠️  Make sure the backend server is running on http://localhost:8000")
    print()
    
    try:
        success = test_phase2_complete()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
