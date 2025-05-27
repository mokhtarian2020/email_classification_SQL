from bs4 import BeautifulSoup
import re
import fitz  # PyMuPDF
from docx import Document
import os
import tempfile
import pytesseract
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # If HEIC support not needed or pillow-heif not installed

# 🚀 Added imports for translation
import torch
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def clean_text(text):
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    text = re.sub(r"^(From|To|Date|Cc|Bcc):.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    patterns = [
        r"^(Gentil[ei] (Cliente|Team)),?\s*", r"^(Buongiorno|Buonasera|Salve),?\s*",
        r"(Cordiali|Distinti) saluti,.*$", r"^Grazie( mille)?,.*$"
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r">.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\bOn\s.*wrote:\b.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"\b\w+\.(pdf|docx|jpg|png|heic|jpeg)\b", "", text)
    text = re.sub(r"\b(Ref|Ticket|Case)[#:]?\s*\w+-\d+\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"[^a-zA-ZÀ-ÿ0-9\s.,!?]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_text_from_attachment(part):
    content_type = part.get_content_type()
    filename = part.get_filename()
    if not filename:
        return ""

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(part.get_payload(decode=True))
        tmp_path = tmp_file.name

    extracted_text = ""
    try:
        if filename.endswith(".pdf"):
            with fitz.open(tmp_path) as doc:  # Ensure the file is properly closed
                for page in doc:
                    extracted_text += page.get_text()
        elif filename.endswith(".docx"):
            doc = Document(tmp_path)
            extracted_text = "\n".join(p.text for p in doc.paragraphs)
        elif filename.endswith(".txt"):
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                extracted_text = f.read()
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
    finally:
        try:
            os.unlink(tmp_path)  # Ensure the file is deleted
        except Exception as e:
            print(f"⚠️ Could not delete temporary file {tmp_path}: {e}")

    return extracted_text


def extract_text_from_image_attachment(part):
    filename = part.get_filename()
    content_type = part.get_content_type()

    if not filename or not content_type.startswith("image/"):
        return ""

    with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as tmp_file:
        tmp_file.write(part.get_payload(decode=True))
        tmp_path = tmp_file.name

    try:
        img = Image.open(tmp_path)
        text = pytesseract.image_to_string(img, lang="ita+eng")  # Use Italian OCR
    except Exception as e:
        print(f"❌ OCR failed for image {filename}: {e}")
        text = ""
    finally:
        os.unlink(tmp_path)

    return text.strip()


# ✅ NEW: Translation with Hugging Face MarianMT
def translate_to_italian(text):
    try:
        detected_lang = detect(text)
        if detected_lang == "it":
            return text

        model_name = "Helsinki-NLP/opus-mt-en-it"
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name).to("cuda" if torch.cuda.is_available() else "cpu")

        tokens = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        tokens = {k: v.to(model.device) for k, v in tokens.items()}
        translated = model.generate(**tokens)
        return tokenizer.decode(translated[0], skip_special_tokens=True)

    except Exception as e:
        print(f"⚠️ Translation failed: {e}")
        return text
