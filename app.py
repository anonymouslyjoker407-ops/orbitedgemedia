import os
from flask import Flask, render_template_string, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from script_1 import script1_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'orbitage-secret-key-2026')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':
        return User('1', 'admin')
    return None

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orbitage CM - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0b0f19; color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .glass-card { background: rgba(30, 41, 59, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; }
        .btn-custom { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); border: none; color: white; }
        .btn-custom:hover { background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); color: white; }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-md-4">
                <div class="text-center mb-4">
                    <h2 class="fw-bold text-primary"><i class="fas fa-cube me-2"></i>Orbitage CM</h2>
                    <p class="text-muted">GitHub-Powered Secure Tools Suite</p>
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
                            <label class="form-label small">Username</label>
                            <input type="text" name="username" class="form-control bg-dark text-light border-secondary" required autocomplete="off">
                        </div>
                        <div class="mb-4">
                            <label class="form-label small">Password</label>
                            <input type="password" name="password" class="form-control bg-dark text-light border-secondary" required>
                        </div>
                        <button type="submit" class="btn btn-custom w-100 py-2 fw-semibold">Login to Dashboard</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orbitage CM - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0b0f19; color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .glass-card { background: rgba(30, 41, 59, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; }
        .btn-custom { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); border: none; color: white; }
        .btn-custom:hover { background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); color: white; }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="d-flex justify-content-between align-items-center mb-5 border-bottom border-secondary pb-3 px-3">
            <div>
                <h3 class="fw-bold text-primary m-0"><i class="fas fa-rocket me-2"></i>Orbitage CM Orbitage Tools</h3>
                <p class="text-muted m-0 small">Storage Backend: GitHub Repository (Zero SQL)</p>
            </div>
            <a href="{{ url_for('logout') }}" class="btn btn-outline-danger btn-sm"><i class="fas fa-sign-out-alt me-1"></i> Logout</a>
        </div>

        <div class="row g-4 px-3">
            <div class="col-md-6">
                <div class="card glass-card p-4 h-100 shadow-sm">
                    <div class="d-flex align-items-center mb-3">
                        <div class="bg-primary bg-opacity-15 p-3 rounded-3 text-primary me-3">
                            <i class="fas fa-school fa-lg text-primary"></i>
                        </div>
                        <div>
                            <h5 class="fw-bold mb-1">Script One: School Management</h5>
                            <p class="text-muted small m-0">Student records, attendance & fees stored in GitHub.</p>
                        </div>
                    </div>
                    <a href="{{ url_for('script1.index') }}" class="btn btn-custom mt-auto w-100"><i class="fas fa-play me-1"></i> Launch Script 1</a>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card glass-card p-4 h-100 shadow-sm">
                    <div class="d-flex align-items-center mb-3">
                        <div class="bg-purple bg-opacity-15 p-3 rounded-3 text-purple me-3">
                            <i class="fas fa-hospital fa-lg text-warning"></i>
                        </div>
                        <div>
                            <h5 class="fw-bold mb-1">Script Two: Hospital Management</h5>
                            <p class="text-muted small m-0">Patient records & billing (Next tool).</p>
                        </div>
                    </div>
                    <button class="btn btn-secondary mt-auto w-100" disabled><i class="fas fa-lock me-1"></i> Coming Soon</button>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'orbitedge2026':
            login_user(User('1', 'admin'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Registering Script 1 Blueprint
app.register_blueprint(script1_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
