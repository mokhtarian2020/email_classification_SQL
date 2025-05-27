import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os
import smtplib
from email.message import EmailMessage

from utils import (
    clean_text,
    extract_text_from_attachment,
    extract_text_from_image_attachment,
    translate_to_italian
)
from classifier import classify_email
from filter_rules import is_auto_reply_or_spam

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
OPERATOR_EMAIL = os.getenv("OPERATOR_EMAIL")


def extract_email_body(msg):
    html = ""
    plain = ""

    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == "text/html" and not html:
            payload = part.get_payload(decode=True)
            if payload:
                html = payload.decode(errors="ignore")
        elif content_type == "text/plain" and not plain:
            payload = part.get_payload(decode=True)
            if payload:
                plain = payload.decode(errors="ignore")

    return html if html else plain


def extract_all_text(msg):
    """
    Gather raw text from subject, body, and attachments
    without translating. The caller decides when to translate.
    """
    # Decode subject (raw)
    subject, encoding = decode_header(msg["Subject"])[0]
    subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject

    # Extract body (raw)
    body_text = extract_email_body(msg).strip()

    # Extract attachments (raw)
    attachment_text = ""
    for part in msg.walk():
        content_dispo = str(part.get("Content-Disposition") or "")
        filename = part.get_filename()
        if "attachment" in content_dispo and filename:
            filename_lower = filename.lower()
            extracted = ""
            if filename_lower.endswith(('.pdf', '.docx', '.txt')):
                extracted = extract_text_from_attachment(part)
            elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.heic')):
                extracted = extract_text_from_image_attachment(part)
            if extracted:
                # Just accumulate raw text here (no translation).
                attachment_text += extracted + "\n"

    # Combine all raw sections
    combined_text = f"{subject}\n{body_text}\n{attachment_text}"
    return combined_text


def forward_to_operator(msg):
    try:
        fwd = EmailMessage()
        fwd["Subject"] = "🔎 Revisione manuale richiesta: " + msg.get("Subject", "")
        fwd["From"] = EMAIL
        fwd["To"] = OPERATOR_EMAIL
        fwd.set_content("Questa email non è stata processata automaticamente. Si prega di revisionarla manualmente.")

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            content = part.get_payload(decode=True)
            if content:
                fwd.add_attachment(content,
                                   maintype=part.get_content_maintype(),
                                   subtype=part.get_content_subtype(),
                                   filename=part.get_filename())

        with smtplib.SMTP("smtp.toyotaitalia.com", 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.send_message(fwd)
        print("📨 Inviata all’operatore per revisione manuale.")
    except Exception as e:
        print(f"❌ Invio all’operatore fallito: {e}")


def check_and_classify():
    imap = imaplib.IMAP4_SSL(IMAP_SERVER)
    imap.login(EMAIL, PASSWORD)
    imap.select("INBOX")

    status, messages = imap.search(None, 'UNSEEN')
    for num in messages[0].split():
        status, msg_data = imap.fetch(num, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # 1) Decode subject for logging/spam check
                raw_subj, encoding = decode_header(msg["Subject"])[0]
                raw_subj = raw_subj.decode(encoding or "utf-8") if isinstance(raw_subj, bytes) else raw_subj

                # Quick spam/auto-reply check on subject alone
                if is_auto_reply_or_spam(raw_subj, ""):
                    print(f"\n📧 Subject: {raw_subj}")
                    print("⚠️ Email ignorata: rilevata come risposta automatica o spam (solo subject).")
                    continue

                # 2) Extract raw text from subject, body, attachments
                raw_text = extract_all_text(msg)

                # 3) Clean the combined text
                cleaned_text = clean_text(raw_text)

                # Optional second spam check with full text:
                if is_auto_reply_or_spam(raw_subj, cleaned_text):
                    print(f"\n📧 Subject: {raw_subj}")
                    print("⚠️ Email ignorata: rilevata come spam dopo analisi completa.")
                    continue

                # 4) If no text remains, forward to operator
                if not cleaned_text.strip():
                    print(f"\n📧 Subject: {raw_subj}")
                    print("⚠️ Nessun contenuto leggibile trovato. Inoltro all’operatore...")
                    forward_to_operator(msg)
                    continue

                # 5) Single translation of the final text
                final_text = translate_to_italian(cleaned_text)

                # 6) Classify
                label, score = classify_email(final_text)
                print(f"\n📧 Subject: {raw_subj}")
                print(f"📂 Department: {label} ({score:.2f})")

    imap.logout()
