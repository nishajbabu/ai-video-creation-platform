import os
import PyPDF2
from typing import List

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts raw text from a given PDF file.
    
    Args:
        pdf_path (str): The absolute or relative path to the PDF file.
        
    Returns:
        str: The extracted text as a single string.
        
    Raises:
        FileNotFoundError: If the specified PDF file does not exist.
        RuntimeError: If the PDF reading process fails.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found at path: {pdf_path}")

    extracted_text = []
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
                    
        return "\n".join(extracted_text).strip()
        
    except Exception as e:
        raise RuntimeError(f"Failed to process PDF: {str(e)}")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Splits a large text string into smaller, overlapping chunks for vector embedding.
    
    Args:
        text (str): The full text to be chunked.
        chunk_size (int): The maximum character length of each chunk.
        overlap (int): The number of characters to overlap between chunks to preserve context.
        
    Returns:
        List[str]: A list of text chunks.
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # Move the start forward, subtracting the overlap to keep context tied together
        start += (chunk_size - overlap)

    return chunks

# --- MODULE EXECUTION ---
if __name__ == "__main__":
    test_pdf = "sample.pdf"
    
    try:
        print(f"Processing '{test_pdf}'...")
        raw_text = extract_text_from_pdf(test_pdf)
        
        print("Chunking text...")
        text_chunks = chunk_text(raw_text, chunk_size=800, overlap=150)
        
        print(f"Successfully generated {len(text_chunks)} chunks.")
        
        # Display the first chunk as a validation check
        if text_chunks:
            print("\n--- CHUNK 1 PREVIEW ---")
            print(text_chunks[0])
            
    except Exception as error:
        print(f"Error during execution: {error}")