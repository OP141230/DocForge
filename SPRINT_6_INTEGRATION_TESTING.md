# Sprint 6: Knowledge Base Integration - Testing Guide

## Overview
Sprint 6 integrated the knowledge base file attachment functionality into the DocumentBriefWizard and added navigation improvements with Lucide icons.

## Changes Made

### 1. File Attachment in Brief Wizard
- **Location**: `frontend/src/components/DocumentBrief/Step4_DocumentSpecificAndAdditional.tsx`
- **New Component**: `frontend/src/components/DocumentBrief/FileAttachmentSelector.tsx`
- **Features**:
  - File selector integrated into Step 4 of the wizard
  - Shows only processed files (extraction_status === 'completed')
  - Search/filter functionality
  - Visual feedback for attached files
  - Works both before and after brief creation
  - Optional section with helpful tooltips

### 2. API Client Updates
- **Location**: `frontend/src/api/client.ts`
- **New Methods**:
  - `attachFileToBrief(briefId, fileId)` - Attach a file to a brief
  - `getBriefAttachments(briefId)` - Get all attached files for a brief
  - `detachFileFromBrief(briefId, fileId)` - Remove file attachment

### 3. Navigation Improvements
- **Location**: `frontend/src/pages/DashboardPage.tsx`
- **Changes**:
  - Replaced emoji icons with Lucide icons for consistency
  - Icons used: `MessageSquare`, `FileText`, `ClipboardList`, `Library`, `Plus`, `Trash2`
  - Improved visual consistency across the dashboard
  - Better accessibility with aria-labels
  - Knowledge Base tab already present with Library icon

## Integration Testing Checklist

### Prerequisites
- Backend server running
- Frontend development server running
- User account created and logged in
- At least one file uploaded and processed in knowledge base

### Test Case 1: Upload and Process File
**Purpose**: Verify file upload and processing workflow

1. Navigate to Knowledge Base (`/knowledge`)
2. Click "Upload File" button
3. Select a valid file (PDF, DOCX, TXT, etc.)
4. Verify file appears in the list with "Pending" status
5. Click the "Extract & Chunk" button (lightning icon)
6. Wait for processing to complete
7. Verify status changes to "Processed"

**Expected Result**: File is uploaded, processed, and shows "Processed" status

**Error Cases to Test**:
- Upload invalid file type (should show error)
- Upload file larger than 50MB (should show error)
- Upload with no network connection (should show error with retry)

---

### Test Case 2: Search Knowledge Base
**Purpose**: Verify search functionality

1. Navigate to Knowledge Base
2. Enter search term in search bar
3. Press Enter or click "Search"
4. Verify search results appear (currently shows all files - feature in development)

**Expected Result**: Search executes without errors (full functionality pending)

**Note**: Search feature displays a message: "Search feature is under development"

---

### Test Case 3: Navigate to Brief Wizard
**Purpose**: Verify navigation to wizard

1. From Dashboard, click "Document Brief" button
2. Verify wizard opens with Step 1
3. Click through steps 1-3 to reach Step 4

**Expected Result**: Wizard opens smoothly and progresses to Step 4

---

### Test Case 4: Attach Files in Wizard (New Brief)
**Purpose**: Verify file attachment when creating new brief

1. Start new brief wizard
2. Complete Steps 1-3
3. On Step 4, scroll to "Reference Files" section
4. Click "Show Available Files"
5. Verify processed files appear in the list
6. Click on a file to select it
7. Verify file appears in "Attached Files" section with blue highlight
8. Click "Hide Available Files"
9. Verify attached file still shows in the summary

**Expected Result**: Files can be attached and UI reflects selection

---

### Test Case 5: Search Files in Attachment Selector
**Purpose**: Verify search within attachment selector

1. In Step 4 of wizard, expand "Show Available Files"
2. Type file name in search box
3. Verify file list filters based on search term
4. Clear search
5. Verify all files reappear

**Expected Result**: File search works correctly

---

### Test Case 6: Remove Attached File
**Purpose**: Verify file can be detached

