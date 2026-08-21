import os
import PyPDF2
from typing import List

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Parses a PDF document and extracts all readable text into a unified string.
    
    Args:
        pdf_path (str): The absolute or relative file path to the target PDF.
        
    Returns:
        str: The complete extracted text payload.
        
    Raises:
        FileNotFoundError: If the provided path does not resolve to a file.
        RuntimeError: If the binary reading process encounters a structural failure.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Missing resource at path: {pdf_path}")

    extracted_text = []
    
    try:
        with open(pdf_path, 'rb') as file_stream:
            pdf_reader = PyPDF2.PdfReader(file_stream)
            for page in pdf_reader.pages:
                text_content = page.extract_text()
                if text_content:
                    extracted_text.append(text_content)
                    
        return "\n".join(extracted_text).strip()
        
    except Exception as execution_error:
        raise RuntimeError(f"PDF extraction failed: {str(execution_error)}")

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Implements a sliding-window algorithm to segment large text payloads 
    into overlapping contextual chunks for vector embedding.
    
    Args:
        text (str): The continuous text payload to be segmented.
        chunk_size (int): The maximum character boundary per chunk.
        overlap (int): The character overlap margin to prevent context loss.
        
    Returns:
        List[str]: A sequence of text segments ready for vectorization.
    """
    if not text:
        return []

    text_chunks = []
    current_index = 0
    total_length = len(text)

    while current_index < total_length:
        boundary = current_index + chunk_size
        text_chunks.append(text[current_index:boundary])
        current_index += (chunk_size - overlap)

    return text_chunks