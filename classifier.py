from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_PATH = os.getenv("MODEL_PATH")

# ✅ Updated department labels
LABELS = [
    "Legale",
    "Contabilità",
    "Fatturazione",
    "Auto Aziendali",
    "Customer Relation",
    "Risorse Umane",
    "Acquisti",
    "Servizi"
]

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()

MAX_LEN = 512
CHUNK_SIZE = 480
OVERLAP = 32

def classify_email(text):
    tokens = tokenizer.encode(text, add_special_tokens=True, truncation=False)
    chunks = []

    for i in range(0, len(tokens), CHUNK_SIZE - OVERLAP):
        chunk = tokens[i:i + CHUNK_SIZE]
        if len(chunk) > 0:
            chunk = chunk[:MAX_LEN]
            chunks.append(chunk)

    all_probs = []
    for chunk in chunks:
        input_ids = torch.tensor([chunk])
        with torch.no_grad():
            outputs = model(input_ids)
            probs = torch.nn.functional.softmax(outputs.logits, dim=1)
            all_probs.append(probs[0])

    avg_probs = torch.stack(all_probs).mean(dim=0)
    pred_idx = torch.argmax(avg_probs).item()

    return LABELS[pred_idx], avg_probs[pred_idx].item()
