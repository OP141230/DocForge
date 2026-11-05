"""Test script for Phase 2C - User data isolation."""
import http.client
import json
from datetime import datetime


BASE_URL = "localhost:8000"
BASE_PATH = "/api"


def make_request(path, method="GET", data=None, cookies=None):
    """Make an HTTP request with optional cookies."""
    conn = http.client.HTTPConnection(BASE_URL)
    
    headers = {"Content-Type": "application/json"}
    
    # Add Cookie header if cookies provided
    if cookies:
        cookie_str = "; ".join([f"{name}={value}" for name, value in cookies.items()])
        headers["Cookie"] = cookie_str
    
    # Prepare request
    body = json.dumps(data) if data else None
    
    try:
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        
        # Read response body
        response_data = None
        if response.status != 204:  # No content
            try:
                response_data = json.loads(response.read().decode('utf-8'))
            except:
                pass
        
        # Extract cookies from Set-Cookie headers
        response_cookies = {}
        set_cookie = response.getheader('Set-Cookie')
        if set_cookie:
            # Parse session_token from Set-Cookie header
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
        print(f"Request error: {e}")
        raise


def test_data_isolation():
    """Test that users can only access their own documents."""
    print("=" * 70)
    print("DocForge Phase 2C - Data Isolation Test")
    print("=" * 70)
    print()
    
    # Test 1: Register two users
    print("📝 Test 1: Register two users")
    print("-" * 70)
    
    user1_data = {
        "full_name": "Alice Johnson",
        "email": f"alice_{int(datetime.now().timestamp())}@test.com",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!"
    }
    
    user2_data = {
        "full_name": "Bob Smith",
        "email": f"bob_{int(datetime.now().timestamp())}@test.com",
        "password": "SecurePass456!",
        "confirm_password": "SecurePass456!"
    }
    
    status, user1, cookies1 = make_request(f"{BASE_PATH}/auth/register", "POST", user1_data)
    if status != 201:
        print(f"❌ Failed to register User 1: Status {status}")
        return
    user1_cookie = cookies1.get("session_token")
    if not user1_cookie:
        print("❌ No session cookie returned for User 1")
        return
    print(f"✅ User 1 registered: {user1['email']}")
    
    status, user2, cookies2 = make_request(f"{BASE_PATH}/auth/register", "POST", user2_data)
    if status != 201:
        print(f"❌ Failed to register User 2: Status {status}")
        return
    user2_cookie = cookies2.get("session_token")
    if not user2_cookie:
        print("❌ No session cookie returned for User 2")
        return
    print(f"✅ User 2 registered: {user2['email']}")
    
    print()
    
    # Test 2: User 1 creates a document
    print("📝 Test 2: User 1 creates a document")
    print("-" * 70)
    
    doc1 = {
        "id": f"doc1_{int(datetime.now().timestamp())}",
        "title": "Alice's Private Document",
        "content": [
            {
                "id": "sec1",
                "title": "Secret Section",
                "level": 2,
                "blocks": [
                    {
                        "id": "p1",
                        "type": "paragraph",
                        "content": [{"text": "This is Alice's confidential content.", "bold": False, "italic": False, "underline": False}]
                    }
                ]
            }
        ],
        "metadata": {
            "author": "Alice",
            "document_type": "general_report",
            "language": "en"
        }
    }
    
    status, created_doc1, _ = make_request(f"{BASE_PATH}/documents", "POST", doc1, {"session_token": user1_cookie})
    if status != 201:
        print(f"❌ Failed to create document: Status {status}")
        return
    doc1_id = created_doc1["id"]
    print(f"✅ User 1 created document: {doc1_id}")
    print(f"   Title: {created_doc1['title']}")
    
    print()
    
    # Test 3: User 2 creates a document
    print("📝 Test 3: User 2 creates a document")
    print("-" * 70)
    
    doc2 = {
        "id": f"doc2_{int(datetime.now().timestamp())}",
        "title": "Bob's Private Document",
        "content": [
            {
                "id": "sec2",
                "title": "Bob's Section",
                "level": 2,
                "blocks": [
                    {
                        "id": "p2",
                        "type": "paragraph",
                        "content": [{"text": "This is Bob's confidential content.", "bold": False, "italic": False, "underline": False}]
                    }
                ]
            }
        ],
        "metadata": {
            "author": "Bob",
            "document_type": "general_report",
            "language": "en"
        }
    }
    
    status, created_doc2, _ = make_request(f"{BASE_PATH}/documents", "POST", doc2, {"session_token": user2_cookie})
    if status != 201:
        print(f"❌ Failed to create document: Status {status}")
        return
    doc2_id = created_doc2["id"]
    print(f"✅ User 2 created document: {doc2_id}")
    print(f"   Title: {created_doc2['title']}")
    
    print()
    
    # Test 4: User 1 lists documents (should only see their own)
    print("📝 Test 4: User 1 lists documents")
    print("-" * 70)
    
    status, result, _ = make_request(f"{BASE_PATH}/documents", "GET", cookies={"session_token": user1_cookie})
    if status != 200:
        print(f"❌ Failed to list documents: Status {status}")
        return
    docs = result["documents"]
    print(f"✅ User 1 sees {len(docs)} document(s)")
    for doc in docs:
        print(f"   - {doc['title']} (ID: {doc['id']})")
    
    # Check isolation
    doc_ids = [d["id"] for d in docs]
    if doc1_id in doc_ids and doc2_id not in doc_ids:
        print("✅ PASS: User 1 can only see their own documents")
    else:
        print("❌ FAIL: Data isolation breach!")
        return
    
    print()
    
    # Test 5: User 2 lists documents (should only see their own)
    print("📝 Test 5: User 2 lists documents")
    print("-" * 70)
    
    status, result, _ = make_request(f"{BASE_PATH}/documents", "GET", cookies={"session_token": user2_cookie})
    if status != 200:
        print(f"❌ Failed to list documents: Status {status}")
        return
    docs = result["documents"]
    print(f"✅ User 2 sees {len(docs)} document(s)")
    for doc in docs:
        print(f"   - {doc['title']} (ID: {doc['id']})")
    
    # Check isolation
    doc_ids = [d["id"] for d in docs]
    if doc2_id in doc_ids and doc1_id not in doc_ids:
        print("✅ PASS: User 2 can only see their own documents")
    else:
        print("❌ FAIL: Data isolation breach!")
        return
    
    print()
    
    # Test 6: User 2 tries to access User 1's document (should fail)
    print("📝 Test 6: User 2 tries to access User 1's document")
    print("-" * 70)
    
    status, _, _ = make_request(f"{BASE_PATH}/documents/{doc1_id}", "GET", cookies={"session_token": user2_cookie})
    if status == 404:
        print("✅ PASS: User 2 cannot access User 1's document (404)")
    else:
        print(f"❌ FAIL: User 2 accessed User 1's document! Status: {status}")
        return
    
    print()
    
    # Test 7: User 1 tries to delete User 2's document (should fail)
    print("📝 Test 7: User 1 tries to delete User 2's document")
    print("-" * 70)
    
    status, _, _ = make_request(f"{BASE_PATH}/documents/{doc2_id}", "DELETE", cookies={"session_token": user1_cookie})
    if status == 404:
        print("✅ PASS: User 1 cannot delete User 2's document (404)")
    else:
        print(f"❌ FAIL: User 1 deleted User 2's document! Status: {status}")
        return
    
    print()
    
    # Test 8: User 1 can access their own document
    print("📝 Test 8: User 1 accesses their own document")
    print("-" * 70)
    
    status, doc, _ = make_request(f"{BASE_PATH}/documents/{doc1_id}", "GET", cookies={"session_token": user1_cookie})
    if status == 200:
        print(f"✅ PASS: User 1 can access their own document")
        print(f"   Title: {doc['title']}")
    else:
        print(f"❌ FAIL: User 1 cannot access their own document! Status: {status}")
        return
    
    print()
    
    # Test 9: Unauthenticated request (should fail)
    print("📝 Test 9: Unauthenticated request to list documents")
    print("-" * 70)
    
    status, _, _ = make_request(f"{BASE_PATH}/documents", "GET")
    if status == 401:
        print("✅ PASS: Unauthenticated request rejected (401)")
    else:
        print(f"❌ FAIL: Unauthenticated request succeeded! Status: {status}")
        return
    
    print()
    print("=" * 70)
    print("🎉 ALL TESTS PASSED - Data isolation working correctly!")
    print("=" * 70)


if __name__ == "__main__":
    print()
    print("⚠️  Make sure the backend server is running on http://localhost:8000")
    print()
    
    try:
        test_data_isolation()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
