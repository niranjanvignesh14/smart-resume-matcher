"""
PDF text extraction. Single responsibility: PDF -> plain text.
"""

import pdfplumber


def extract_text_from_pdf(file) -> str:
    """file: a Streamlit UploadedFile object (behaves like a file handle)."""
    text_parts = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)
