# pilot_email_reader.py

import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

from utils import clean_text, extract_text_from_attachment, extract_text_from_image_attachment, translate_to_italian

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
print("IMAP_SERVER from env:", IMAP_SERVER)


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
    body_text = extract_email_body(msg)
    attachment_text = ""

    for part in msg.walk():
        content_dispo = str(part.get("Content-Disposition") or "")
        filename = part.get_filename()

        if "attachment" in content_dispo and filename:
            filename_lower = filename.lower()
            if filename_lower.endswith(('.pdf', '.docx', '.txt')):
                attachment_text += extract_text_from_attachment(part) + "\n"
            elif filename_lower.endswith(('.jpg', '.jpeg', '.png')):
                attachment_text += extract_text_from_image_attachment(part) + "\n"

    full_text = body_text + "\n" + attachment_text
    return clean_text(full_text)


def read_last_2_unseen_emails():
    imap = imaplib.IMAP4_SSL(IMAP_SERVER)
    imap.login(EMAIL, PASSWORD)
    imap.select("INBOX")

    status, messages = imap.search(None, 'UNSEEN')
    email_ids = messages[0].split()
    last_2 = email_ids[-2:]

    print(f"\n📬 Fetching {len(last_2)} unseen emails...\n")

    for num in last_2:
        status, msg_data = imap.fetch(num, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject
                translated_subject = translate_to_italian(subject)

                full_clean_text = extract_all_text(msg)
                translated_text = translate_to_italian(full_clean_text)

                print("======================================")
                print(f"📧 Subject: {translated_subject}")
                print(f"📝 Cleaned Text:\n{translated_text}")
                print("======================================\n")

    imap.logout()


if __name__ == "__main__":
    read_last_2_unseen_emails()
