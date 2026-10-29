import io
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from app.core.logger import get_logger

logger = get_logger("document_tool")


class DocumentParserTool:
    """
    Document Parser Tool for ingesting literature, research papers, and audit reports.
    Extracts structured page content, word counts, and metadata from PDF, Markdown, and TXT files.
    """

    @staticmethod
    def parse_pdf_bytes(file_bytes: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
        """
        Extracts text per page from PDF bytes.
        Gracefully falls back to plain text extraction if the file is a text-based paper.
        """
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
            pages_content: List[Dict[str, Any]] = []
            full_text_list: List[str] = []

            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                text = page.extract_text() or ""
                text = text.strip()
                word_count = len(text.split())
                
                pages_content.append({
                    "page_number": page_num,
                    "text": text,
                    "word_count": word_count
                })
                if text:
                    full_text_list.append(f"--- Page {page_num} ---\n{text}")

            total_words = sum(p["word_count"] for p in pages_content)
            full_text = "\n\n".join(full_text_list)

            logger.info(f"Parsed PDF '{filename}': {total_pages} pages, {total_words} words extracted.")

            return {
                "filename": filename,
                "total_pages": total_pages,
                "total_words": total_words,
                "pages": pages_content,
                "full_text": full_text
            }
        except Exception as err:
            logger.warning(f"pypdf reader encountered an issue on '{filename}': {err}. Falling back to text decoder.")
            return DocumentParserTool.parse_text_bytes(file_bytes, filename)

    @staticmethod
    def parse_text_bytes(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses plain text or markdown files."""
        text = file_bytes.decode("utf-8", errors="replace").strip()
        words = len(text.split())
        return {
            "filename": filename,
            "total_pages": 1,
            "total_words": words,
            "pages": [{"page_number": 1, "text": text, "word_count": words}],
            "full_text": text
        }
