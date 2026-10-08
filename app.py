import io
import numpy as np
import streamlit as st
import easyocr
from PIL import Image
from docx import Document
from pypdf import PdfReader
from pdf2image import convert_from_bytes

st.set_page_config(page_title="Document Text & OCR Extractor", layout="centered")

@st.cache_resource
def load_ocr_reader():
    """Cache EasyOCR Reader to avoid reloading weights on every run."""
    return easyocr.Reader(['en'], gpu=False)

def extract_from_docx(file_bytes) -> str:
    """Extract text from Word (.docx) files."""
    doc = Document(io.BytesIO(file_bytes))
    full_text = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
    return "\n\n".join(full_text)

def extract_from_pdf(file_bytes, reader) -> str:
    """Extract digital text from PDF, falling back to OCR for scanned pages."""
    pdf_reader = PdfReader(io.BytesIO(file_bytes))
    extracted_pages = []

    for idx, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        # If the page contains standard digital text, use it directly
        if text and len(text.strip()) > 20:
            extracted_pages.append(f"--- Page {idx + 1} ---\n" + text.strip())
        else:
            # Fallback: Convert page to image, cast to NumPy array, and run OCR
            images = convert_from_bytes(file_bytes, first_page=idx + 1, last_page=idx + 1)
            if images:
                img_np = np.array(images[0])  # Convert PIL Image to NumPy array
                ocr_result = reader.readtext(img_np, detail=0)
                extracted_pages.append(f"--- Page {idx + 1} (OCR) ---\n" + "\n".join(ocr_result))

    return "\n\n".join(extracted_pages)

def extract_from_image(file_bytes, reader) -> str:
    """Extract text from raw image files (PNG/JPG)."""
    # EasyOCR accepts raw bytes directly for images
    results = reader.readtext(file_bytes, detail=0)
    return "\n".join(results)


st.title("📄 Document Text & OCR Extractor")
st.write("Upload a PDF, DOCX, or Image file to extract all plain text.")

uploaded_file = st.file_uploader(
    "Choose a file", 
    type=["pdf", "docx", "png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()
    file_bytes = uploaded_file.read()

    with st.spinner("Processing file and running OCR if needed..."):
        ocr_reader = load_ocr_reader()
        extracted_text = ""

        try:
            if file_type == "docx":
                extracted_text = extract_from_docx(file_bytes)
            elif file_type == "pdf":
                extracted_text = extract_from_pdf(file_bytes, ocr_reader)
            elif file_type in ["png", "jpg", "jpeg"]:
                extracted_text = extract_from_image(file_bytes, ocr_reader)

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
