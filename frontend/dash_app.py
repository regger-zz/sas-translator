import dash
from dash import dcc, html, Input, Output, State, callback
import dash_auth
import base64
import requests

# Authentication
VALID_USERNAME_PASSWORD_PAIRS = {'demo': 'demo', 'admin': 'yourpassword'}
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True 
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)
app.title = "SAS QA Translation Framework (Dash)"

# Layout - MUST include dcc.Store that callbacks reference
app.layout = html.Div([
    html.H1("🔬 SAS-to-SQL/Python QA Translation Framework", style={'textAlign': 'center'}),
    
    html.Div([
        html.H3("📁 Stage 1: Upload & Analyze"),
        dcc.Upload(
            id='upload-sas',
            children=html.Div(['Drag and Drop or ', html.A('Select a SAS File (.sas)')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                'textAlign': 'center', 'margin': '10px'
            },
            multiple=False,
            accept='.sas'  
        ),
        html.Button('🔍 Generate Analysis Blueprint', id='analyze-button', n_clicks=0,
                   style={'margin': '10px', 'padding': '10px'}),
        html.Div(id='output-file-name'),
    ], style={'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px'}),
    
    # Results area
    html.Div([
        html.H3("📋 Analysis Blueprint"),
        html.Div(id='blueprint-output', style={'whiteSpace': 'pre-wrap'})
    ], id='results-section', style={'padding': '20px', 'display': 'none'}),
    
    # CRITICAL: This Store component MUST exist for callbacks to work
    dcc.Store(id='stored-file-content'),
])

# Callback 1: Store uploaded file
@callback(
    Output('output-file-name', 'children'),
    Output('stored-file-content', 'data'),
    Input('upload-sas', 'contents'),
    State('upload-sas', 'filename')
)
def store_uploaded_file(contents, filename):
    """Stores the uploaded file's content and shows its name."""
    if contents is not None:
        try:
            # 1. Split the base64 string
            content_type, content_string = contents.split(',')
            # 2. Decode from base64
            decoded = base64.b64decode(content_string)
            # 3. Decode bytes to string, REPLACING invalid characters
            sas_code = decoded.decode('utf-8', errors='replace')
            # Optional: Clean common problematic characters
            sas_code = sas_code.replace('\r', ' ')  # Replace carriage returns
            sas_code = sas_code.replace('\x00', ' ') # Replace null bytes
            return f"📄 File loaded: {filename}", {'filename': filename, 'code': sas_code}
        except Exception as e:
            return f"❌ Error processing file: {str(e)}", None
    return "No file uploaded.", None

# Callback 2: Generate blueprint
@callback(
    Output('blueprint-output', 'children'),
    Output('results-section', 'style'),
    Input('analyze-button', 'n_clicks'),
    State('stored-file-content', 'data'),
    prevent_initial_call=True
)
def generate_blueprint(n_clicks, file_data):

    # Initialize button_section with an empty Div to avoid reference errors
    button_section = html.Div()  # <-- ADD THIS LINE
    if file_data is None:
        return "❌ Please upload a file first.", {'display': 'block'}
        
    API_URL = "http://localhost:8000/parse"
    
    try:
        # DEBUG: Inspect the raw data being sent
        print("=== DEBUG START ===")
        print(f"Raw code type: {type(file_data['code'])}")
        print(f"Raw code length: {len(file_data['code'])}")
        # Show first 200 characters and their raw representation
        sample = file_data['code'][:200]
        print(f"Code sample (raw): {repr(sample)}")
        print("=== DEBUG END ===")

        response = requests.post(API_URL, json={"code": file_data['code']})
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                # Check for blueprint data
                if 'blueprint' in data:
                    bp = data['blueprint']

# --- START OF CONDITIONAL BUTTON LOGIC --
                    bp_summary = bp.get('summary', {})
                    priority = bp_summary.get('translation_priority')
                    complexity = bp_summary.get('complexity_score', 100)

# Define thresholds
                    PRIORITY_THRESHOLD = PRIORITY_THRESHOLD = ['Low', 'Medium', 'High']  # Shows for all
                    COMPLEXITY_THRESHOLD = 100  # Adjust this based on testing

                    print(f"Priority value: '{bp['summary']['translation_priority']}'") 
                    print(f"Threshold: {PRIORITY_THRESHOLD}")
                    print(f"Button should show: {bp['summary']['translation_priority'] in PRIORITY_THRESHOLD}")
# Decision logic
                    show_button = (priority in PRIORITY_THRESHOLD) and (complexity < COMPLEXITY_THRESHOLD)
                    print(f"[DEBUG] show_button is: {show_button}")
                    print(f"[DEBUG] button_section type: {type(button_section)}")

# Prepare the button section
                    if show_button:
                        button_section = html.Div([
                            html.Hr(),
                            html.Button('🚀 Generate Translation', id='btn-translate', n_clicks=0),
                            # CRITICAL: Store the tokens for Callback 3 to use
                            dcc.Store(id='store-parsed-tokens', data=data['tokens']),
                            html.Div(id='translation-output', style={'marginTop': '20px'})
                        ])
                    else:
                        button_section = html.Div([
                            html.Hr(),
                            html.P("ℹ️ Translation not recommended for this code's complexity or priority.",
                            style={'color': 'gray', 'fontStyle': 'italic'})
                    ])
# --- END OF CONDITIONAL BUTTON LOGIC ---

                    # Build the display
                    display = html.Div([
                        html.H4(f"✅ Analysis Complete: {file_data['filename']}"),
                        html.P(f"🏷️ Translation Priority: {bp['summary']['translation_priority']}"),
                        html.P(f"🧮 Complexity Score: {bp['summary']['complexity_score']}"),
                        html.P(f"📈 Total Lines: {bp['summary']['total_lines']}"),
                        html.Hr(),
                        html.H5("🔍 Detailed Counts"),
                        html.P(f"📝 DATA Steps: {bp['detailed_counts']['DATA Steps']}"),
                        html.P(f"⚙️ PROC Blocks: {bp['detailed_counts']['PROC Blocks']}"),
                        html.P(f"🗃️ PROC SQL Blocks: {bp['detailed_counts']['PROC SQL Blocks']}"),
                        html.Hr(),
                        html.H5("💡 Recommendations"),
                        html.Ul([html.Li(rec) for rec in bp['recommendations']]),
                        html.Hr(),
                        html.P(f"Tokens Found: {len(data.get('tokens', []))}"),
                        html.P(f"Errors Found: {len(data.get('errors', []))}")
                    ])
                    # Combine the main display with the button section
                    final_display = html.Div([
                        display,    # original analysis results
                        button_section  # The new conditional button and placeholder
                    ])

                    print(f"[DEBUG] button_section in final_display: {button_section in final_display.children}")

                    # === ADD THESE DEBUG LINES ===
                    print(f"[DEBUG] Condition check - Priority: {priority} (in {PRIORITY_THRESHOLD}?), Complexity: {complexity} ( < {COMPLEXITY_THRESHOLD}?)")
                    print(f"[DEBUG] show_button result: {show_button}")
                    print(f"[DEBUG] Type of button_section: {type(button_section)}")
                    print(f"[DEBUG] Checking for 'translation-output' in button_section...")
                    # What's actually in button_section?
                    if button_section:
                        print(f"button_section has {len(button_section.children)} children")
                        for i, child in enumerate(button_section.children):
                            print(f"  child {i}: {child}")
                    else:
                        print("button_section is None or empty")   

                    # Simple check: if button_section is a Div, look at its children's IDs
                    if hasattr(button_section, 'children'):
                        for i, child in enumerate(button_section.children):
                            if hasattr(child, 'id') and child.id:
                                print(f"  Child {i} ID: {child.id}")
                    # ==============================

                    final_display = html.Div([display, button_section])
                    return final_display, {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}
                else:
                    # Fallback if no blueprint
                    return f"✅ Parsed. Tokens: {len(data.get('tokens', []))}, Errors: {len(data.get('errors', []))}", {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}
            else:
                return f"❌ Backend error: {data.get('error', 'Unknown')}", {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}
        else:
            return f"❌ HTTP error: {response.status_code}", {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}
    except Exception as e:
        return f"⚠️ Connection error: {e}", {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}

# Add this import at the top if not present 
import requests

# New Callback 3
@callback(
    Output('translation-output', 'children'),
    Input('btn-translate', 'n_clicks'),
    State('stored-file-content', 'data'),  # ← Change this line
    prevent_initial_call=True
)
def call_translate_endpoint(n_clicks, tokens):
    print(f"Button clicked! n_clicks={n_clicks}")
    if n_clicks > 0:
        try:
            # 1. Call your new Part 2 endpoint
            sas_code = tokens['code']  # tokens is your stored data dict
            response = requests.post(
               'http://localhost:8000/translate',
                json={
        "tokens": [],  # Empty list
        "code": sas_code,  # Your code
        "target_language": "python"
    }
            )
            result = response.json()

            # 2. Display the result
            if result.get('success'):
                return html.Div([
                    html.H5("📄 Generated Translation:"),
                    dcc.Markdown(f'''```python\n{result['translation']}\n```''')
                ])
            else:
                return html.Div(f"Translation failed: {result}", style={'color': 'red'})
        except Exception as e:
            return html.Div(f"Error contacting translation service: {e}", style={'color': 'red'})
    return ""  # Return nothing if button hasn't been clicked

if __name__ == '__main__':
    app.run(debug=True, port=8050)