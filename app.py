import uuid
import os
import glob
import time
import logging
import traceback

from flask import Flask, request, jsonify, render_template
from orchestrator import agent
from data_loader import ALL_COLS, NUMERIC_COLS, CATEGORICAL_COLS, df, SAMPLE_ROWS
from daily_question import get_daily_question
from report_generator import generate_report
from config import CHART_DIR, REPORTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format=(
    "%(asctime)s " # Time of logging message
    "[%(name)s] " # Name of file that show the message
    "%(levelname)s - " # Type of message
    "%(message)s" # The message
    )
)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

memory_store = {}
MIN_SECONDS_BETWEEN_REQUETS = 2
last_request_time = {}

def cleanup_old_files(folder, max_age_hours=24):
    """
    Delete old files each day 
    so we don't expand folders with files.
    """
    # Calculate the current age from 1970 by seconds
    cutoff = (
        time.time() - (max_age_hours * 3600)
    )
    deleted = 0
    # For each folder get all the files
    for filepath in glob.glob(
        os.path.join(folder, '*')
    ):
        try:
            # Get the age of the file by seconds
            if os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
                deleted += 1
        except Exception as e:
            logger.warning(f"Could not delete {filepath}: {e}")
    if deleted > 0:
        logger.info(
            f"Deleted {deleted} old files from {folder}"
        )

def check_rate_limit(session_id):
    """
    Stop the process some time between 2 requests.
    """
    now = time.time()
    last = last_request_time.get(session_id, 0)
    if now - last < MIN_SECONDS_BETWEEN_REQUETS:
        return False
    
    last_request_time[session_id] = now
    return True

def validate_question(question):

    if not question or not question.strip():
        return False, 'Please enter a question'
    
    if len(question) > 1000:
        return False, (
            'Question is too long. '
            'Please keep it under 1000 characters.'
        )
    
    if len(question.strip()) < 2:
        return False, 'Question is too short.'
    
    return True, ''

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify(
        {
            'status': 'ok',
            'rows': len(df)
        }
    )

@app.route('/schema')
def schema():
    return jsonify(
        {
            'columns': ALL_COLS,
            'numeric': NUMERIC_COLS,
            'categorical': CATEGORICAL_COLS,
            'rows': len(df),
            'sample': SAMPLE_ROWS
        }
    )

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # convert the JSON request response to python dictionary
        # and if empty get empty JSON
        body = request.get_json() or {}
        question = (body.get('question') or "").strip()
        session_id = body.get('session_id') or str(uuid.uuid4())
        valid, error_msg = validate_question(question)
        if not valid:
            return jsonify(
                {
                    'error': error_msg
                }
            ), 400
        if not check_rate_limit(session_id):
            return jsonify(
                {
                    'error': 'Please wait a moment before sending another question.'
                }
            ), 429
        
        memory = memory_store.get(session_id, [])
        logger.info(
            f"session={session_id[:8]} | {question[:60]}"
        )
        result = agent.run(
            question=question,
            memory=memory
        )
        # if session id doesn't existe. creates one and add the quesion to it
        memory_store.setdefault(session_id, []).append({
            'question': question,
            'answer': result.get('text', '')[:300]
        }
        )
        memory_store[session_id] = memory_store[session_id][-10:]

        return jsonify(
            {
                'session_id': session_id,
                'answer': result.get('text', 'No answer.'),
                'chart': result.get('chart'),
                'report_url': result.get('report_url'),
                'category': result.get('category', 'analytics'),
                'intent': result.get('intent', ''),
                'last_qa': memory_store[session_id][-5:]
            }
        )
    except Exception as e:
        traceback.print_exc()
        logger.error(
            f"Unexpected error: {e}"
        )

        return jsonify(
            {
                'error': str(e),
                'answer': 'Server error. Please try again.'
            }
        ), 500
    
@app.route('/report')
def download_report():
    return jsonify(generate_report())

@app.route('/clear', methods=['POST'])
def clear_session():
    data = request.get_json() or {}
    sid = data.get('session_id')
    if sid:
        memory_store.pop(sid, None)
        last_request_time.pop(sid, None)
        logger.info(
            f"Session {str(sid)[:8]} cleared"
        )
    return jsonify(
        {
            'status': 'cleared'
        }
    )

@app.route('/daily-question', methods=['GET'])
def daily_question_route():
    try:
        # we used '.args' to get the value of lang from the URL 
        lang = request.args.get('lang', 'en')
        if lang not in ('en', 'fr'):
            lang = 'en'
        return jsonify(get_daily_question(lang))
    except Exception as e:
        logger.error(
            f"Daily question error: {e}"
        )
        return jsonify(
            {
                'error': str(e)
            }
        ), 500
    
if __name__ == '__main__':
    logger.info("Starting NexusAI on http://127.0.0.1:5000")
    app.run(debug=False, host='127.0.0.1', port=5000)