from pypdf import PdfReader
from typing import List, Optional

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        str: The extracted text.
    """
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

