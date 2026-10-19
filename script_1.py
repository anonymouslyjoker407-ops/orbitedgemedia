import os
import json
import base64
import requests
from datetime import datetime
from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from flask_login import login_required

script1_bp = Blueprint('script1', __name__, url_prefix='/script1')

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = os.environ.get('GITHUB_REPO', '') # e.g. 'username/repo-name'
DATA_DIR = 'school_data'

def github_api_request(method, path, payload=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    if method == 'GET':
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            content = base64.b64decode(data['content']).decode('utf-8')
            return json.loads(content), data['sha']
        return None, None
    elif method == 'PUT':
        res = requests.put(url, headers=headers, json=payload)
        return res.status_code in [200, 201]
    elif method == 'DELETE':
        res = requests.delete(url, headers=headers, json=payload)
        return res.status_code == 200
    return False

def load_json_from_github(filename):
    data, _ = github_api_request('GET', f"{DATA_DIR}/{filename}")
    return data if data is not None else []

def save_json_to_github(filename, data_list, message):
    path = f"{DATA_DIR}/{filename}"
    _, sha = github_api_request('GET', path)
    
    json_str = json.dumps(data_list, indent=4)
    encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": message,
        "content": encoded
    }
    if sha:
        payload["sha"] = sha
    return github_api_request('PUT', path, payload)

def upload_file_to_github(class_name, file_obj, prefix):
    if not file_obj or file_obj.filename == '':
        return None
    ext = file_obj.filename.rsplit('.', 1)[1].lower() if '.' in file_obj.filename else ''
    filename = f"{prefix}_{int(datetime.now().timestamp())}.{ext}"
    
    # Systematic subfolder based on Class name inside GitHub repo
    safe_class = class_name.strip().replace(" ", "_").lower()
    path = f"{DATA_DIR}/classes/{safe_class}/uploads/{filename}"
    
    file_bytes = file_obj.read()
    encoded = base64.b64encode(file_bytes).decode('utf-8')
    
    _, sha = github_api_request('GET', path)
    payload = {
        "message": f"Upload file for class {class_name}",
        "content": encoded
    }
    if sha:
        payload["sha"] = sha
        
    success = github_api_request('PUT', path, payload)
    return f"classes/{safe_class}/uploads/{filename}" if success else None

