"""Text extraction service for various document formats."""
import csv
import io
from typing import Optional, Dict, Any
from pathlib import Path
import re

# PDF extraction
try:
    from PyPDF2 import PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# DOCX extraction
try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# HTML extraction
try:
    from bs4 import BeautifulSoup
    HAS_HTML = True
except ImportError:
    HAS_HTML = False


class ExtractionResult:
    """Result of text extraction."""
    
    def __init__(
        self,
        text: str,
        word_count: int,
        page_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.word_count = word_count
        self.page_count = page_count
        self.metadata = metadata or {}


class ExtractionService:
    """Service for extracting text from various file formats."""
    
    def __init__(self):
        self.extractors = {
            'pdf': self._extract_pdf,
            'docx': self._extract_docx,
            'txt': self._extract_txt,
            'md': self._extract_markdown,
            'html': self._extract_html,
            'csv': self._extract_csv,
        }
    
    async def extract(self, file_data: bytes, file_extension: str) -> ExtractionResult:
        """
        Extract text from file data.
        
        Args:
            file_data: File bytes
            file_extension: File extension (without dot)
            
        Returns:
            ExtractionResult with text and metadata
            
        Raises:
            ValueError: If format not supported
            Exception: If extraction fails
        """
        file_extension = file_extension.lower().strip('.')
        
        if file_extension not in self.extractors:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        extractor = self.extractors[file_extension]
        return await extractor(file_data)
    
    async def _extract_pdf(self, file_data: bytes) -> ExtractionResult:
        """Extract text from PDF."""
        if not HAS_PDF:
            raise Exception("PyPDF2 not installed")
        
        try:
            pdf_file = io.BytesIO(file_data)
            reader = PdfReader(pdf_file)
            
            pages = []
            page_texts = []
            
            for i, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append(i)
                        page_texts.append(f"[Page {i}]\n{text}\n")
                except Exception:
                    # Skip pages that fail to extract
                    continue
            
            full_text = "\n".join(page_texts)
            
            if not full_text.strip():
                raise Exception("No text could be extracted from PDF (may be scanned/image-based)")
            
            word_count = len(full_text.split())
            
            return ExtractionResult(
                text=full_text,
                word_count=word_count,
                page_count=len(reader.pages),
                metadata={
                    'pages_with_text': pages,
                    'total_pages': len(reader.pages),
                    'extraction_method': 'PyPDF2'
                }
            )
            
        except Exception as e:
            raise Exception(f"Failed to extract PDF: {str(e)}")
    
    async def _extract_docx(self, file_data: bytes) -> ExtractionResult:
        """Extract text from DOCX."""
        if not HAS_DOCX:
            raise Exception("python-docx not installed")
        
        try:
            docx_file = io.BytesIO(file_data)
            doc = DocxDocument(docx_file)
            
            paragraphs = []
            headings = []
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    # Check if it's a heading
                    if para.style.name.startswith('Heading'):
                        headings.append(text)
                        paragraphs.append(f"\n## {text}\n")
                    else:
                        paragraphs.append(text)
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        paragraphs.append(row_text)
            
            full_text = "\n\n".join(paragraphs)
            
            if not full_text.strip():
                raise Exception("No text found in DOCX file")
            
            word_count = len(full_text.split())
            
            return ExtractionResult(
                text=full_text,
                word_count=word_count,
                metadata={
                    'paragraph_count': len(doc.paragraphs),
                    'heading_count': len(headings),
                    'table_count': len(doc.tables),
                    'headings': headings[:10],  # First 10 headings
                    'extraction_method': 'python-docx'
                }
            )
            
        except Exception as e:
            raise Exception(f"Failed to extract DOCX: {str(e)}")
    
    async def _extract_txt(self, file_data: bytes) -> ExtractionResult:
        """Extract text from plain text file."""
        try:
            # Try UTF-8 first
            try:
                text = file_data.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to latin-1
                text = file_data.decode('latin-1')
            
            if not text.strip():
                raise Exception("Text file is empty")
            
            word_count = len(text.split())
            line_count = len(text.splitlines())
            
            return ExtractionResult(
                text=text,
                word_count=word_count,
                metadata={
                    'line_count': line_count,
                    'encoding': 'utf-8',
                    'extraction_method': 'direct'
                }
            )
            
        except Exception as e:
            raise Exception(f"Failed to extract text: {str(e)}")
    
    async def _extract_markdown(self, file_data: bytes) -> ExtractionResult:
        """Extract text from Markdown file."""
        try:
            # Decode markdown
            try:
                text = file_data.decode('utf-8')
            except UnicodeDecodeError:
                text = file_data.decode('latin-1')
            
            if not text.strip():
                raise Exception("Markdown file is empty")
            
            # Extract headings for metadata
            headings = re.findall(r'^#{1,6}\s+(.+)$', text, re.MULTILINE)
            
            word_count = len(text.split())
            
            return ExtractionResult(
                text=text,
                word_count=word_count,
                metadata={
                    'heading_count': len(headings),
                    'headings': headings[:10],  # First 10 headings
                    'extraction_method': 'direct',
                    'format': 'markdown'
                }
            )
            
        except Exception as e:
            raise Exception(f"Failed to extract markdown: {str(e)}")
    
    async def _extract_html(self, file_data: bytes) -> ExtractionResult:
        """Extract text from HTML file."""
        if not HAS_HTML:
            raise Exception("beautifulsoup4 not installed")
        
        try:
            # Decode HTML
            try:
                html = file_data.decode('utf-8')
            except UnicodeDecodeError:
                html = file_data.decode('latin-1')
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # Extract headings
            headings = []
            for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = tag.get_text().strip()
                if heading_text:
                    headings.append(heading_text)
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            if not text.strip():
                raise Exception("No text found in HTML file")
            
            word_count = len(text.split())
            
            return ExtractionResult(
                text=text,
                word_count=word_count,
                metadata={
                    'heading_count': len(headings),
                    'headings': headings[:10],
                    'extraction_method': 'beautifulsoup4'
                }
            )
            
        except Exception as e:
            raise Exception(f"Failed to extract HTML: {str(e)}")
    
    async def _extract_csv(self, file_data: bytes) -> ExtractionResult:
        """Extract text from CSV file."""
        try:
            # Decode CSV
            try:
                csv_text = file_data.decode('utf-8')
            except UnicodeDecodeError:
                csv_text = file_data.decode('latin-1')
            
            # Parse CSV
            csv_file = io.StringIO(csv_text)
            reader = csv.reader(csv_file)
            
            rows = list(reader)
            
            if not rows:
                raise Exception("CSV file is empty")
            
            # Format as table-like text
            lines = []
            
            # Assume first row is header
            if rows:
                header = rows[0]
                lines.append("Columns: " + ", ".join(header))
                lines.append("")
                
                # Add data rows
                for i, row in enumerate(rows[1:], 1):
                    row_dict = dict(zip(header, row))
                    row_text = f"Row {i}: " + "; ".join(f"{k}={v}" for k, v in row_dict.items())
                    lines.append(row_text)
            
            text = "\n".join(lines)
            word_count = len(text.split())
            
            return ExtractionResult(
                text=text,
                word_count=word_count,
                metadata={
                    'row_count': len(rows) - 1 if len(rows) > 1 else 0,
                    'column_count': len(rows[0]) if rows else 0,
                    'columns': rows[0] if rows else [],
                    'extraction_method': 'csv'
                }
            )
            
        except Exception as e:
            raise Exception(f"Failed to extract CSV: {str(e)}")


# Global extraction service instance
_extraction_service: Optional[ExtractionService] = None


def get_extraction_service() -> ExtractionService:
    """Get or create global extraction service."""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = ExtractionService()
    return _extraction_service
