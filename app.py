import io
import streamlit as st
import pytesseract
from PIL import Image
from docx import Document
from pypdf import PdfReader
from pdf2image import convert_from_bytes

st.set_page_config(page_title="Document Text & OCR Extractor", layout="centered")

def extract_from_docx(file_bytes) -> str:
    """Extract text from Word (.docx) files."""
    doc = Document(io.BytesIO(file_bytes))
    full_text = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
    return "\n\n".join(full_text)

def extract_from_pdf(file_bytes) -> str:
    """Extract digital text from PDF, falling back to OCR for scanned pages."""
    pdf_reader = PdfReader(io.BytesIO(file_bytes))
    extracted_pages = []

    for idx, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if text and len(text.strip()) > 20:
            extracted_pages.append(f"--- Page {idx + 1} ---\n" + text.strip())
        else:
            # Fallback: Convert PDF page to image and run Tesseract OCR
            images = convert_from_bytes(file_bytes, first_page=idx + 1, last_page=idx + 1)
            if images:
                ocr_result = pytesseract.image_to_string(images[0])
                extracted_pages.append(f"--- Page {idx + 1} (OCR) ---\n" + ocr_result.strip())

    return "\n\n".join(extracted_pages)

def extract_from_image(file_bytes) -> str:
    """Extract text from raw image files (PNG/JPG)."""
    image = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(image)


st.title("📄 Document Text & OCR Extractor")
st.write("Upload a PDF, DOCX, or Image file to extract plain text.")

uploaded_file = st.file_uploader(
    "Choose a file", 
    type=["pdf", "docx", "png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()
    file_bytes = uploaded_file.read()

    with st.spinner("Extracting text..."):
        extracted_text = ""
        try:
            if file_type == "docx":
                extracted_text = extract_from_docx(file_bytes)
            elif file_type == "pdf":
                extracted_text = extract_from_pdf(file_bytes)
            elif file_type in ["png", "jpg", "jpeg"]:
                extracted_text = extract_from_image(file_bytes)

            if extracted_text.strip():
                st.success("Extraction Complete!")
                st.subheader("Extracted Text")
                st.text_area("Result", value=extracted_text, height=350)

                st.download_button(
                    label="Download Plain Text (.txt)",
                    data=extracted_text,
                    file_name=f"{uploaded_file.name}_extracted.txt",
                    mime="text/plain"
                )
            else:
                st.warning("No readable text found in the uploaded file.")

        except Exception as e:
            st.error(f"Error processing document: {e}")
