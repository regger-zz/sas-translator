import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
VALID_CREDENTIALS = {
    'demo': 'demo',
    'admin': os.getenv('ADMIN_PASSWORD', 'yourpassword')
}

# ============================================================================
# HTTP Basic Authentication
# ============================================================================
def check_auth(username, password):
    return username in VALID_CREDENTIALS and VALID_CREDENTIALS[username] == password

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ============================================================================
# Routes
# ============================================================================
@app.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    """Upload page."""
    if request.method == 'POST':
        # Check file
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if not file.filename.endswith('.sas'):
            flash('Please upload a .sas file')
            return redirect(request.url)

        # Read file content
        try:
            code = file.read().decode('utf-8', errors='replace')
        except Exception as e:
            flash(f"Error reading file: {str(e)}")
            return redirect(request.url)

        # Call backend /parse endpoint
        try:
            response = requests.post(f"{BACKEND_URL}/parse", json={"code": code})
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            flash(f"Backend communication error: {str(e)}")
            return redirect(request.url)
        except ValueError:
            flash("Backend did not return valid JSON")
            return redirect(request.url)

        # Check backend success
        if not data.get('success'):
            flash(f"Backend error: {data.get('error', 'Unknown error')}")
            return redirect(request.url)

        # Extract data
        blueprint = data.get('blueprint', {})
        tokens = data.get('tokens', [])
        errors = data.get('errors', [])

        # Determine if translation button should be shown
        summary = blueprint.get('summary', {})
        priority = summary.get('translation_priority', 'Low')
        complexity = summary.get('complexity_score', 0)
        show_button = (priority in ['Low', 'Medium', 'High']) and (complexity < 100)

        # Render blueprint page
        return render_template('blueprint.html',
                               filename=file.filename,
                               blueprint=blueprint,
                               tokens=tokens,
                               errors=errors,
                               show_button=show_button,
                               original_code=code)

    # GET request – show upload form
    return render_template('upload.html')

@app.route('/translate', methods=['POST'])
@requires_auth
def translate():
    """Receive original code from form, send to backend /translate, show result."""
    original_code = request.form.get('original_code')
    print("FORM DATA:", request.form)
    if not original_code:
        flash('No original code provided')
        return redirect(url_for('index'))

    # Call backend /translate endpoint
    try:
        payload = {
            "code": original_code,
            "target_language": "python"
        }
        response = requests.post(f"{BACKEND_URL}/translate", json=payload)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        flash(f"Translation failed: {str(e)}")
        return redirect(url_for('index'))
    except ValueError:
        flash("Backend did not return valid JSON")
        return redirect(url_for('index'))

    # Check backend success
    if not data.get('success'):
        flash(f"Translation error: {data.get('error', 'Unknown error')}")
        return redirect(url_for('index'))

    # Extract translation from response
    translation = data.get('translation', '')
    return render_template('result.html', translation=translation)

if __name__ == '__main__':
    app.run(debug=True, port=5000)