1. With a file attached in Step 4
2. Click the X button next to the attached file
3. Verify file is removed from "Attached Files" section
4. Verify file checkbox is unchecked in available files list
5. Re-attach the file
6. Verify it reappears correctly

**Expected Result**: Files can be attached and detached smoothly

---

### Test Case 7: Multiple File Attachments
**Purpose**: Verify multiple files can be attached

1. In Step 4, expand available files
2. Select 3-5 different files
3. Verify all appear in "Attached Files" section
4. Verify count shows correctly (e.g., "Attached Files (5)")
5. Remove one file
6. Verify count updates

**Expected Result**: Multiple files can be attached simultaneously

---

### Test Case 8: Brief Auto-Save with Attachments
**Purpose**: Verify attachments persist through auto-save

1. Create new brief and reach Step 4
2. Attach 2-3 files
3. Wait for auto-save indicator ("Draft saved automatically")
4. Navigate to Step 5 (Review)
5. Go back to Step 4
6. Verify attached files are still present

**Expected Result**: Attachments persist through wizard navigation

---

### Test Case 9: Resume Existing Brief with Attachments
**Purpose**: Verify attachments load when reopening a brief

1. Create brief with attached files through to Step 5
2. Close wizard
3. Navigate to Brief Manager
4. Open the same brief
5. Go to Step 4
6. Verify attached files load correctly

**Expected Result**: Previously attached files appear when brief is reopened

---

### Test Case 10: No Files Available
**Purpose**: Verify graceful handling when no files exist

1. Delete all files from knowledge base (or use fresh account)
2. Open brief wizard to Step 4
3. Expand "Show Available Files"
4. Verify helpful empty state message appears
5. Verify link to upload files is present

**Expected Result**: Clear message about no files with link to knowledge base

---

### Test Case 11: Only Unprocessed Files
**Purpose**: Verify behavior when files exist but aren't processed

1. Upload a file but don't process it
2. Open brief wizard to Step 4
3. Expand available files
4. Verify unprocessed file doesn't appear
5. Verify message about no processed files

**Expected Result**: Only processed files appear in selector

---

### Test Case 12: Generate Document with Attachments
**Purpose**: Verify attached files are used in generation

1. Complete brief wizard with attached files
2. Generate outline in Step 6
3. Approve outline
4. Generate document
5. Check if document content references attached file information

**Expected Result**: Document generation completes (content relevance requires manual review)

**Note**: Backend should pass attached files to retrieval service for context

---

### Test Case 13: Navigation Icons
**Purpose**: Verify improved navigation icons

1. Navigate to Dashboard
2. Verify tab icons appear correctly:
   - Conversations: Message icon
   - Documents: File icon
   - Briefs: Clipboard icon
   - Knowledge: Library icon
3. Verify icons are consistent and not emoji
4. Click each tab and verify icons remain visible

**Expected Result**: All icons render as Lucide React icons (not emoji)

---

### Test Case 14: View File Content from Knowledge Base
**Purpose**: Verify file preview works

1. Navigate to Knowledge Base
2. Click "View content" button (eye icon) on a processed file
3. Verify modal opens with file content
4. Verify content is readable
5. Close modal

**Expected Result**: File content displays correctly in modal

---

### Test Case 15: Delete File with Attachments
**Purpose**: Verify attachment handling when file is deleted

1. Attach a file to a brief
2. Navigate to Knowledge Base
3. Delete the attached file
4. Return to brief
5. Go to Step 4
6. Verify deleted file no longer appears in attached files

**Expected Result**: Deleted files are removed from attachment lists

**Note**: This requires backend cascade deletion or orphan handling

---

### Test Case 16: Responsive Design
**Purpose**: Verify UI works on different screen sizes

1. Open brief wizard to Step 4
2. Resize browser window to mobile size (< 640px)
3. Verify file selector remains usable
4. Verify attached files display properly
5. Test tablet size (768px - 1024px)

**Expected Result**: UI adapts gracefully to different screen sizes

---

### Test Case 17: Loading States
**Purpose**: Verify loading indicators work correctly

1. Open brief wizard to Step 4 with slow network
2. Verify loading spinner appears while files load
3. Verify loading message is clear
4. After files load, verify loading state clears

