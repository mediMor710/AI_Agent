import io 
import os  
import re
import sys
import json
import uuid # For generating unique filenames
import traceback # For printing detailed error messages
import logging 
import boto3
import matplotlib
matplotlib.use("Agg")   # 'Agg' == saves to file directly
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from config import(
    BEDROCK_MODEL_ID,
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_KEY,
    CHART_DIR,
    PALETTE
)
from data_loader import (
    df,
    get_schema_description,
    CAT_VALUES,
    SAMPLE_ROWS
)
from security import is_safe_code, get_block_reason

logger = logging.getLogger(__name__)

session = boto3.Session(
    region_name = AWS_REGION,
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_KEY
)

bedrock = session.client('bedrock-runtime')

def call_claude(prompt, max_tokens=2000):
    """
    Communicate with claude.
    """
    logger.info(f"PROMPT PREVIEW: {prompt[:300]}")
    body = {
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': max_tokens,
        'messages': [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': str(prompt)
                    }
                ]
                }
            ]
        }   
    resp = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body)
        )

    return json.loads(resp['body'].read())['content'][0]['text'].strip()

# Define the charts configuration
CHART_STYLE = f"""
CHART STYLE RULES:
- fig.patch.set_facecolor("#0f1117")
- ax.set_facecolor("#1a1d27")
- Titles: color="#e8eaf0"
- Axis labels and ticks: color="#9ca3af"
- Grid: ax.grid(axis="y", color="#2d3047", linewidth=0.6, linestyle="--", alpha=0.7)
- Spines: spine.set_edgecolor("#2d3047") for all spines
- Colors: use PALETTE list {PALETTE}
- Bar charts: figsize=(9, 4)
- Pie charts: figsize=(7, 7)
- Always end with fig.tight_layout() then chart_path = _save_chart(fig)
"""

def build_prompt(question, lang, memory):
    """
    Claude builds a prompt based on the user's question.
    """

    if memory:
            mem_text = '\n'.join(
                f"Q: {m['question']}\n"
                f"A: {str(m.get('answer', ''))[:120]}"
                for m in memory[-3:]
        )
    else: 
        mem_text = 'None'

    cat_vals_str = ""

    for col, vals in CAT_VALUES.items():
        cat_vals_str += (
            f'{col}: {vals[:30]}\n'
        )

    if lang == 'fr':
        lang_note = (
            'Write result_text ENTIRELY in French.'
        )
    else:
        lang_note = (
            'Write result_text ENTIRELY in English.'
        )

    prompt = f"""
        You are a Python data analysis engine.

{lang_note}

=== DATAFRAME SCHEMA ===
{get_schema_description()}

=== EXACT VALUES IN TEXT COLUMNS ===
{cat_vals_str}

=== SAMPLE DATA (first 5 rows) ===
{json.dumps(SAMPLE_ROWS, indent=2, default=str)}

=== RECENT CONVERSATION ===
{mem_text}

=== USER QUESTION ===
{question}

=== AVAILABLE VARIABLES (do NOT import or redefine) ===
  df           → the full pandas DataFrame
  pd           → pandas
  np           → numpy
  plt          → matplotlib.pyplot
  PALETTE      → list of hex colors: {PALETTE}
  save_chart  → function(fig) saves chart and returns its URL

=== RULES ===
1. Filter case-insensitively:
   df[df['region'].str.lower() == 'west']

2. Date columns are datetime. Use:
   df['order_date'].dt.year
   df['order_date'].dt.month

3. Always check for empty results:
   if filtered.empty:
       result_text = "No data found."

4. Always set result_text — never leave it undefined.

5. Format numbers:
   f"{{value:,.2f}}"  → 1,234,567.89
   f"{{value:,}}"     → 1,234,567

6. One chart maximum. Skip chart if just one number.

7. Do NOT write import statements.

8. - You MUST output ONLY Python code
- No explanations
- No greetings
- No English text
- No markdown
- Output must start immediately with Python code

If you do not follow this, the system will fail.

{CHART_STYLE}

Write ONLY Python code. No explanations. No markdown. Start directly.
"""
    return prompt

