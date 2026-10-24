import json
import re
import logging
import boto3

from config import (
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_KEY,
    BEDROCK_MODEL_ID,
    KNOWLEDGE_BASE_ID,
)
from data_loader import ALL_COLS, SAMPLE_ROWS

logger = logging.getLogger(__name__)

##### AWS clients #####
session = boto3.Session(
    region_name = AWS_REGION,
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_KEY
)
bedrock_runtime = session.client("bedrock-runtime")
bedrock_agent   = session.client("bedrock-agent-runtime")


##### LANGUAGE DETECTION #####
FRENCH_WORDS = {
    "montre","affiche","donne","quel","quelle","quels","quelles",
    "combien","comment","pourquoi","quand","meilleur","meilleurs",
    "total","moyenne","ventes","chiffre","produit","produits",
    "region","région","categorie","catégorie","tendance","rapport",
    "graphique","histogramme","camembert","classement","les","des",
    "par","sur","est","sont","mon","ma","tu","je","bonjour",
    "salut","merci","aide","génère","genere","fais","faire","voir",
    "dis","moi","résumé","résume","mensuel","annuel","afficher",
}

ANALYTICS_KEYWORDS = {
    "show", "plot", "chart", "graph", "display", "list",
    "compare", "rank", "sort", "visualize", "draw",
    "top", "bottom", "best", "worst", "highest", "lowest",
    "most", "least", "largest", "smallest",
    "total", "sum", "average", "mean", "count",
    "how many", "percentage", "rate", "ratio",
    "growth", "trend", "distribution", "correlation",
    "histogram", "pie", "bar", "line", "scatter",
    "sales", "profit", "revenue", "discount", "quantity",
    "category", "sub_category", "subcategory",
    "segment", "region", "state", "city", "country",
    "product", "customer", "order", "ship_mode", "shipmode",
    "furniture", "technology", "office", "supplies",
    "consumer", "corporate", "home",
    "bookcases", "chairs", "tables", "storage",
    "phones", "copiers", "machines", "accessories",
    "binders", "paper", "labels", "envelopes", "fasteners",
    "appliances", "art",
    "central", "east", "south", "west",
    "standard", "second", "first", "same day",
    "monthly", "yearly", "annual", "weekly", "daily",
    "year", "month", "quarter", "2018", "2019", "2020", "2021",
    "montre", "affiche", "graphique", "ventes", "bénéfice",
    "remise", "quantité", "tendance", "région", "catégorie",
    "segment", "produit", "client", "commande",
}

RAG_KEYWORDS = {
    "account", "password", "login", "sign up", "register",
    "registration", "profile", "username", "forgot password",
    "reset password", "delete account", "create account",
    "update account", "account information", "account settings",
    "cancel order", "cancellation", "change order", "modify order",
    "order status", "where is my order", "track order",
    "tracking number", "order history", "wrong item",
    "missing item", "order confirmation",
    "delivery", "shipping policy", "delivery time",
    "shipping time", "free shipping", "shipping cost",
    "shipping address", "change address", "delivery address",
    "international shipping", "express shipping",
    "expedited shipping", "estimated delivery",
    "delivery problem", "delivery delay", "late delivery",
    "lost package", "damaged package", "missing package",
    "return", "refund", "exchange", "money back",
    "return policy", "refund policy", "return request",
    "refund status", "how to return", "return label",
    "partial refund", "full refund",
    "payment", "pay", "credit card", "debit card",
    "paypal", "payment method", "payment issue",
    "billing", "charge", "invoice", "receipt",
    "get invoice", "request invoice", "payment failed",
    "payment problem", "payment information",
    "complaint", "complain", "feedback", "review",
    "bad experience", "problem with", "issue with",
    "not satisfied", "disappointed", "broken", "defective",
    "not working", "wrong color", "wrong size",
    "support", "contact", "help", "customer service",
    "speak to agent", "human agent", "live chat",
    "phone number", "email address", "contact us",
    "business hours", "opening hours", "available",
    "talk to someone",
    "promo code", "discount code", "coupon", "voucher",
    "promotion", "offer", "deal", "loyalty program",
    "gift card", "bulk discount", "wholesale",
    "price match", "price adjustment",
    "out of stock", "back order", "backorder", "pre order",
    "discontinued", "coming soon", "available",
    "when will", "restock", "notify me",
    "warranty", "guarantee", "satisfaction",
    "gift wrap", "gift message", "newsletter",
    "unsubscribe", "subscription", "installation",
    "assembly", "privacy policy", "terms", "conditions",
    "faq", "how to", "can i",
    "politique", "retour", "remboursement", "livraison",
    "paiement", "annulation", "garantie", "compte",
    "mot de passe", "service client", "réclamation",
    "facture", "reçu", "aide", "contacter", "plainte",
    "adresse", "promotion", "code promo",
}

