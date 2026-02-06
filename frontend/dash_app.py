import dash
from dash import dcc, html, Input, Output, State, callback
import dash_auth
import base64
import requests

# Authentication
VALID_USERNAME_PASSWORD_PAIRS = {'demo': 'demo', 'admin': 'yourpassword'}
app = dash.Dash(__name__)
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
            multiple=False
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
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        sas_code = decoded.decode('utf-8')
        return f"📄 File loaded: {filename}", {'filename': filename, 'code': sas_code}
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
    if file_data is None:
        return "❌ Please upload a file first.", {'display': 'block'}
    
    API_URL = "http://localhost:8000/parse"
    
    try:
        response = requests.post(API_URL, json={"code": file_data['code']})
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                # Check for blueprint data
                if 'blueprint' in data:
                    bp = data['blueprint']
                    
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
                    return display, {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}
                else:
                    # Fallback if no blueprint
                    return f"✅ Parsed. Tokens: {len(data.get('tokens', []))}, Errors: {len(data.get('errors', []))}", {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}
            else:
                return f"❌ Backend error: {data.get('error', 'Unknown')}", {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}
        else:
            return f"❌ HTTP error: {response.status_code}", {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}
    except Exception as e:
        return f"⚠️ Connection error: {e}", {'padding': '20px', 'border': '1px solid #ddd', 'margin': '20px', 'display': 'block'}

if __name__ == '__main__':
    app.run(debug=True, port=8050)