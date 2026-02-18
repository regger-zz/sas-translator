"""
SAS Parser API - Backend for the SAS QA Translation Tool
This is the FastAPI application that provides the parsing endpoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sas_lexer  # This is the critical Rust-based parser
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Initialize the FastAPI application
app = FastAPI(
    title="SAS Parser API",
    description="API for lexing and analyzing SAS code. Powers the SAS QA Translation Frontend.",
    version="1.0.0"
)

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8050"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# --- Data Model ---
class SASCode(BaseModel):
    """Pydantic model for the incoming SAS code string."""
    code: str

class TranslationRequest(BaseModel):
    """Request model for the /translate endpoint."""
    tokens: List[Dict[str, Any]]  # The parsed token list from /parse
    target_language: Optional[str] = "python"  # Options: "python", "sql"

# ====================
# BLUEPRINT GENERATION
# ====================
def generate_blueprint(serializable_tokens, raw_sas_code):
    """
    Analyze SAS tokens to create a translation blueprint.
    Works with serialized token dictionaries from sas_lexer.
    """
    # Initialize counters and trackers
    analysis = {
        "data_steps": 0,
        "proc_blocks": 0,
        "proc_sql_blocks": 0,
        "macro_definitions": 0,
        "macro_calls": 0,
        "proc_types": set(),
        "datasets_created": set(),
        "datasets_used": set(),
        "has_retain": False,
        "has_lag": False,
        "has_merge": False,
        "has_arrays": False,
        "in_data_step": False,
        "in_proc_block": False,
        "current_proc": None,
        "pointer_controls": 0,
        "line_hold_single": False,
        "line_hold_double": False,
        "platform_concerns": [],
        "has_proc_import": False,
    }
    
    # Helper: Safe token text extraction (WORKS WITH DICTIONARIES)
    def get_token_text_safe(token_idx):
        if token_idx >= len(serializable_tokens) or token_idx < 0:
            return None
        token = serializable_tokens[token_idx]
        start = token.get('start')
        stop = token.get('stop')
        if start is not None and stop is not None and isinstance(start, int) and isinstance(stop, int):
            return raw_sas_code[start:stop].upper()
        return token.get('text', '').upper()
    
    # Helper: Safe token type check (WORKS WITH DICTIONARIES)
    def get_token_type_safe(token_idx):
        if token_idx >= len(serializable_tokens) or token_idx < 0:
            return None
        token = serializable_tokens[token_idx]
        token_type = token.get('token_type')
        
        # Convert TokenType object to string if needed
        if token_type is None:
            return None
        elif hasattr(token_type, 'name'):  # It's a TokenType object
            return token_type.name
        else:  # It's already a string
            return str(token_type)
    
    # ========== MAIN PROCESSING LOOP ==========
    i = 0
    while i < len(serializable_tokens):
        token_text = get_token_text_safe(i)
        token_type = get_token_type_safe(i)

        # 1. IMMEDIATELY skip whitespace and comments
        if token_type in ['WS', 'COMMENT']:
            i += 1
            continue

        # 2. NOW, run ALL original detection logic
        # Example: DATA step detection 
        if token_text == 'DATA' and not analysis["in_data_step"]:
            next_text = get_token_text_safe(i+1)
            if next_text and next_text not in ['_NULL_', 'STEP', '='] and not next_text.startswith('('):
                analysis["data_steps"] += 1
                analysis["in_data_step"] = True
                # ... KEEP ALL ORIGINAL DATA STEP LOGIC ...

        # --- PROC BLOCK DETECTION ---
        elif token_text == 'PROC':
            print(f"  [PROC DETECTED] At token i={i}, text='{token_text}'")
            # Find procedure name, skipping whitespace
            proc_pos = i + 1
            while proc_pos < len(serializable_tokens) and get_token_type_safe(proc_pos) in ['WS', 'COMMENT']:
                proc_pos += 1
            
            if proc_pos < len(serializable_tokens):
                proc_name = get_token_text_safe(proc_pos)
                print(f"    Found proc_name='{proc_name}' at position {proc_pos}")
                if proc_name and proc_name.isalpha():
                    proc_name = proc_name.upper()
                    analysis["proc_types"].add(proc_name)
                    analysis["proc_blocks"] += 1
                    print(f"    -> SUCCESS: Added PROC block. Total now: {analysis['proc_blocks']}")
                    analysis["in_proc_block"] = True
                    analysis["current_proc"] = proc_name
                    if proc_name == 'SQL':
                        analysis["proc_sql_blocks"] += 1
        # --- END OF DETECTION LOGIC ---

        # 3. CRITICAL: Increment i ONCE, here at the end
        i += 1

        # =====================================
        
        # --- ORIGINAL ANALYSIS LOGIC GOES HERE ---
        # (Keep all detection logic for DATA, PROC, etc.)
        # Example: DATA step detection
        if token_text == 'DATA' and not analysis["in_data_step"]:
            next_text = get_token_text_safe(i+1)
            if next_text and next_text not in ['_NULL_', 'STEP', '='] and not next_text.startswith('('):
                analysis["data_steps"] += 1
                analysis["in_data_step"] = True
                # ... rest of the DATA step logic ...
        
        # PROC detection, macro detection, etc.
        # ...
        # ==============================================
        
        # INCREMENT INDEX (for all non-skipped tokens)
        i += 1
    
    # --- CALCULATE COMPLEXITY SCORE (existing code) ---
    complexity_score = (
        analysis["data_steps"] * 1 +
        analysis["proc_blocks"] * 1 +
        analysis["proc_sql_blocks"] * 2 +
        analysis["macro_definitions"] * 5 +
        analysis["macro_calls"] * 2 +
        (5 if analysis["has_retain"] else 0) +
        (5 if analysis["has_lag"] else 0) +
        (3 if analysis["has_merge"] else 0) +
        (3 if analysis["has_arrays"] else 0) +
        (analysis["pointer_controls"] * 2) +
        (10 if analysis["line_hold_double"] else 0) +
        (8 if analysis["line_hold_single"] else 0) +
        (len(analysis["platform_concerns"]) * 3) +
        (10 if analysis["has_proc_import"] else 0)
    )
    
       # --- DETERMINE PRIORITY ---
    if complexity_score > 25:
        priority = "High"
        confidence = "Manual review strongly recommended"
    elif complexity_score > 15:
        priority = "Medium"
        confidence = "Mixed automation with oversight"
    else:
        priority = "Low"
        confidence = "Good candidate for automated translation"
    
    # --- GENERATE RECOMMENDATIONS ---
    recommendations = []
    if analysis["macro_definitions"] > 0:
        recommendations.append("Manual review required for custom macro definitions.")
    if analysis["proc_sql_blocks"] > 0:
        recommendations.append(f"Verify logic of {analysis['proc_sql_blocks']} PROC SQL block(s).")
    if analysis["has_retain"]:
        recommendations.append("RETAIN statements require stateful translation logic.")
    if analysis["has_lag"]:
        recommendations.append("LAG functions need special handling for row context.")
    if analysis["pointer_controls"] > 0:
        recommendations.append(f"Column pointer controls (@) detected: {analysis['pointer_controls']} instance(s). Requires careful input parsing translation.")
    if analysis["line_hold_single"]:
        recommendations.append("Single trailing @ detected: Line hold requires stateful INPUT buffer management.")
    if analysis["line_hold_double"]:
        recommendations.append("Double trailing @@ detected: Complex line hold across multiple records.")
    if analysis["platform_concerns"]:
        unique_concerns = list(set(analysis["platform_concerns"]))
        concerns_text = ", ".join(sorted(unique_concerns))
        recommendations.append(f"Platform-specific code: {concerns_text}. Review for portability.")
    if analysis["has_proc_import"]:
        recommendations.append("PROC IMPORT detected: Requires manual mapping to pandas.read_csv()/read_excel() with specific parameter analysis.")
    if not recommendations:
        recommendations.append("Code structure appears straightforward for automated translation.")

    # --- STRUCTURE FINAL BLUEPRINT ---
    blueprint = {
        "summary": {
            "translation_priority": priority,
            "confidence_assessment": confidence,
            "complexity_score": complexity_score,
            "total_lines": len(raw_sas_code.split('\n')),
            "total_tokens": len(serializable_tokens)
        },
        "detailed_counts": {
            "DATA Steps": analysis["data_steps"],
            "PROC Blocks": analysis["proc_blocks"],
            "PROC SQL Blocks": analysis["proc_sql_blocks"],
            "Macro Definitions": analysis["macro_definitions"],
            "Macro Calls": analysis["macro_calls"],
            "PROC Types Found": list(sorted(analysis["proc_types"]))
        },
        "data_flow": {
            "datasets_created": list(sorted(analysis["datasets_created"])),
            "datasets_used": list(sorted(analysis["datasets_used"]))
        },
        "complexity_flags": {
            "has_retain_statement": analysis["has_retain"],
            "has_lag_function": analysis["has_lag"],
            "has_merge_statement": analysis["has_merge"],
            "has_array_declarations": analysis["has_arrays"],
            "pointer_controls_count": analysis["pointer_controls"],
            "has_line_hold_single": analysis["line_hold_single"],
            "has_line_hold_double": analysis["line_hold_double"],
            "platform_concerns": analysis["platform_concerns"]
        },
        "recommendations": recommendations
    }
    
    return blueprint
# --- API Endpoints ---
@app.post("/parse")
def parse_sas(sas_input: SASCode):
    """
    Main parsing endpoint.
    Accepts a JSON object with a 'code' field containing the SAS code.
    Returns the lexed tokens, any errors, and the full analysis blueprint.
    """
    try:
        # 1. Call the lexer
        tokens, errors, _ = sas_lexer.lex_program_from_str(sas_input.code)
        
        # 2. Convert complex Token objects AND Error objects to serializable format
        serializable_tokens = []
        if hasattr(tokens, '__iter__'):
            for token in tokens:
                try:
                    token_dict = vars(token)
                    filtered_dict = {k: v for k, v in token_dict.items() if isinstance(v, (str, int, float, bool, type(None)))}
                    serializable_tokens.append(filtered_dict)
                except TypeError:
                    # Handle Error objects specifically
                    if hasattr(token, 'message'):  # Likely an Error object
                        serializable_tokens.append({
                            "type": "error",
                            "message": str(getattr(token, 'message', 'Unknown error')),
                            "repr": repr(token)
                        })
                    else:
                        serializable_tokens.append({
                            "repr": repr(token),
                            "text": getattr(token, 'text', 'N/A'),
                            "start": getattr(token, 'start', 'N/A'),
                            "stop": getattr(token, 'stop', 'N/A'),
                            "token_type": getattr(token, 'token_type', 'N/A')
                        })
        else:
            serializable_tokens = str(tokens)
        
        # 3. ALSO serialize any Error objects in the errors list
        serializable_errors = []
        for err in errors:
            if hasattr(err, 'message'):
                serializable_errors.append({
                    "type": "error",
                    "message": str(getattr(err, 'message', 'Unknown error')),
                    "repr": repr(err)
                })
            else:
                serializable_errors.append(str(err))  # Fallback

        # 4. Generate the blueprint
        blueprint = generate_blueprint(serializable_tokens, sas_input.code)
        
        # 5. Return everything
        return {
            "success": True,
            "tokens": serializable_tokens,
            "errors": serializable_errors,  # CRITICAL: Use the serialized version
            "blueprint": blueprint
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Parsing failed: {str(e)}"
        }

@app.get("/")
def read_root():
    """Simple health check endpoint."""
    return {"message": "SAS Parser API is running"}

@app.get("/health")
def health_check():
    """Explicit health check for monitoring."""
    return {"status": "healthy"}

 # --- Add the New Endpoint ---
@app.post("/translate")
async def create_translation(request: TranslationRequest):
    """
    Generate a translation from SAS tokens to the target language.
    """
    tokens = request.tokens
    target = request.target_language

    # 1. LOGGING (Very useful for debugging)
    print(f"[INFO] /translate called. Tokens: {len(tokens)}, Target: {target}")

    # 2. TODO: INTEGRATE YOUR LEGACY TRANSLATION LOGIC HERE
    # ======================================================
    # This is the critical step. You will call your actual conversion function.
    # For now, we create a structured placeholder.
    # translated_code = your_actual_conversion_function(tokens, target)
    # ======================================================

    # Placeholder logic demonstrating structure
    translated_code_placeholder = f"""# SAS to {target.capitalize()} Translation (Placeholder)
# Analysis based on {len(tokens)} parsed tokens.

# DATA step and PROC logic would be converted here.
print("Translation engine ready. Integrate conversion function.")"""

    # 3. Return a structured response
    return {
        "success": True,
        "target_language": target,
        "translated_code": translated_code_placeholder,
        "metadata": {
            "tokens_processed": len(tokens),
            "translation_engine": "sas-translator-v1"
        }
    }