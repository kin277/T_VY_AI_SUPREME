"""
====================================================================
DOCUMENT PARSER - TRÍCH XUẤT NỘI DUNG TỪ PDF, DOCX & TXT
====================================================================
"""

import io
from pypdf import PdfReader
from docx import Document

class DocumentParser:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts).strip()
        except Exception as e:
            return f"[Lỗi đọc file PDF: {str(e)}]"

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        try:
            doc = Document(io.BytesIO(file_bytes))
            text_parts = [para.text for para in doc.paragraphs if para.text]
            return "\n".join(text_parts).strip()
        except Exception as e:
            return f"[Lỗi đọc file DOCX: {str(e)}]"

    @staticmethod
    def parse_file(filename: str, file_bytes: bytes) -> str:
        fn_lower = filename.lower()
        if fn_lower.endswith('.pdf'):
            return DocumentParser.extract_text_from_pdf(file_bytes)
        elif fn_lower.endswith(('.docx', '.doc')):
            return DocumentParser.extract_text_from_docx(file_bytes)
        elif fn_lower.endswith('.txt'):
            return file_bytes.decode('utf-8', errors='ignore')
        else:
            return f"[Định dạng file không hỗ trợ: {filename}]"