# DocForge Phase 4 - Manual Testing Guide

This guide provides step-by-step instructions for manually testing Phase 4 features.

---

## Prerequisites

### 1. Start Backend
```powershell
# Option 1: Use the startup script
.\start_backend.ps1

# Option 2: Manual start
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Verify backend is running:
- Open: http://localhost:8000/docs
- You should see the FastAPI interactive documentation

### 2. Start Frontend
```powershell
cd frontend
npm run dev
```

Verify frontend is running:
- Open: http://localhost:5173
- You should see the DocForge application

### 3. Login or Register
- If you don't have an account, register a new user
- Login to access the application

---

## Test Scenario 1: File Upload (All Formats)

### Prepare Test Files

Create sample files in a test folder:

**sample.txt:**
```
This is a sample text file for testing.
It contains multiple lines of text.
Testing knowledge base functionality.
```

**sample.md:**
```markdown
# Sample Markdown Document

## Introduction
This is a markdown file for testing.

## Features
- Bullet points
- Lists
- Formatting

## Conclusion
End of sample document.
```

**sample.html:**
```html
<!DOCTYPE html>
<html>
<head><title>Sample</title></head>
<body>
  <h1>Sample HTML Document</h1>
  <p>This is for testing HTML parsing.</p>
</body>
</html>
```

**sample.csv:**
```csv
Name,Value,Description
Item1,100,First item
Item2,200,Second item
Item3,300,Third item
```

For PDF and DOCX, use any existing files or create new ones with some text content.

### Upload Files

1. Navigate to **Knowledge Base** (or Files page)
2. You should see a file upload area
3. **Test drag-and-drop:**
   - Drag `sample.txt` and drop it
   - Wait for upload to complete
   - Verify file appears in the file list
4. **Test click-to-browse:**
   - Click the upload area
   - Select `sample.md` from file browser
   - Verify upload completes
5. **Repeat for all file types:**
   - Upload sample.html
   - Upload sample.csv
   - Upload sample.pdf (if available)
   - Upload sample.docx (if available)

### Verify Upload Results

For each uploaded file, check:
- ✅ File appears in the list
- ✅ Filename is correct
- ✅ File size is displayed
- ✅ Upload date is shown
- ✅ Status shows "uploaded" or "pending"
- ✅ File type icon is appropriate

### Test Error Cases

1. **Unsupported file type:**
   - Try to upload a .exe or .zip file
   - Expected: Error message "File type not supported"

2. **Oversized file:**
   - If you have a file > 50MB, try to upload it
   - Expected: Error message about file size limit

---

## Test Scenario 2: Text Extraction

For each uploaded file:

1. **Start extraction:**
   - Find the "Extract & Chunk" button next to the file
   - Click it
   - Watch the status update

2. **Wait for processing:**
   - Status should change from "pending" to "processing"
   - Then to "completed" (or "failed" if error)

3. **View extracted content:**
   - Click "View Content" or "Details" button
   - Verify the extracted text is correct:
     - TXT: Should match original text exactly
     - MD: Should include heading markers
     - HTML: Should extract visible text (no tags)
     - CSV: Should include data in readable format
     - PDF: Should extract text from pages
     - DOCX: Should extract document text

4. **Check extraction metadata:**
   - Word count should be reasonable
   - Page count (for PDF) should be correct
   - Chunk count should be > 0

### Expected Results

| File Type | Extraction Result |
|-----------|-------------------|
| TXT | ✅ Exact text match |
| Markdown | ✅ Text with formatting markers |
| HTML | ✅ Text content without tags |
| CSV | ✅ Tabular data as text |
| PDF | ✅ Text from all pages |
| DOCX | ✅ Document text content |

---

## Test Scenario 3: Knowledge Base Search

### Basic Search

1. Go to Knowledge Base page
2. Find the search bar
3. **Test Query 1:** Enter "sample"
   - Should return all files containing "sample"
   - Check that results are ranked by relevance
4. **Test Query 2:** Enter "testing"
   - Should return files with "testing" in content
5. **Test Query 3:** Enter a unique word from one file
   - Should return only that file

### Advanced Search

1. **Multi-word search:** "sample document"
   - Should find files with both words
2. **Phrase search:** Try specific phrases from your files
3. **No results:** Search for "xyznonexistent123"
   - Should show "No results found" message

### Verify Search Results

For each result:
- ✅ Filename displayed
- ✅ Relevance score or ranking
- ✅ Snippet showing matched text
- ✅ Matched terms highlighted
- ✅ Click to view full content works

---

## Test Scenario 4: Document Brief with Attachments

### Create New Brief with Attachments

1. **Navigate to Document Briefs**
2. **Click "New Document Brief"**
3. **Fill in basic details:**
   - Title: "Technical Report with References"
   - Purpose: "Create a technical report using uploaded sources"
   - Audience: "Technical team"
   - Document type: "Report"

4. **Attach reference files:**
   - Navigate to the "Reference Files" step
   - You should see a list of your uploaded files
   - Select 2-3 files (e.g., sample.md, sample.txt, sample.csv)
   - Verify selected files are highlighted
   - Complete the wizard

5. **View the brief:**
   - Open the created brief
   - Verify attached files are listed
   - Check that file names and metadata are shown

### Manage Attachments

1. **Add more files:**
   - Edit the brief
   - Attach additional files
   - Save and verify

2. **Remove files:**
   - Click remove (X) button on an attached file
   - Verify file is removed from the brief
   - Original file should still exist in knowledge base

---

## Test Scenario 5: Generate Document from Brief with Sources

This is the most important Phase 4 test!

### Setup

1. Create or open a brief with 2-3 attached files
2. Ensure attached files have meaningful content
3. Make sure the brief has clear requirements

### Generate Outline

1. Click "Generate Outline"
2. Wait for AI to generate outline
3. Review the outline structure
4. **Check if outline references sources** (implementation dependent)

### Approve and Generate Document

1. Approve the outline (or edit first if needed)
2. Click "Generate Full Document"
3. Wait for generation (this may take longer with sources)
4. Review the generated document

### Verify Source Integration

Check the generated document for:
- ✅ Content that appears to come from attached files
- ✅ References to source information
- ✅ Source citations (e.g., [1], footnotes, or inline citations) **if implemented**
- ✅ Coherent integration of source material
- ✅ Document doesn't just copy-paste, but synthesizes information

### Compare with Non-Source Generation

1. Create another brief WITHOUT attachments
2. Generate a document
3. Compare quality and content with source-based document
4. Source-based document should be more detailed/accurate

---

## Test Scenario 6: Regression Tests

### Phase 1 Features (Basic Document Editing)

1. **Create simple document:**
   - Go to Documents
   - Create new document (not from brief)
   - Add title and content
   - Save
   - ✅ Document created

2. **Edit document:**
   - Open document
   - Edit in Tiptap editor
   - Add formatting (bold, lists, headings)
   - Save changes
   - ✅ Changes persist

3. **Export documents:**
   - Export to DOCX → ✅ Open in Word, verify formatting
   - Export to PDF → ✅ Open in PDF reader, verify content
   - Export to Markdown → ✅ Open in text editor, verify syntax

### Phase 2 Features (Authentication & Conversations)

1. **User authentication:**
   - Logout
   - Login again
   - ✅ Session maintained
   - ✅ User data loads correctly

2. **Create conversation:**
   - Go to chat/conversations
   - Start new conversation
   - Send messages
   - ✅ AI responds appropriately

3. **Data isolation:**
   - Note your current user's documents
   - Logout
   - Register/login as different user
   - ✅ New user sees only their own data
   - ✅ Cannot access first user's documents

### Phase 3 Features (Document Briefs)

1. **Create brief without sources:**
   - Create new brief
   - Don't attach any files
   - Complete wizard
   - ✅ Brief created successfully

2. **Generate from brief:**
   - Generate outline
   - Approve
   - Generate document
   - ✅ Document generation works as before

3. **Edit brief:**
   - Edit brief title and details
   - Save changes
   - ✅ Changes persist

---

## Browser Console Checks

While testing, keep browser DevTools open (F12):

### Check for Errors

Monitor the **Console** tab:
- ❌ Red errors indicate problems
- ⚠️ Yellow warnings may be acceptable
- Look specifically for:
  - API call failures
  - Component rendering errors
  - Network errors
  - Authentication issues

### Check Network Requests

Monitor the **Network** tab:
- File uploads should show progress
- API calls should return 200/201 status
- Check response data is correct
- Watch for 401 (auth) or 403 (forbidden) errors

---

## Backend Log Checks

Monitor the terminal where backend is running:

### Look for:
- ✅ Successful API requests (200, 201 status codes)
- ✅ File upload processing logs
- ✅ Extraction processing logs
- ✅ Search query logs
- ❌ Error stack traces (investigate if found)
- ❌ Database errors
- ❌ AI provider errors

### Example Good Logs:
```
INFO:     127.0.0.1:xxxxx - "POST /api/knowledge/upload HTTP/1.1" 201
INFO:     127.0.0.1:xxxxx - "GET /api/knowledge/files HTTP/1.1" 200
INFO:     File uploaded: sample.txt
INFO:     Extraction started for file: abc123
```

---

## Common Issues and Solutions

### Issue: File Upload Fails
**Check:**
- File size < 50MB
- File type is supported (.pdf, .docx, .txt, .md, .html, .csv)
- Backend is running
- Check browser console for errors

### Issue: Extraction Fails
**Check:**
- File is not corrupted
- Required libraries installed (pypdf, python-docx, beautifulsoup4)
- Check backend logs for error details
- Try with a simple .txt file first

### Issue: Search Returns No Results
**Check:**
- Files have been extracted (status = "completed")
- FTS5 index is populated
- Try simple one-word queries first
- Check backend logs for search query processing

### Issue: Cannot Attach Files to Brief
**Check:**
- Files exist in knowledge base
- Files have been extracted successfully
- Brief is saved before attaching files
- Check browser console for API errors

### Issue: Source Integration Not Working
**Check:**
- Files are actually attached to the brief
- Files contain meaningful content
- AI provider is configured correctly
- Check AI provider has context length for sources
- Review backend logs for AI generation requests

---

## Test Results Checklist

After completing all tests, fill this out:

### Phase 4 Features
- [ ] Upload TXT file - works
- [ ] Upload Markdown file - works
- [ ] Upload HTML file - works
- [ ] Upload CSV file - works
- [ ] Upload PDF file - works
- [ ] Upload DOCX file - works
- [ ] Extract text from files - works
- [ ] View extracted content - works
- [ ] Search knowledge base - works
- [ ] Results ranked correctly - works
- [ ] Attach files to brief - works
- [ ] Remove files from brief - works
- [ ] Generate with sources - works
- [ ] Source content integrated - works
- [ ] Source citations present - works (if implemented)

### Regression Tests
- [ ] Create document (Phase 1) - works
- [ ] Edit document (Phase 1) - works
- [ ] Export DOCX (Phase 1) - works
- [ ] Export PDF (Phase 1) - works
- [ ] Export Markdown (Phase 1) - works
- [ ] User login (Phase 2) - works
- [ ] Conversations (Phase 2) - works
- [ ] Data isolation (Phase 2) - works
- [ ] Create brief (Phase 3) - works
- [ ] Generate outline (Phase 3) - works
- [ ] Generate document (Phase 3) - works

### Overall Quality
- [ ] No console errors during normal use
- [ ] UI is responsive and intuitive
- [ ] Loading states are clear
- [ ] Error messages are helpful
- [ ] Performance is acceptable
- [ ] Features work as documented

---

## Reporting Issues

If you find any issues during testing:

1. **Note the exact steps to reproduce**
2. **Capture error messages** (browser console and backend logs)
3. **Take screenshots** if UI issues
4. **Document expected vs actual behavior**
5. **Check if issue is blocking or minor**

---

## Success Criteria

Phase 4 testing is successful if:

✅ All file formats upload correctly
✅ Text extraction works for all formats
✅ Search returns relevant results
✅ Files can be attached to briefs
✅ Document generation uses source content
✅ All Phase 1-3 features still work
✅ No critical errors in console or logs
✅ UI is usable and intuitive

---

**Happy Testing!** 🎉

If you complete all tests successfully, Phase 4 is ready for acceptance!
