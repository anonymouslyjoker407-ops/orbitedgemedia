import os
from flask import Flask, render_template_string, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
# Render pe secure session ke liye secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'orbitage-secret-key-2026')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple User Model (Aap yahan apne credentials change kar sakte ho)
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':
        return User('1', 'admin')
    return None

# --- HTML TEMPLATES (Inline for single-file deployment) ---

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orbitage CM - Tools Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; }
        .btn-custom { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); border: none; color: white; transition: 0.3s; }
        .btn-custom:hover { opacity: 0.9; transform: translateY(-1px); color: white; }
    </style>
</head>
<body>
    <div class="container py-4">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

LOGIN_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="row justify-content-center align-items-center min-vh-100">
    <div class="col-md-4">
        <div class="text-center mb-4">
            <h2 class="fw-bold text-info"><i class="fas fa-cube me-2"></i>Orbitage CM</h2>
            <p class="text-muted">Sign in to access your web tools</p>
        </div>
        <div class="card glass-card p-4 shadow-lg">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-danger py-2 mb-3 small">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label text-sm">Username</label>
                    <input type="text" name="username" class="form-control bg-dark text-light border-secondary" required autocomplete="off">
                </div>
                <div class="mb-4">
                    <label class="form-label text-sm">Password</label>
                    <input type="password" name="password" class="form-control bg-dark text-light border-secondary" required>
                </div>
                <button type="submit" class="btn btn-custom w-100 py-2 fw-semibold">Login to Dashboard</button>
            </form>
        </div>
    </div>
</div>
""")

DASHBOARD_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="d-flex justify-content-between align-items-center mb-5 border-bottom border-secondary pb-3">
    <div>
        <h3 class="fw-bold text-info m-0"><i class="fas fa-rocket me-2"></i>Orbitage CM Orbitage Tools</h3>
        <p class="text-muted m-0 small">Welcome back, {{ current_user.username }}!</p>
    </div>
    <a href="{{ url_for('logout') }}" class="btn btn-outline-danger btn-sm"><i class="fas fa-sign-out-alt me-1"></i> Logout</a>
</div>

<div class="row g-4">
    <div class="col-md-6">
        <div class="card glass-card p-4 h-100 shadow-sm">
            <div class="d-flex align-items-center mb-3">
                <div class="bg-primary bg-opacity-15 p-3 rounded-3 text-primary me-3">
                    <i class="fas fa-terminal fa-lg text-info"></i>
                </div>
                <div>
                    <h5 class="fw-bold mb-1">Script One</h5>
                    <p class="text-muted small m-0">Run your primary web tool utility.</p>
                </div>
            </div>
            <a href="{{ url_for('run_script', script_id=1) }}" class="btn btn-custom mt-auto w-100"><i class="fas fa-play me-1"></i> Launch Script 1</a>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card glass-card p-4 h-100 shadow-sm">
            <div class="d-flex align-items-center mb-3">
                <div class="bg-purple bg-opacity-15 p-3 rounded-3 text-purple me-3">
                    <i class="fas fa-code fa-lg text-warning"></i>
                </div>
                <div>
                    <h5 class="fw-bold mb-1">Script Two</h5>
                    <p class="text-muted small m-0">Execute your secondary automated process.</p>
                </div>
            </div>
            <a href="{{ url_for('run_script', script_id=2) }}" class="btn btn-custom mt-auto w-100"><i class="fas fa-play me-1"></i> Launch Script 2</a>
        </div>
    </div>
</div>
""")

SCRIPT_VIEW_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="mb-4">
    <a href="{{ url_for('dashboard') }}" class="btn btn-outline-light btn-sm"><i class="fas fa-arrow-left me-1"></i> Back to Dashboard</a>
</div>
<div class="card glass-card p-4 shadow-lg">
    <h4 class="text-info fw-bold mb-3"><i class="fas fa-laptop-code me-2"></i>Execution Result: Script {{ script_id }}</h4>
    <div class="bg-black p-3 rounded border border-secondary font-monospace text-success" style="min-height: 200px;">
        {{ output }}
    </div>
</div>
""")

# --- ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Yahan aap apna username aur password set kar sakte ho
        if username == 'admin' and password == 'orbitage2026':
            user = User('1', username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
            
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/script/<int:script_id>')
@login_required
def run_script(script_id):
    # Yahan aap apni script_1.py ya script_2.py ko import karke execute kar sakte ho
    output_text = ""
    if script_id == 1:
        # Example output for Script 1
        output_text = "[SUCCESS] Script 1 executed successfully on server.\nOutput data from Script 1 logic..."
    elif script_id == 2:
        # Example output for Script 2
        output_text = "[SUCCESS] Script 2 execution completed.\nProcessed background data stream..."
    else:
        output_text = "[ERROR] Invalid script selected."
        
    return render_template_string(SCRIPT_VIEW_TEMPLATE, script_id=script_id, output=output_text)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
