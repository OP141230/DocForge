# Phase 2D Testing Instructions

## What Was Implemented

Phase 2D adds conversation and message management backend functionality:

### New Backend Components

1. **ConversationRepository** (`backend/app/repositories/conversation_repository.py`)
   - `create(user_id, title)` - Create new conversation
   - `get_by_id(conversation_id, user_id)` - Get conversation with ownership check
   - `list_by_user(user_id, limit, offset)` - List user's conversations (paginated)
   - `update_title(conversation_id, title, user_id)` - Update conversation title
   - `delete(conversation_id, user_id)` - Delete conversation

2. **MessageRepository** (`backend/app/repositories/message_repository.py`)
   - `create(conversation_id, role, content, sequence_number)` - Create message
   - `list_by_conversation(conversation_id, limit, offset)` - List messages (paginated)
   - `get_latest_sequence(conversation_id)` - Get latest sequence number
   - `delete_by_conversation(conversation_id)` - Delete all messages

3. **API Routes** (`backend/app/api/routes/conversations.py`)
   - `POST /api/conversations` - Create conversation
   - `GET /api/conversations` - List conversations (paginated)
   - `GET /api/conversations/{id}` - Get conversation
   - `PUT /api/conversations/{id}` - Update conversation title
   - `DELETE /api/conversations/{id}` - Delete conversation
   - `POST /api/conversations/{id}/messages` - Add message
   - `GET /api/conversations/{id}/messages` - List messages (paginated)

4. **Enhanced Documents Route**
   - `POST /api/documents?conversation_id={id}` - Create document linked to conversation

### Key Features

- **Authentication Required**: All endpoints require valid session token
- **Ownership Verification**: Users can only access their own conversations/messages
- **Auto-Sequencing**: Message sequence numbers are auto-calculated server-side
- **Pagination**: List endpoints support limit/offset parameters
- **Access Control**: Returns 404 for unauthorized access (not 403)
- **Database Integration**: Uses existing SQLite schema with proper foreign keys

## How to Test

### Prerequisites

Backend must be running on http://localhost:8000

### Start Backend Server

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Run Automated Test Script

In a separate terminal:

```powershell
cd c:\Users\om141\OneDrive\Desktop\PROJECTS\DocForge
python test_conversations.py
```

### What the Test Script Does

1. ✅ Registers first test user
2. ✅ Logs in first user
3. ✅ Creates a conversation
4. ✅ Lists conversations
5. ✅ Gets conversation by ID
6. ✅ Adds messages to conversation
7. ✅ Lists messages
8. ✅ Updates conversation title
9. ✅ Registers and logs in second user
10. ✅ Verifies second user CANNOT access first user's conversation (404)
11. ✅ Deletes conversation
12. ✅ Verifies deletion (404)
13. ✅ Creates conversation with default title

### Expected Results

All steps should show:
- ✅ Green checkmarks for successful operations
- Status 201 for creates
- Status 200 for gets/lists/updates
- Status 204 for deletes
- Status 404 for unauthorized access and deleted resources

### Manual Testing via API Docs

1. Navigate to http://localhost:8000/docs
2. Use the interactive API documentation
3. First call `/api/auth/register` and `/api/auth/login`
4. Click "Authorize" and add session token from login response
5. Test conversation endpoints

### Pytest Tests

```powershell
cd backend
pytest app/tests/ -v
```

**Result**: All 4 existing tests pass ✅

## Architecture Patterns Followed

✅ **Async/await** for all database operations
✅ **Repository pattern** matching DocumentRepository
✅ **Ownership filtering** via user_id in queries
✅ **Return 404** for not found/unauthorized (consistency)
✅ **Pydantic models** from app.models.auth
✅ **Session-based auth** via get_current_user dependency
✅ **Database connections** via await get_database()
✅ **Proper indexing** using existing database schema
✅ **Foreign key constraints** with CASCADE/SET NULL
✅ **Pagination support** with total count

## Files Modified/Created

### Created
- `backend/app/repositories/conversation_repository.py`
- `backend/app/repositories/message_repository.py`
- `backend/app/api/routes/conversations.py`
- `test_conversations.py`

### Modified
- `backend/main.py` - Registered conversations router
- `backend/app/api/routes/documents.py` - Added conversation_id parameter
- `backend/app/tests/conftest.py` - Added conversation_repo and message_repo fixtures

## Database Schema (Already Exists)

```sql
-- Conversations
conversations (id, user_id FK, title, created_at, updated_at)
INDEX: user_id, updated_at DESC

-- Messages
messages (id, conversation_id FK, role, content, sequence_number, created_at, updated_at, is_deleted)
INDEX: conversation_id, sequence_number

-- Documents (already had these fields)
documents.user_id FK → CASCADE
documents.conversation_id FK → SET NULL
```

## Known Limitations

1. Message role is currently hardcoded to 'user' in POST /messages endpoint
   - Future: Add role parameter to support 'assistant' messages
2. Soft delete (is_deleted flag) implemented in queries but no route to soft-delete yet
3. No message editing/updating endpoint yet (only create/list)
4. No conversation search/filter functionality yet

## Next Steps

After verifying Phase 2D works correctly:

1. Start backend server
2. Run test script: `python test_conversations.py`
3. Verify all tests pass with green checkmarks
4. Check for any errors in console
5. Optionally test via http://localhost:8000/docs
6. Continue to Phase 2E (if planned) or frontend integration

## Commit Information

```
Commit: feat: implement conversation and message management backend (Phase 2D)
Files: 7 changed, 703 insertions(+)
Tests: All pytest tests pass (4/4)
```