REPORT_KEYWORDS = {
    "report", "pdf", "export", "generate report",
    "create report", "make report", "full report",
    "rapport", "génère rapport",
}

def detect_language(text: str) -> str:
    """
    Looking into the text and trying to recognize
    any french or english words.
    """

    text = text.lower()
    # Split the text trough special characters
    # Convert to set to ignore duplicates
    words = set(
        re.split(
            r"[\s'\-,;:.!?]+",
            text
        )
    )
    if words & FRENCH_WORDS:
        return 'fr'
    else:
        return 'en'

def classify_question(question, lang="en"):
    """
    Quickly classify the question type using a lightweight prompt.
    Returns: "analytics" | "rag" | "report"
    """
    
    q_lower = question.lower()
    # Check the report keywords
    for keyword in REPORT_KEYWORDS:
        if keyword in q_lower:
            logger.info('Fast Classify-> report')
            return 'report'
    
    words = set(
        re.split(
             r"[\s'\-,;:.!?]+",
             q_lower
        )
    )

    # Gets the common words
    analytics_score = len(
        words & ANALYTICS_KEYWORDS
    )
    
    rag_score = len(
        words & RAG_KEYWORDS
    )
    
    if analytics_score > rag_score:
        logger.info('Fast classify -> analytics')
        return 'analytics'
    
    if rag_score > analytics_score:
        logger.info('Fast classify -> rag')
        return 'rag'
    
    logger.info('Ambiguous — calling Claude to classify')

    prompt = f"""Classify this question into ONE category:
Question: "{question}"
Categories:
- analytics: data, numbers, charts, sales metrics
- report: user wants a PDF report
- rag: policies, shipping, payments, account, FAQs
Reply with ONLY one word: analytics, rag, or report."""

    try:
        body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 10,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        resp = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body)
        )

        answer = json.loads(
            resp['body'].read()
        )['content'][0]['text']
        answer = answer.strip().lower()

        if 'report' in answer:
            return 'report'
        
        if 'rag' in answer:
            return 'rag'
        
        return 'analytics'
    
    except Exception as e:
        logger.error(f'Classification failed: {e}')

        return 'analytics'

def ask_rag(question, lang="en"):
    """
    after the claude choose the RAG class.
    we pass him the user's question.
    """

    if lang == 'fr':
        prefix = (
        "Tu es un assistant. "
        "Réponds TOUJOURS en français. "
        )
    else:
        prefix = (
        "You are a helpful assistant. "
        "Reply in English. "
        )

    try:
        resp = bedrock_agent.retrieve_and_generate(
            input={
                "text": prefix + question
                },
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": 'arn:aws:bedrock:us-east-1:469830469617:inference-profile/global.anthropic.claude-haiku-4-5-20251001-v1:0',
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {"numberOfResults": 5}
                    },
                },
            },
        )
        answer = (
            resp.get("output", {})
            .get("text", "")
        )
        if not answer:
            if lang == 'fr':
                answer = (
                "Je n'ai pas trouvé de réponse."
                )
            else:
                answer = (
                "I couldn't find an answer."
            )
                
        sources = set()

        for ref in resp.get("citations", []):
            for loc in ref.get("retrievedReferences", []):
                # Gets the path  of the response
                uri = (
                    loc.get("location", {})
                    .get("s3Location", {})
                    .get("uri", "")
                )
                if uri:
                # Extracts the file name from the path
                    filename = uri.split('/')[-1]
                    sources.add(filename)

        if sources:
            answer += (
                f"\n\n📎 Sources: "
                f"{', '.join(sorted(sources))}"
            )

        return {"text": answer, "chart": None}
    except Exception as e:
       logger.error(f'RAG error: {e}')

       return {
           'text': f'Knowledge base error: {e}',
           'chart': None
       }