**Expected Result**: Loading states display during async operations

---

### Test Case 18: Error Handling in Attachment
**Purpose**: Verify error messages display correctly

1. Simulate network error (disable internet)
2. Try to attach a file
3. Verify error message appears
4. Reconnect network
5. Retry attachment
6. Verify success

**Expected Result**: Clear error messages with ability to retry

---

### Test Case 19: Tooltips and Help Text
**Purpose**: Verify helpful guidance is present

1. In Step 4, hover over the info icon (ⓘ) next to "Reference Files"
2. Verify tooltip appears with explanation
3. Verify tooltip is readable and helpful
4. Check other tooltips in the wizard

**Expected Result**: Tooltips provide clear, helpful information

---

### Test Case 20: Accessibility
**Purpose**: Verify keyboard and screen reader support

1. Use Tab key to navigate through Step 4
2. Verify all interactive elements are reachable
3. Verify focused elements have visible focus indicators
4. Test with screen reader (if available)
5. Verify aria-labels are present on icon buttons

**Expected Result**: Wizard is keyboard-accessible with proper focus management

---

## Known Limitations

1. **Search Functionality**: Basic filename search only (no full-text search in wizard)
2. **File Preview**: Cannot preview files directly from attachment selector
3. **Bulk Operations**: No "attach all" or "clear all" functionality
4. **File Status Refresh**: Manual refresh needed to see processing status updates
5. **Attachment Limits**: No UI enforcement of maximum number of attachments

## Environment Prerequisites

1. **Backend**:
   - Python 3.8+
   - All dependencies installed (`pip install -r requirements.txt`)
   - Database migrated with Sprint 5 schema
   - Storage directory configured

2. **Frontend**:
   - Node.js 16+
   - Dependencies installed (`npm install`)
   - Environment variable `VITE_API_BASE_URL` set correctly

3. **Database**:
   - Tables: `knowledge_files`, `extracted_content`, `content_chunks`, `brief_file_attachments`
   - Indexes created for performance

## Manual UI Checks

### Visual Polish
- [ ] File icons display correctly for each file type
- [ ] Colors are consistent with DocForge theme (blue primary)
- [ ] Spacing and padding are balanced
- [ ] Loading spinners are centered and smooth
- [ ] Empty states have helpful imagery
- [ ] Error messages are clearly visible (red theme)
- [ ] Success states are affirming (green/blue theme)

### Interaction Polish
- [ ] Buttons have hover states
- [ ] Click areas are adequately sized (minimum 44x44px)
- [ ] Transitions are smooth (not jarring)
- [ ] No layout shift when elements load
- [ ] Scrolling is smooth in file list
- [ ] Modal overlays are properly centered

### Information Architecture
- [ ] File attachment section is clearly labeled
- [ ] Optional fields are marked as "(Optional)"
- [ ] Required fields have clear indicators
- [ ] Help text is concise and helpful
- [ ] Navigation between steps is intuitive

## Success Criteria

Sprint 6 is considered complete when:

1. ✅ File attachment functionality works in the wizard
2. ✅ Users can search and filter available files
3. ✅ Attached files persist through wizard navigation
4. ✅ Navigation icons use Lucide React (not emoji)
5. ✅ All CRUD operations for attachments work
6. ✅ Empty states and loading states are polished
7. ✅ Error handling is graceful with clear messages
8. ✅ UI is responsive on mobile, tablet, and desktop
9. ✅ Accessibility standards are met (keyboard navigation, focus indicators)
10. ✅ Integration points with knowledge base API are functional

## Next Steps

After Sprint 6 testing is complete:

1. **Sprint 7**: Backend retrieval service integration
   - Use attached files in document generation
   - Implement relevance scoring
   - Add source citations to generated content

2. **Future Enhancements**:
   - Real-time processing status updates (WebSockets)
   - File preview in attachment selector
   - Drag-and-drop file attachment
   - Attachment analytics (which files are most used)
   - Version control for attached files

---

**Testing Status**: Ready for testing after all sprints complete
**Last Updated**: Sprint 6 Implementation