def save_chart_fn(fig):
    """
    Defines the path where the charts must be saved.
    """

    # 'hex' removes '-' from the unique id
    unique_id = uuid.uuid4().hex
    fname = f"{unique_id}.png"
    fpath = os.path.join(CHART_DIR, fname)
    plt.savefig(fpath,
                dpi=130, # Normal image iquality
                bbox_inches='tight', # To get clean margin
                facecolor='#0f1117' # BgColor
                )
    plt.close('all')
    
    return (f'static/charts/{fname}')

def extract_code(raw):
    """
    Removes markdowns ``` that Claude may generates in his response.
    """

    # remove any 'python' and the first markdown in the response 
    raw = re.sub(
        r"```(?:python)?\s*",
        "", 
        raw)
    # remove the markdown of the response
    raw = re.sub(f"```", 
                 "", 
                 raw)

    cleaned = raw.strip()
    if not cleaned or "Hello" in cleaned or "How can I help" in cleaned:
        return ""

    return cleaned

def execute_code(code):
    """
    Execute the code that Claude generated.
    """
    namespace = {
        'df': df.copy(), # To avoid deleting something needed
        'pd': pd,
        'np': np,
        'plt': plt,
        'json': json,
        'PALETTE': PALETTE,
        'save_chart': save_chart_fn,
        'result_text': None,
        'chart_path': None
    }

    old_stdout = sys.stdout
    # Fake file to store the printed text
    sys.stdout = io.StringIO()
    try:
        logger.info("=== GENERATED CODE START ===")
        logger.info(code)
        logger.info("=== GENERATED CODE END ===")
        exec(
            compile(
                code,
                '<generated>',
                'exec'
            ),
            namespace
        )
        # Get the printed value in that fake file
        printed = sys.stdout.getvalue()
    except Exception as e:
        sys.stdout = old_stdout
        error_details = traceback.format_exc()
        logger.error(
            f'Execution failed: {error_details}'
        )

        return {
            'text': f'Error: {e}',
            'chart': None,
            'error': error_details
        }
    finally:
        sys.stdout = old_stdout

    if printed:
        logger.debug(
            f"Code printed: {printed[:200]}"
        )

    result_text = namespace.get('result_text')
    chart_path = namespace.get('chart_path')
    if result_text is None:
        result_text = (
            'Done. No text result was produced.'
        )

    return {
        'text': str(result_text),
        'chart': 
            chart_path
            if isinstance(chart_path, str)
            else None,
        'error': None
    }

def run_analysis(question, lang='en', memory=None):

    if memory is None:
        memory = []
    
    logger.info(
        f"Question: {question[:80]}"
    )

    prompt = build_prompt(
        question,
        lang,
        memory
    )

    raw_code = call_claude(
        prompt,
        max_tokens=2000
    )
    logger.info("=== RAW CODE ===")
    logger.info(raw_code)

    code = extract_code(raw_code)
    logger.info("=== CLEAN CODE ===")
    logger.info(code)

    logger.info(
        f"Generated {len(code)} chars of code"
    )

    if not is_safe_code(code):
        reason = get_block_reason(code)
        
        return {
            'text': (
                f"Requete bloquee: {reason}."
                if lang == 'fr' else
                f"Query blocked: {reason}."
            ),
            'chart': None,
            'error': None
        }

    result = execute_code(code)

    if result['error']:
        logger.warning('First attempt failed - retrying')
        retry_prompt = prompt + f"""
=== YOUR PREVIOUS CODE HAD AN ERROR ===
Code:
{code}

Error:
{result['error']}

Write CORRECTED code only.
"""
        raw_code2 = call_claude(retry_prompt, max_tokens=2000)
        code2 = extract_code(raw_code2)
        if not is_safe_code(code2):
            reason = get_block_reason(code2)
            
            return {
                'text': (
                    f"Requete bloquee: {reason}."
                    if lang == 'fr' else
                    f"Query blocked: {reason}."
                ),
                'chart': None,
                'error': None
            }
        
        result = execute_code(code2)
        if result['error']:
            logger.error('Both attempts failed.')
            result['text'] = (
                "Je n'ai pas pu analyser cette question."
                if lang == 'fr' else
                "I could not analyze this question. Please try rephrasing."
            )
            result['chart'] = None
            result['error'] = None

    logger.info('Analysis complete.')
    return result