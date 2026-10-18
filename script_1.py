import os
import sqlite3
import zipfile
import io
from datetime import datetime
from flask import Blueprint, render_template_string, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required

# Blueprint define kiya hai taaki ise main app.py mein easily integrate kiya ja sake
script1_bp = Blueprint('script1', __name__, url_prefix='/script1')

# UPLOADS & DB CONFIG
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
DB_PATH = os.path.join(os.getcwd(), 'school_database.db')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'photos'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'documents'), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            section TEXT,
            guardian_phone TEXT,
            address TEXT,
            photo_filename TEXT,
            doc_filename TEXT,
            created_at TEXT
        )
    ''')
    # Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')
    # Fees Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            amount REAL,
            month TEXT,
            status TEXT,
            payment_date TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- HTML TEMPLATES ---
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orbitage CM - School Management Software</title>
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
                <p class="text-muted small m-0">Complete Academic & Administration Suite</p>
            </div>
            <div>
                <a href="/dashboard" class="btn btn-outline-light btn-sm me-2"><i class="fas fa-home me-1"></i> Main Dashboard</a>
                <a href="{{ url_for('script1.backup_data') }}" class="btn btn-success btn-sm me-2"><i class="fas fa-download me-1"></i> Backup Data (ZIP)</a>
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
                    <li class="nav-item"><a class="nav-link {{ 'active' if active_tab == 'students' }}" href="{{ url_for('script1.index', tab='students') }}"><i class="fas fa-user-graduate me-1"></i> Students Management</a></li>
                    <li class="nav-item"><a class="nav-link {{ 'active' if active_tab == 'attendance' }}" href="{{ url_for('script1.index', tab='attendance') }}"><i class="fas fa-clipboard-user me-1"></i> Attendance</a></li>
                    <li class="nav-item"><a class="nav-link {{ 'active' if active_tab == 'fees' }}" href="{{ url_for('script1.index', tab='fees') }}"><i class="fas fa-file-invoice-dollar me-1"></i> Fee Collection</a></li>
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

# Dashboard Tab Content
TAB_DASHBOARD = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="row g-4">
    <div class="col-md-4">
        <div class="glass-card p-4 text-center shadow">
            <i class="fas fa-users fa-3text text-primary mb-3 fa-2x"></i>
            <h4 class="text-muted">Total Students</h4>
            <h2 class="fw-bold text-light">{{ total_students }}</h2>
        </div>
    </div>
    <div class="col-md-4">
        <div class="glass-card p-4 text-center shadow">
            <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
            <h4 class="text-muted">Today's Attendance Recorded</h4>
            <h2 class="fw-bold text-light">{{ today_attendance_count }}</h2>
        </div>
    </div>
    <div class="col-md-4">
        <div class="glass-card p-4 text-center shadow">
            <i class="fas fa-rupee-sign fa-3x text-warning mb-3"></i>
            <h4 class="text-muted">Total Fees Collected</h4>
            <h2 class="fw-bold text-light">&#8377; {{ total_fees }}</h2>
        </div>
    </div>
</div>
""")

# Students Management Tab Content
TAB_STUDENTS = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="row g-4">
    <div class="col-lg-4">
        <div class="glass-card p-4 shadow">
            <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-user-plus me-2"></i>Register New Student</h5>
            <form method="POST" action="{{ url_for('script1.add_student') }}" enctype="multipart/form-data">
                <div class="mb-2">
                    <label class="form-label small">Roll Number / ID</label>
                    <input type="text" name="roll_no" class="form-control bg-dark text-light border-secondary" required>
                </div>
                <div class="mb-2">
                    <label class="form-label small">Full Name</label>
                    <input type="text" name="name" class="form-control bg-dark text-light border-secondary" required>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-2">
                        <label class="form-label small">Class</label>
                        <input type="text" name="class_name" class="form-control bg-dark text-light border-secondary" required>
                    </div>
                    <div class="col-md-6 mb-2">
                        <label class="form-label small">Section</label>
                        <input type="text" name="section" class="form-control bg-dark text-light border-secondary">
                    </div>
                </div>
                <div class="mb-2">
                    <label class="form-label small">Guardian Phone</label>
                    <input type="text" name="guardian_phone" class="form-control bg-dark text-light border-secondary">
                </div>
                <div class="mb-2">
                    <label class="form-label small">Address</label>
                    <textarea name="address" class="form-control bg-dark text-light border-secondary" rows="2"></textarea>
                </div>
                <div class="mb-2">
                    <label class="form-label small">Student Photo (Image)</label>
                    <input type="file" name="photo" class="form-control bg-dark text-light border-secondary" accept="image/*">
                </div>
                <div class="mb-3">
                    <label class="form-label small">Document / ID Proof (PDF/Doc)</label>
                    <input type="file" name="document" class="form-control bg-dark text-light border-secondary">
                </div>
                <button type="submit" class="btn btn-custom w-100 py-2 fw-semibold">Save Student Record</button>
            </form>
        </div>
    </div>
    
    <div class="col-lg-8">
        <div class="glass-card p-4 shadow">
            <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-list me-2"></i>Student Directory</h5>
            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                <table class="table table-dark table-hover align-middle small">
                    <thead>
                        <tr>
                            <th>Photo</th>
                            <th>Roll / Name</th>
                            <th>Class</th>
                            <th>Guardian Phone</th>
                            <th>Docs</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in students %}
                        <tr>
                            <td>
                                {% if s[7] %}
                                    <img src="{{ url_for('static', filename='uploads/photos/' + s[7]) }}" class="rounded-circle" width="40" height="40" style="object-fit: cover;">
                                {% else %}
                                    <div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center text-light" style="width: 40px; height: 40px;">N/A</div>
                                {% endif %}
                            </td>
                            <td>
                                <strong>{{ s[2] }}</strong><br>
                                <span class="text-muted">Roll: {{ s[1] }}</span>
                            </td>
                            <td>{{ s[3] }} - {{ s[4] }}</td>
                            <td>{{ s[5] }}</td>
                            <td>
                                {% if s[8] %}
                                    <a href="{{ url_for('static', filename='uploads/documents/' + s[8]) }}" target="_blank" class="btn btn-sm btn-outline-info"><i class="fas fa-file-alt"></i></a>
                                {% else %}
                                    <span class="text-muted">None</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="{{ url_for('script1.delete_student', student_id=s[0]) }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Are you sure you want to delete this student?');"><i class="fas fa-trash"></i></a>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="6" class="text-center text-muted py-4">No students registered yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
""")

# Attendance Tab Content
TAB_ATTENDANCE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="glass-card p-4 shadow">
    <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-clipboard-user me-2"></i>Daily Attendance Register</h5>
    <form method="POST" action="{{ url_for('script1.mark_attendance') }}">
        <div class="row mb-3">
            <div class="col-md-4">
                <label class="form-label small">Select Date</label>
                <input type="date" name="att_date" value="{{ today_date }}" class="form-control bg-dark text-light border-secondary" required>
            </div>
        </div>
        <div class="table-responsive" style="max-height: 450px; overflow-y: auto;">
            <table class="table table-dark table-striped align-middle">
                <thead>
                    <tr>
                        <th>Roll No</th>
                        <th>Student Name</th>
                        <th>Class</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for s in students %}
                    <tr>
                        <td>{{ s[1] }}</td>
                        <td>{{ s[2] }}</td>
                        <td>{{ s[3] }} - {{ s[4] }}</td>
                        <td>
                            <div class="btn-group" role="group">
                                <input type="radio" class="btn-check" name="status_{{ s[0] }}" id="present_{{ s[0] }}" value="Present" checked>
                                <label class="btn btn-outline-success btn-sm" for="present_{{ s[0] }}">Present</label>

                                <input type="radio" class="btn-check" name="status_{{ s[0] }}" id="absent_{{ s[0] }}" value="Absent">
                                <label class="btn btn-outline-danger btn-sm" for="absent_{{ s[0] }}">Absent</label>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="4" class="text-center text-muted">No students available for attendance.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% if students %}
        <button type="submit" class="btn btn-custom mt-3 px-4"><i class="fas fa-save me-1"></i> Save Attendance</button>
        {% endif %}
    </form>
</div>
""")

# Fees Tab Content
TAB_FEES = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="row g-4">
    <div class="col-lg-4">
        <div class="glass-card p-4 shadow">
            <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-receipt me-2"></i>Collect Fee Payment</h5>
            <form method="POST" action="{{ url_for('script1.collect_fee') }}">
                <div class="mb-2">
                    <label class="form-label small">Select Student</label>
                    <select name="student_id" class="form-control bg-dark text-light border-secondary" required>
                        <option value="">-- Choose Student --</option>
                        {% for s in students %}
                        <option value="{{ s[0] }}">{{ s[2] }} (Roll: {{ s[1] }})</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="mb-2">
                    <label class="form-label small">Amount (&#8377;)</label>
                    <input type="number" step="0.01" name="amount" class="form-control bg-dark text-light border-secondary" required>
                </div>
                <div class="mb-2">
                    <label class="form-label small">Fee Month / Term</label>
                    <input type="text" name="month" placeholder="e.g. October 2026" class="form-control bg-dark text-light border-secondary" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small">Payment Status</label>
                    <select name="status" class="form-control bg-dark text-light border-secondary">
                        <option value="Paid">Paid</option>
                        <option value="Pending">Pending</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-custom w-100 py-2 fw-semibold">Record Payment</button>
            </form>
        </div>
    </div>
    
    <div class="col-lg-8">
        <div class="glass-card p-4 shadow">
            <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-history me-2"></i>Fee Collection History</h5>
            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                <table class="table table-dark table-hover align-middle small">
                    <thead>
                        <tr>
                            <th>Student Name</th>
                            <th>Month</th>
                            <th>Amount</th>
                            <th>Status</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for f in fees %}
                        <tr>
                            <td>{{ f[5] }}</td>
                            <td>{{ f[2] }}</td>
                            <td>&#8377; {{ f[1] }}</td>
                            <td><span class="badge bg-{{ 'success' if f[3] == 'Paid' else 'warning' }}">{{ f[3] }}</span></td>
                            <td>{{ f[4] }}</td>
                        </tr>
                        {% else %}
                        <tr><td colspan="5" class="text-center text-muted py-4">No fee records found.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
""")

# --- ROUTES & LOGIC ---

@script1_bp.route('/')
@login_required
def index():
    tab = request.args.get('tab', 'dashboard')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]
    
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date = ?", (today,))
    today_attendance_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(amount) FROM fees WHERE status = 'Paid'")
    total_fees = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT * FROM students ORDER BY id DESC")
    students = cursor.fetchall()
    
    cursor.execute("""
        SELECT fees.id, fees.amount, fees.month, fees.status, fees.payment_date, students.name 
        FROM fees JOIN students ON fees.student_id = students.id ORDER BY fees.id DESC
    """)
    fees = cursor.fetchall()
    conn.close()
    
    if tab == 'students':
        return render_template_string(TAB_STUDENTS, active_tab=tab, students=students)
    elif tab == 'attendance':
        return render_template_string(TAB_ATTENDANCE, active_tab=tab, students=students, today_date=today)
    elif tab == 'fees':
        return render_template_string(TAB_FEES, active_tab=tab, students=students, fees=fees)
    else:
        return render_template_string(TAB_DASHBOARD, active_tab='dashboard', total_students=total_students, today_attendance_count=today_attendance_count, total_fees=total_fees)

@script1_bp.route('/add_student', methods=['POST'])
@login_required
def add_student():
    roll_no = request.form.get('roll_no')
    name = request.form.get('name')
    class_name = request.form.get('class_name')
    section = request.form.get('section')
    guardian_phone = request.form.get('guardian_phone')
    address = request.form.get('address')
    
    photo_filename = None
    doc_filename = None
    
    # Handle Photo Upload
    photo = request.files.get('photo')
    if photo and photo.filename != '':
        ext = photo.filename.rsplit('.', 1)[1].lower() if '.' in photo.filename else ''
        photo_filename = f"photo_{roll_no}_{int(datetime.now().timestamp())}.{ext}"
        photo.save(os.path.join(UPLOAD_FOLDER, 'photos', photo_filename))
        
    # Handle Document Upload
    doc = request.files.get('document')
    if doc and doc.filename != '':
        ext = doc.filename.rsplit('.', 1)[1].lower() if '.' in doc.filename else ''
        doc_filename = f"doc_{roll_no}_{int(datetime.now().timestamp())}.{ext}"
        doc.save(os.path.join(UPLOAD_FOLDER, 'documents', doc_filename))
        
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO students (roll_no, name, class_name, section, guardian_phone, address, photo_filename, doc_filename, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (roll_no, name, class_name, section, guardian_phone, address, photo_filename, doc_filename, created_at))
        conn.commit()
        conn.close()
        flash('Student registered successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Error: Roll number already exists!', 'error')
        
    return redirect(url_for('script1.index', tab='students'))

@script1_bp.route('/delete_student/<int:student_id>')
@login_required
def delete_student(student_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT photo_filename, doc_filename FROM students WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    if row:
        if row[0]:
            p_path = os.path.join(UPLOAD_FOLDER, 'photos', row[0])
            if os.path.exists(p_path): os.remove(p_path)
        if row[1]:
            d_path = os.path.join(UPLOAD_FOLDER, 'documents', row[1])
            if os.path.exists(d_path): os.remove(d_path)
            
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    cursor.execute("DELETE FROM fees WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('script1.index', tab='students'))

@script1_bp.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    att_date = request.form.get('att_date')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Pehle us date ka purana entry hata do taaki duplicate na ho
    cursor.execute("DELETE FROM attendance WHERE date = ?", (att_date,))
    
    cursor.execute("SELECT id FROM students")
    students = cursor.fetchall()
    
    for s in students:
        s_id = s[0]
        status = request.form.get(f'status_{s_id}', 'Present')
        cursor.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)", (s_id, att_date, status))
        
    conn.commit()
    conn.close()
    flash('Attendance saved successfully!', 'success')
    return redirect(url_for('script1.index', tab='attendance'))

@script1_bp.route('/collect_fee', methods=['POST'])
@login_required
def collect_fee():
    student_id = request.form.get('student_id')
    amount = request.form.get('amount')
    month = request.form.get('month')
    status = request.form.get('status')
    payment_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO fees (student_id, amount, month, status, payment_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (student_id, amount, month, status, payment_date))
    conn.commit()
    conn.close()
    flash('Fee transaction recorded successfully!', 'success')
    return redirect(url_for('script1.index', tab='fees'))

@script1_bp.route('/backup_data')
@login_required
def backup_data():
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add Database
        if os.path.exists(DB_PATH):
            zf.write(DB_PATH, os.path.basename(DB_PATH))
        # Add Uploads folder files
        for root, dirs, files in os.walk(UPLOAD_FOLDER):
            for file in files:
                absolute_path = os.path.join(root, file)
                relative_path = os.path.relpath(absolute_path, os.getcwd())
                zf.write(absolute_path, relative_path)
                
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'school_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    )