# --- HTML TEMPLATES ---
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orbitage - School Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0b0f19; color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .glass-card { background: rgba(30, 41, 59, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; }
        .btn-custom { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); border: none; color: white; }
        .btn-custom:hover { background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); color: white; }
        .nav-pills .nav-link.active { background-color: #3b82f6 !important; }
        .nav-link { color: #94a3b8; }
        .nav-link:hover { color: #f1f5f9; }
        table { color: #f1f5f9 !important; }
    </style>
</head>
<body>
    <div class="container-fluid py-3">
        <div class="d-flex justify-content-between align-items-center mb-4 px-3 border-bottom border-secondary pb-3">
            <div>
                <h3 class="fw-bold text-primary m-0"><i class="fas fa-school me-2"></i>Orbitage School Manager</h3>
                <p class="text-muted small m-0"><i class="fab fa-github me-1"></i> GitHub Structured JSON Storage (No SQL)</p>
            </div>
            <div>
                <a href="/dashboard" class="btn btn-outline-light btn-sm"><i class="fas fa-home me-1"></i> Main Dashboard</a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show mx-3" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="row px-3 mb-4">
            <div class="col-12">
                <ul class="nav nav-pills gap-2 glass-card p-2 shadow-sm">
                    <li class="nav-item"><a class="nav-link {{ 'active' if active_tab == 'dashboard' }}" href="{{ url_for('script1.index', tab='dashboard') }}"><i class="fas fa-chart-pie me-1"></i> Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link {{ 'active' if active_tab == 'students' }}" href="{{ url_for('script1.index', tab='students') }}"><i class="fas fa-user-graduate me-1"></i> Students</a></li>
                    <li class="nav-item"><a class="nav-link {{ 'active' if active_tab == 'attendance' }}" href="{{ url_for('script1.index', tab='attendance') }}"><i class="fas fa-clipboard-user me-1"></i> Attendance</a></li>
                    <li class="nav-item"><a class="nav-link {{ 'active' if active_tab == 'fees' }}" href="{{ url_for('script1.index', tab='fees') }}"><i class="fas fa-file-invoice-dollar me-1"></i> Fees</a></li>
                </ul>
            </div>
        </div>

        <div class="px-3">
            {% block content %}{% endblock %}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

TAB_DASHBOARD = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="row g-4">
    <div class="col-md-4">
        <div class="glass-card p-4 text-center shadow">
            <i class="fas fa-users text-primary mb-3 fa-2x"></i>
            <h4 class="text-muted fs-6">Total Students</h4>
            <h2 class="fw-bold text-light">{{ total_students }}</h2>
        </div>
    </div>
    <div class="col-md-4">
        <div class="glass-card p-4 text-center shadow">
            <i class="fas fa-check-circle text-success mb-3 fa-2x"></i>
            <h4 class="text-muted fs-6">Today's Attendance</h4>
            <h2 class="fw-bold text-light">{{ today_attendance_count }}</h2>
        </div>
    </div>
    <div class="col-md-4">
        <div class="glass-card p-4 text-center shadow">
            <i class="fas fa-rupee-sign text-warning mb-3 fa-2x"></i>
            <h4 class="text-muted fs-6">Total Fees Collected</h4>
            <h2 class="fw-bold text-light">&#8377; {{ total_fees }}</h2>
        </div>
    </div>
</div>
""")

TAB_STUDENTS = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="row g-4">
    <div class="col-lg-4">
        <div class="glass-card p-4 shadow">
            <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-user-plus me-2"></i>Register Student</h5>
            <form method="POST" action="{{ url_for('script1.add_student') }}" enctype="multipart/form-data">
                <div class="mb-2"><label class="form-label small">Roll No</label><input type="text" name="roll_no" class="form-control bg-dark text-light border-secondary" required></div>
                <div class="mb-2"><label class="form-label small">Full Name</label><input type="text" name="name" class="form-control bg-dark text-light border-secondary" required></div>
                <div class="row">
                    <div class="col-md-6 mb-2"><label class="form-label small">Class (e.g. 10th)</label><input type="text" name="class_name" class="form-control bg-dark text-light border-secondary" required></div>
                    <div class="col-md-6 mb-2"><label class="form-label small">Section</label><input type="text" name="section" class="form-control bg-dark text-light border-secondary"></div>
                </div>
                <div class="mb-2"><label class="form-label small">Guardian Phone</label><input type="text" name="guardian_phone" class="form-control bg-dark text-light border-secondary"></div>
                <div class="mb-2"><label class="form-label small">Photo</label><input type="file" name="photo" class="form-control bg-dark text-light border-secondary" accept="image/*"></div>
                <div class="mb-3"><label class="form-label small">Document</label><input type="file" name="document" class="form-control bg-dark text-light border-secondary"></div>
                <button type="submit" class="btn btn-custom w-100 py-2 fw-semibold">Save to GitHub Folder</button>
            </form>
        </div>
    </div>
    <div class="col-lg-8">
        <div class="glass-card p-4 shadow">
            <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-list me-2"></i>Student Directory</h5>
            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                <table class="table table-dark table-hover align-middle small">
                    <thead><tr><th>Photo</th><th>Roll / Name</th><th>Class</th><th>Phone</th><th>Action</th></tr></thead>
                    <tbody>
                        {% for s in students %}
                        <tr>
                            <td>
                                {% if s.photo %}
                                    <img src="https://raw.githubusercontent.com/{{ repo }}/main/school_data/{{ s.photo }}" class="rounded-circle" width="40" height="40" style="object-fit: cover;">
                                {% else %}
                                    <div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center text-light" style="width: 40px; height: 40px;">N/A</div>
                                {% endif %}
                            </td>
                            <td><strong>{{ s.name }}</strong><br><span class="text-muted">Roll: {{ s.roll_no }}</span></td>
                            <td>{{ s.class_name }} - {{ s.section }}</td>
                            <td>{{ s.guardian_phone }}</td>
                            <td><a href="{{ url_for('script1.delete_student', student_id=s.id) }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete student?');"><i class="fas fa-trash"></i></a></td>
                        </tr>
                        {% else %}
                        <tr><td colspan="5" class="text-center text-muted py-4">No students registered yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
""")

TAB_ATTENDANCE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="glass-card p-4 shadow">
    <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-clipboard-user me-2"></i>Daily Attendance</h5>
    <form method="POST" action="{{ url_for('script1.mark_attendance') }}">
        <div class="row mb-3"><div class="col-md-4"><label class="form-label small">Date</label><input type="date" name="att_date" value="{{ today_date }}" class="form-control bg-dark text-light border-secondary" required></div></div>
        <div class="table-responsive" style="max-height: 450px; overflow-y: auto;">
            <table class="table table-dark table-striped align-middle">
                <thead><tr><th>Roll No</th><th>Name</th><th>Class</th><th>Status</th></tr></thead>
                <tbody>
                    {% for s in students %}
                    <tr>
                        <td>{{ s.roll_no }}</td>
                        <td>{{ s.name }}</td>
                        <td>{{ s.class_name }} - {{ s.section }}</td>
                        <td>
                            <div class="btn-group" role="group">
                                <input type="radio" class="btn-check" name="status_{{ s.id }}" id="p_{{ s.id }}" value="Present" checked>
                                <label class="btn btn-outline-success btn-sm" for="p_{{ s.id }}">Present</label>
                                <input type="radio" class="btn-check" name="status_{{ s.id }}" id="a_{{ s.id }}" value="Absent">
                                <label class="btn btn-outline-danger btn-sm" for="a_{{ s.id }}">Absent</label>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="4" class="text-center text-muted">No students available.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% if students %}<button type="submit" class="btn btn-custom mt-3 px-4">Save Attendance</button>{% endif %}
    </form>
</div>
""")

TAB_FEES = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="row g-4">
    <div class="col-lg-4">
        <div class="glass-card p-4 shadow">
            <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-receipt me-2"></i>Collect Fee</h5>
            <form method="POST" action="{{ url_for('script1.collect_fee') }}">
                <div class="mb-2"><label class="form-label small">Student</label><select name="student_id" class="form-control bg-dark text-light border-secondary" required><option value="">-- Choose --</option>{% for s in students %}<option value="{{ s.id }}">{{ s.name }} ({{ s.roll_no }})</option>{% endfor %}</select></div>
                <div class="mb-2"><label class="form-label small">Amount (&#8377;)</label><input type="number" step="0.01" name="amount" class="form-control bg-dark text-light border-secondary" required></div>
                <div class="mb-2"><label class="form-label small">Month</label><input type="text" name="month" placeholder="e.g. October 2026" class="form-control bg-dark text-light border-secondary" required></div>
                <div class="mb-3"><label class="form-label small">Status</label><select name="status" class="form-control bg-dark text-light border-secondary"><option value="Paid">Paid</option><option value="Pending">Pending</option></select></div>
                <button type="submit" class="btn btn-custom w-100 py-2 fw-semibold">Record Fee</button>
            </form>
        </div>
    </div>
    <div class="col-lg-8">
        <div class="glass-card p-4 shadow">
            <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-history me-2"></i>Fee History</h5>
            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                <table class="table table-dark table-hover align-middle small">
                    <thead><tr><th>Student</th><th>Month</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
                    <tbody>
                        {% for f in fees %}
                        <tr>
                            <td>{{ f.student_name }}</td>
                            <td>{{ f.month }}</td>
                            <td>&#8377; {{ f.amount }}</td>
                            <td><span class="badge bg-{{ 'success' if f.status == 'Paid' else 'warning' }}">{{ f.status }}</span></td>
                            <td>{{ f.payment_date }}</td>
                        </tr>
                        {% else %}
                        <tr><td colspan="5" class="text-center text-muted py-4">No records found.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
""")

@script1_bp.route('/')
@login_required
def index():
    tab = request.args.get('tab', 'dashboard')
    students = load_json_from_github('students.json')
    attendance = load_json_from_github('attendance.json')
    fees = load_json_from_github('fees.json')
    
    total_students = len(students)
    today = datetime.now().strftime('%Y-%m-%d')
    today_attendance_count = sum(1 for a in attendance if a.get('date') == today and a.get('status') == 'Present')
    total_fees = sum(float(f.get('amount', 0)) for f in fees if f.get('status') == 'Paid')
    
    if tab == 'students':
        return render_template_string(TAB_STUDENTS, active_tab=tab, students=students, repo=GITHUB_REPO)
    elif tab == 'attendance':
        return render_template_string(TAB_ATTENDANCE, active_tab=tab, students=students, today_date=today)
    elif tab == 'fees':
        return render_template_string(TAB_FEES, active_tab=tab, students=students, fees=fees)
    else:
        return render_template_string(TAB_DASHBOARD, active_tab='dashboard', total_students=total_students, today_attendance_count=today_attendance_count, total_fees=total_fees)

@script1_bp.route('/add_student', methods=['POST'])
@login_required
def add_student():
    students = load_json_from_github('students.json')
    roll_no = request.form.get('roll_no')
    class_name = request.form.get('class_name')
    
    if any(s['roll_no'] == roll_no for s in students):
        flash('Error: Roll number already exists!', 'error')
        return redirect(url_for('script1.index', tab='students'))
        
    photo_file = request.files.get('photo')
    doc_file = request.files.get('document')
    
    photo_path = upload_file_to_github(class_name, photo_file, f"photo_{roll_no}")
    doc_path = upload_file_to_github(class_name, doc_file, f"doc_{roll_no}")
    
    new_student = {
        "id": int(datetime.now().timestamp()),
        "roll_no": roll_no,
        "name": request.form.get('name'),
        "class_name": class_name,
        "section": request.form.get('section'),
        "guardian_phone": request.form.get('guardian_phone'),
        "photo": photo_path,
        "document": doc_path,
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    students.append(new_student)
    save_json_to_github('students.json', students, f"Add student {roll_no}")
    flash('Student registered securely in GitHub repo folders!', 'success')
    return redirect(url_for('script1.index', tab='students'))

@script1_bp.route('/delete/<int:student_id>')
@login_required
def delete_student(student_id):
    students = load_json_from_github('students.json')
    students = [s for s in students if s['id'] != student_id]
    save_json_to_github('students.json', students, f"Delete student ID {student_id}")
    flash('Student removed successfully!', 'success')
    return redirect(url_for('script1.index', tab='students'))

@script1_bp.route('/attendance', methods=['POST'])
@login_required
def mark_attendance():
    att_date = request.form.get('att_date')
    students = load_json_from_github('students.json')
    attendance = load_json_from_github('attendance.json')
    
    attendance = [a for a in attendance if a.get('date') != att_date]
    for s in students:
        status = request.form.get(f"status_{s['id']}", 'Present')
        attendance.append({
            "student_id": s['id'],
            "student_name": s['name'],
            "date": att_date,
            "status": status
        })
        
    save_json_to_github('attendance.json', attendance, f"Update attendance for {att_date}")
    flash('Attendance saved to GitHub!', 'success')
    return redirect(url_for('script1.index', tab='attendance'))

@script1_bp.route('/fee', methods=['POST'])
@login_required
def collect_fee():
    fees = load_json_from_github('fees.json')
    students = load_json_from_github('students.json')
    
    student_id = int(request.form.get('student_id'))
    student_name = next((s['name'] for s in students if s['id'] == student_id), 'Unknown')
    
    new_fee = {
        "id": int(datetime.now().timestamp()),
        "student_id": student_id,
        "student_name": student_name,
        "amount": request.form.get('amount'),
        "month": request.form.get('month'),
        "status": request.form.get('status'),
        "payment_date": datetime.now().strftime('%Y-%m-%d')
    }
    
    fees.append(new_fee)
    save_json_to_github('fees.json', fees, f"Record fee for {student_name}")
    flash('Fee recorded to GitHub!', 'success')
    return redirect(url_for('script1.index', tab='fees'))
