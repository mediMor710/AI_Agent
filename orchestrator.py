import logging

from bedrock_client import detect_language, classify_question, ask_rag
from code_executor import run_analysis
from report_generator import generate_report

logger = logging.getLogger(__name__)

GREET_KEYWORDS = {
    "hi", "hello", "hey", "good morning", "good afternoon",
    "good evening", "what can you do", "who are you",
    "help me", "help",
    "bonjour", "salut", "bonsoir", "aide moi",
}

REPORT_KEYWORDS = {
    "report", "pdf", "export", "generate report",
    "create report", "make report", "full report",
    "rapport", "génère", "générer",
}

GREET_EN = """\
👋 Hello! I'm NexusAI, your Sales Intelligence Agent.

I can help you with:
  📊 Analytics — ask me anything about your sales data
  📚 Knowledge Base — company policies and FAQs
  📄 Reports — generate custom PDF reports

Try asking:
  • "What are the total sales by region?"
  • "Show top 10 products by revenue"
  • "What is your return policy?"
  • "Generate a full PDF report"

What would you like to know?
"""

GREET_FR = """\
👋 Bonjour ! Je suis NexusAI, votre agent d'intelligence commerciale.

Je peux vous aider avec :
  📊 Analytique — posez-moi n'importe quelle question sur vos ventes
  📚 Base de connaissances — politiques et FAQ
  📄 Rapports — génération de rapports PDF

Essayez :
  • "Quelles sont les ventes totales par région ?"
  • "Montre le top 10 des produits par revenu"
  • "Quelle est votre politique de retour ?"
  • "Génère un rapport PDF complet"

Que souhaitez-vous savoir ?
"""

def is_greeting(question):
    """
    Check the user's question if it has a greeting keywords.
    """
    q = question.lower().strip()
    for kw in GREET_KEYWORDS:
        if q.startswith(kw) or q == kw:
            return True
    return False

def is_report(question):
    """
    Check the user's question if it has a report keywords.
    """
    q = question.lower()
    for kw in REPORT_KEYWORDS:
        if kw in q:
            return True
    return False

class AgentWorkflow:

    def run(self,question,memory):

        lang = detect_language(question)
        logger.info(f'lang{lang} | question={question[:80]}')

        if is_greeting(question):
            logger.info('Route -> greeting')
            return {
                'text': GREET_FR if lang == 'fr' else GREET_EN,
                'chart': None,
                'report_url': None,
                'category': 'greeting',
                'intent': 'User greeting',
                'lang': lang
            }
        
        if is_report(question):
            logger.info('Route -> report')
            try:
                result = generate_report(question=question, lang=lang)
                return {
                    **result,
                    'category': 'report',
                    'intent': 'Generate PDF report',
                    'lang': lang
                }
            except Exception as e:
                logger.error(f'Report failed: {e}')
                return {
                    'text': (
                        f"Impossible de générer le rapport: {e}"
                        if lang == 'fr' else
                        f"Could not generate the report: {e}"
                    ),
                    'chart': None,
                    'report_url': None,
                    'category': 'report',
                    'intent': 'Report failed',
                    'lang': lang
                }
            
        q_type = classify_question(question, lang)
        logger.info(f'Classified as: {q_type}')

        if q_type == 'rag':
            try:
                result = ask_rag(question, lang)
                return {
                    **result, # Combine the dict of 'result' with this one
                    'report_url': None,
                    'category': 'rag',
                    'intent': 'Knowledge base lookup',
                    'lang': lang
                }
            except Exception as e:
                logger.info(f"RAG failed: {e}")
                return {
                    'text': (
                        'Erreur de base de connaissances.'
                        if lang == 'fr' else
                        'Knowledge base error. Please try again.'
                    ),
                        'chart': None,
                        'report_url': None,
                        'category': 'rag',
                        'intent': 'RAG failed',
                        'lang': lang
                    }
        try:
            result = run_analysis(question, lang=lang, memory=memory)
            if result is None:
                return {
                    'text': 'Sorry, I could not generate an answer. Please rephrase your question.',
                    'chart': None,
                    'report_url': None,
                    'category': 'analytics',
                    'intent': 'Data analytics',
                    'lang': lang
                }
            return {
                'text': result.get('text', ''),
                'chart': result.get('chart'),
                'report_url': None,
                'category': 'analytics',
                'intent': 'Data analysis',
                'lang': lang
            }
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            return {
                'text': (
                    "Je n'ai pas pu analyser cette question."
                    if lang == 'fr' else
                    "I could not analyze this question. Please try rephrasing."
                ),
                'chart': None,
                'report_url': None,
                'category': 'analytics',
                'intent': 'Analysis failed',
                'lang': lang
            }
            
agent = AgentWorkflow()