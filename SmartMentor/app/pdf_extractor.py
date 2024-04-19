# pdf_extractor.py
import PyPDF2

def extract_text_from_pdf(pdf_file):
    # Assuming pdf_file is a file path or a file-like object
    reader = PyPDF2.PdfReader(pdf_file)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text
