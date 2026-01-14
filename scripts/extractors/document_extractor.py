"""
Document text extraction for simulant information
Supports: PDF, DOCX, HTML files
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import PyPDF2
import pdfplumber
from bs4 import BeautifulSoup

# Try to import python-docx
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not installed. DOCX files will be skipped.")


class DocumentExtractor:
    """Extract text from various document formats"""

    # Directories to exclude from scanning
    EXCLUDE_DIRS = {'.venv', 'venv', '__pycache__', 'node_modules', '.git', 'site-packages'}

    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def find_documents(self) -> List[Path]:
        """Find all supported documents (PDF, DOCX, HTML) excluding venv dirs"""
        if not self.directory.exists():
            print(f"⚠️  Directory not found: {self.directory}")
            return []

        documents = []
        extensions = {'.pdf', '.docx', '.doc', '.html', '.htm'}

        for root, dirs, files in os.walk(self.directory):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

            for file in files:
                if Path(file).suffix.lower() in extensions:
                    documents.append(Path(root) / file)

        # Group by type for reporting
        pdf_count = len([d for d in documents if d.suffix.lower() == '.pdf'])
        docx_count = len([d for d in documents if d.suffix.lower() in {'.docx', '.doc'}])
        html_count = len([d for d in documents if d.suffix.lower() in {'.html', '.htm'}])

        print(f"📄 Found {len(documents)} documents: {pdf_count} PDFs, {docx_count} DOCX, {html_count} HTML")
        return documents

    def extract_text_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                    text += "\n"
                return text.strip()
        except Exception:
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()
            except Exception as e:
                print(f"⚠️  Failed to extract PDF {file_path.name}: {e}")
                return ""

    def extract_text_docx(self, file_path: Path) -> str:
        """Extract text from DOCX"""
        if not DOCX_AVAILABLE:
            return ""

        try:
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs]
            return "\n".join(paragraphs)
        except Exception as e:
            print(f"⚠️  Failed to extract DOCX {file_path.name}: {e}")
            return ""

    def extract_text_html(self, file_path: Path) -> str:
        """Extract text from HTML"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text()
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                return '\n'.join(line for line in lines if line)
        except Exception as e:
            print(f"⚠️  Failed to extract HTML {file_path.name}: {e}")
            return ""

    def extract_text(self, file_path: Path) -> str:
        """Extract text from any supported document type"""
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return self.extract_text_pdf(file_path)
        elif suffix in {'.docx', '.doc'}:
            return self.extract_text_docx(file_path)
        elif suffix in {'.html', '.htm'}:
            return self.extract_text_html(file_path)
        else:
            return ""

    def search_for_simulant(self, simulant_name: str, context_size: int = 4000) -> List[Dict[str, str]]:
        """
        Search all documents for mentions of a specific simulant
        Returns list of {source, file_path, text, source_type}
        """
        documents = self.find_documents()
        results = []

        for doc_path in documents:
            text = self.extract_text(doc_path)

            if simulant_name.lower() in text.lower():
                excerpts = self._extract_context(text, simulant_name, context_size)

                doc_type = doc_path.suffix.lower().replace('.', '').upper()
                for excerpt in excerpts:
                    results.append({
                        "source": f"{doc_type}: {doc_path.name}",
                        "file_path": str(doc_path),
                        "text": excerpt,
                        "source_type": doc_type.lower()
                    })

        print(f"   Found {len(results)} document excerpts mentioning '{simulant_name}'")
        return results

    def _extract_context(self, text: str, keyword: str, context_size: int = 4000) -> List[str]:
        """Extract text around keyword mentions"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        excerpts = []

        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break

            excerpt_start = max(0, pos - context_size // 2)
            excerpt_end = min(len(text), pos + context_size // 2)
            excerpt = text[excerpt_start:excerpt_end]

            excerpts.append(excerpt)
            start = pos + len(keyword_lower)

        return excerpts


# Keep backward compatibility with old name
PDFExtractor = DocumentExtractor


if __name__ == "__main__":
    from config import PDF_DIRECTORY
    extractor = DocumentExtractor(PDF_DIRECTORY)
    docs = extractor.find_documents()
    print(f"\nFound {len(docs)} total documents")
