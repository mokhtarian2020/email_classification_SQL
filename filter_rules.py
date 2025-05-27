import re

def is_auto_reply_or_spam(subject: str, body: str) -> bool:
    text = f"{subject.lower()} {body.lower()}"

    auto_reply_keywords = [
        "out of office", "risposta automatica", "auto-reply", "non sono disponibile",
        "sono fuori sede", "away from my desk", "tornerò il", "torneremo il",
        "i will be back", "i am currently unavailable", "sarò assente", "vacation",
        "ferie", "leave of absence", "assenza", "momentaneamente non disponibile"
    ]

    spam_keywords = [
        "unsubscribe", "newsletter", "offerta speciale", "promo", "pubblicità",
        "advertising", "mailing list", "clicca qui", "special offer", "limited time",
        "guadagna", "opportunità", "richiedi ora", "compra ora", "offerta imperdibile",
        "sconto esclusivo", "bonus", "vincere", "lotteria", "concorso", "free trial",
        "try now", "scarica ora", "download now", "urgent", "act now", "limited offer"
    ]

    auto_reply_patterns = [
        r"^i am (currently )?(out of the office|on vacation|away from my desk)",
        r"^sono (momentaneamente )?(fuori sede|in ferie|non disponibile)",
        r"^torner(ò|emo) il \d{1,2}/\d{1,2}/\d{4}",
        r"^i will (be back|return) on \d{1,2}/\d{1,2}/\d{4}",
        r"^this is an automated response",
        r"^questa è una risposta automatica"
    ]

    spam_patterns = [
        r"click (here|below)", r"clicca (qui|sotto)", r"unsubscribe", r"annulla iscrizione",
        r"special offer", r"offerta speciale", r"limited time", r"tempo limitato",
        r"win a prize", r"vincere un premio", r"free trial", r"prova gratuita"
    ]

    if any(kw in text for kw in auto_reply_keywords + spam_keywords):
        return True

    for pattern in auto_reply_patterns + spam_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False
