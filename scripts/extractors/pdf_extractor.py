"""
PDF text extraction for simulant information
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import PyPDF2
import pdfplumber


class PDFExtractor:
    """Extract text from PDF documents"""

    def __init__(self, pdf_directory: Path):
        self.pdf_directory = Path(pdf_directory)

    def find_pdfs(self) -> List[Path]:
        """Find all PDF files in the directory"""
        if not self.pdf_directory.exists():
            print(f"⚠️  PDF directory not found: {self.pdf_directory}")
            return []

        pdfs = list(self.pdf_directory.rglob("*.pdf"))
        print(f"📄 Found {len(pdfs)} PDF files")
        return pdfs

    def extract_text_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2 (fallback method)"""
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"⚠️  PyPDF2 failed for {pdf_path.name}: {e}")
            return ""

    def extract_text_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber (better quality)"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                    text += "\n"
                return text
        except Exception as e:
            print(f"⚠️  pdfplumber failed for {pdf_path.name}: {e}")
            return ""

    def extract_text(self, pdf_path: Path) -> str:
        """Extract text from PDF (try pdfplumber first, fall back to PyPDF2)"""
        text = self.extract_text_pdfplumber(pdf_path)
        if not text.strip():
            text = self.extract_text_pypdf2(pdf_path)
        return text.strip()

    def search_for_simulant(self, simulant_name: str) -> List[Dict[str, str]]:
        """
        Search PDFs for mentions of a specific simulant
        Returns list of {file, text_excerpt} where simulant is mentioned
        """
        pdfs = self.find_pdfs()
        results = []

        for pdf_path in pdfs:
            text = self.extract_text(pdf_path)

            # Check if simulant is mentioned
            if simulant_name.lower() in text.lower():
                # Extract context around mentions
                excerpts = self._extract_context(text, simulant_name, context_size=4000)

                for excerpt in excerpts:
                    results.append({
                        "source": f"PDF: {pdf_path.name}",
                        "file_path": str(pdf_path),
                        "text": excerpt,
                        "source_type": "pdf"
                    })

        print(f"   Found {len(results)} PDF excerpts mentioning '{simulant_name}'")
        return results

    def _extract_context(self, text: str, keyword: str, context_size: int = 1000) -> List[str]:
        """Extract text around keyword mentions"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        excerpts = []

        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break

            # Extract context
            excerpt_start = max(0, pos - context_size // 2)
            excerpt_end = min(len(text), pos + context_size // 2)
            excerpt = text[excerpt_start:excerpt_end]

            excerpts.append(excerpt)
            start = pos + len(keyword_lower)

        return excerpts


if __name__ == "__main__":
    # Test
    from config import PDF_DIRECTORY
    extractor = PDFExtractor(PDF_DIRECTORY)
    results = extractor.search_for_simulant("JSC-1")
    print(f"Found {len(results)} results for JSC-1")
