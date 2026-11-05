"""Test authentication endpoints."""
import asyncio
import httpx


BASE_URL = "http://localhost:8000"


async def test_auth_flow():
    """Test complete authentication flow."""
    print("🧪 Testing Authentication Flow\n")
    
    async with httpx.AsyncClient() as client:
        # Test 1: Register
        print("1. Testing registration...")
        register_data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/auth/register", json=register_data)
            if response.status_code == 201:
                print("   ✅ Registration successful")
                user_data = response.json()
                print(f"   User: {user_data['full_name']} ({user_data['email']})")
            else:
                print(f"   ❌ Registration failed: {response.text}")
                return
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
        
        print()
        
        # Test 2: Login
        print("2. Testing login...")
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/auth/login", json=login_data)
            if response.status_code == 200:
                print("   ✅ Login successful")
                cookies = response.cookies
                print(f"   Session cookie: {'session_token' in cookies}")
            else:
                print(f"   ❌ Login failed: {response.text}")
                return
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
        
        print()
        
        # Test 3: Get current user
        print("3. Testing /auth/me (with session)...")
        try:
            response = await client.get(
                f"{BASE_URL}/api/auth/me",
                cookies={"session_token": cookies.get("session_token")}
            )
            if response.status_code == 200:
                print("   ✅ Successfully retrieved current user")
                user_data = response.json()
                print(f"   User: {user_data['full_name']} ({user_data['email']})")
            else:
                print(f"   ❌ Failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 4: Get current user without session
        print("4. Testing /auth/me (without session)...")
        try:
            response = await client.get(f"{BASE_URL}/api/auth/me")
            if response.status_code == 401:
                print("   ✅ Correctly rejected unauthenticated request")
            else:
                print(f"   ❌ Should have returned 401, got {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 5: Logout
        print("5. Testing logout...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/logout",
                cookies={"session_token": cookies.get("session_token")}
            )
            if response.status_code == 200:
                print("   ✅ Logout successful")
            else:
                print(f"   ❌ Logout failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 6: Verify session is invalidated
        print("6. Testing /auth/me after logout...")
        try:
            response = await client.get(
                f"{BASE_URL}/api/auth/me",
                cookies={"session_token": cookies.get("session_token")}
            )
            if response.status_code == 401:
                print("   ✅ Session correctly invalidated")
            else:
                print(f"   ❌ Session should be invalid, got {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ Authentication tests complete!")


if __name__ == "__main__":
    print("Make sure backend is running on http://localhost:8000")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    input()
    asyncio.run(test_auth_flow())
