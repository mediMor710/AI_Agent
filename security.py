import re
import logging

logger = logging.getLogger(__name__)

##### SECURITY WALL IN THE PROMPT #####

BLOCKED_PATTERNS = [
    # Reporting the keywords that allow to harm the files system
    r'\bos\.(remove|unlink|rmdir|system|popen|execv|fork)\b',

    # Reporting the keywords that allow to operate inside the files 
    r'\bshutil\.(rmtree|move|copy2?|copytree|disk_usage)\b',

    # Reporting the keyword that allow to open a file
    r'open\s*\([^)]*["\'][wa]["\']',

    # Not allowing to run shell commands in python
    r'\bsubprocess\b',
    r'\bos\.system\b',
    r'\b__import__\s*\(',
    
    # Not allowing to run a string as code
    r'\beval\s*\(',
    r'\bcompile\s*\(',

    # Network access 
    r'\b(requests|urllib|http\.client|socket)\b',
    r'\bgetattr\s*\([^,]+,\s*["\']__',
]


##### THE SAFETY CHECK FUNCTION #####
def is_safe_code(code):
    """
    Checks the code that claude generated if safe to run.
    """
    
    for pattern in BLOCKED_PATTERNS:

        found = re.search(pattern, code, re.IGNORECASE)
        if found:
            logger.warning(f'Blocked dangerous pattern: {pattern}')
            return False

    return True

def get_block_reason(code):
    """
    returns a description of why the code was blocked.
    """

    descriptions = [
        (r'\bos\.(remove|unlink|rmdir|system|popen|execv|fork)\b',
         "Dangerous OS file/system operation"),
 
        (r'\bshutil\.(rmtree|move|copy2?|copytree|disk_usage)\b',
         "Dangerous file manipulation (shutil)"),
 
        (r'open\s*\([^)]*["\'][wa]["\']',
         "Attempt to write or overwrite a file"),
 
        (r'\bsubprocess\b',
         "Attempt to run external shell command (subprocess)"),
 
        (r'\b__import__\s*\(',
         "Sneaky import attempt (__import__)"),
 
        (r'\beval\s*\(',
         "Dynamic code execution attempt (eval)"),
 
        (r'\bcompile\s*\(',
         "Dynamic code compilation attempt (compile)"),
 
        (r'\b(requests|urllib|http\.client|socket)\b',
         "Network access attempt"),
 
        (r'\bgetattr\s*\([^,]+,\s*["\']__',
         "Sandbox escape attempt (getattr with dunder)"),
    ]

    for pattern, description in descriptions:
        
        if re.search(pattern, code, re.IGNORECASE):
            return description
        
    return "safe"