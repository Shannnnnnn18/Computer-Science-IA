from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json, os, datetime, uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'
DATA_FILE = 'data.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def generate_user_id(data):
    n = len(data.get('users', {})) + 1
    return f"u{n:03d}"

def generate_task_id(tasks):
    n = len(tasks) + 1
    # ensure uniqueness if keys removed
    while True:
        tid = f"t{n:03d}"
        if tid not in tasks:
            return tid
        n += 1

def current_iso():
    return datetime.datetime.utcnow().isoformat()

# pages67
@app.route('/')
def index(): 
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    return render_template('home.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/tasks')
def tasks():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('tasks.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = load_data()
    payload = request.json
    username = payload.get('username','').strip()
    email = payload.get('email','').strip()
    password = payload.get('password','')

    if not username or not email or not password:
        return jsonify({"status":"error","message":"All fields required"}), 400
    if '@' not in email:
        return jsonify({"status":"error","message":"Invalid email"}), 400
    # unqiue
    for uid, u in data.get('users',{}).items():
        if u.get('username') == username:
            return jsonify({"status":"error","message":"Username exists"}), 400
        if u.get('email') == email:
            return jsonify({"status":"error","message":"Email exists"}), 400

    uid = generate_user_id(data)
    hashed = generate_password_hash(password)
    data['users'][uid] = {
        "username": username,
        "email": email,
        "password": hashed,
        "dateCreated": current_iso(),
        "profilePic": "/static/default_pfp.png",
        "themePref": "light",
        "lastLogin": None,
        "tasks": {},
        "preferences": {}
    }
    save_data(data)
    return jsonify({"status":"ok","userID": uid})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    db = load_data()
    for uid, user in db['users'].items():
        if user['username'] == username or user['email'] == username:
            if check_password_hash(user['password'], password):
                session['user_id'] = uid
                return jsonify({"status": "ok"})

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

# ---------- API: Tasks ----------
@app.route('/api/get_tasks')
def api_get_tasks():
    if 'user_id' not in session:
        return jsonify({}), 401
    uid = session['user_id']
    data = load_data()
    user = data['users'].get(uid)
    if not user:
        return jsonify({}), 404
    tasks = user.get('tasks', {})
    # assign orders if missing
    if any('order' not in t for t in tasks.values()):
        sorted_by_creation = sorted(tasks.items(), key=lambda x: x[1]['createdAt'])
        for i, (tid, _) in enumerate(sorted_by_creation):
            tasks[tid]['order'] = i
        save_data(data)
    # sort by order
    sorted_tasks = sorted(tasks.items(), key=lambda x: x[1].get('order', 9999))
    sorted_list = [{"id": tid, **task} for tid, task in sorted_tasks]
    return jsonify({"tasks": sorted_list})

@app.route('/api/add_task', methods=['POST'])
def api_add_task():
    if 'user_id' not in session:
        return jsonify({"status":"error","message":"Unauthorized"}), 401
    uid = session['user_id']
    payload = request.json
    title = payload.get('title','').strip()
    dueDate = payload.get('dueDate','').strip()
    priority = payload.get('priority','Medium')
    description = payload.get('description','')
    tags = payload.get('tags',[])
    reminder = payload.get('reminder','')

    # validations
    if not title:
        return jsonify({"status":"error","message":"Title required"}), 400
    try:
        if dueDate:
            datetime.datetime.fromisoformat(dueDate)
    except Exception:
        return jsonify({"status":"error","message":"Invalid due date (ISO format)"}), 400

    data = load_data()
    user = data['users'].get(uid)
    if user is None:
        return jsonify({"status":"error","message":"User not found"}), 404

    tasks = user.setdefault('tasks', {})
    tid = generate_task_id(tasks)
    max_order = max((t.get('order', -1) for t in tasks.values()), default=-1)
    new_order = max_order + 1
    tasks[tid] = {
        "title": title,
        "description": description,
        "dueDate": dueDate,
        "priority": priority,
        "status": "Pending",
        "completed": payload.get("completed", False),
        "tags": tags,
        "reminder": reminder,
        "createdAt": current_iso(),
        "lastEdited": None,
        "recurrence": "none",
        "recurrenceGenerated": False,
        "reminderTriggered": False,
        "order": new_order
    }
    save_data(data)
    return jsonify({"status":"ok","taskID": tid})

@app.route('/api/edit_task', methods=['POST'])
def api_edit_task():
    if 'user_id' not in session:
        return jsonify({"status":"error","message":"Unauthorized"}), 401
    uid = session['user_id']
    p = request.json
    taskID = p.get('taskID')
    if not taskID:
        return jsonify({"status":"error","message":"taskID required"}), 400

    data = load_data()
    user = data['users'].get(uid)
    if not user or taskID not in user.get('tasks',{}):
        return jsonify({"status":"error","message":"Task not found"}), 404

    task = user['tasks'][taskID]
    # update fields with very basic validation
    title = p.get('title', task['title']).strip()
    if not title:
        return jsonify({"status":"error","message":"Title required"}), 400
    task['title'] = title
    task['description'] = p.get('description', task.get('description',''))
    dueDate = p.get('dueDate', task.get('dueDate',''))
    if dueDate:
        try:
            datetime.datetime.fromisoformat(dueDate)
            task['dueDate'] = dueDate
        except:
            return jsonify({"status":"error","message":"Invalid dueDate format"}), 400
    task['priority'] = p.get('priority', task.get('priority','Medium'))
    task['completed'] = p.get('completed', task.get('completed', False))
    task['status'] = p.get('status', task.get('status','Pending'))
    task['tags'] = p.get('tags', task.get('tags',[]))
    task['reminder'] = p.get('reminder', task.get('reminder',''))
    task['lastEdited'] = current_iso()
    save_data(data)
    return jsonify({"status":"ok"})

@app.route('/api/delete_task', methods=['POST'])
def delete_task():
    if 'user_id' not in session:
        return jsonify({"status":"error","message":"Unauthorized"}), 401
    uid = session['user_id']
    p = request.json
    tid = p.get('taskID')
    if not tid:
        return jsonify({"status":"error","message":"Task ID required"}), 400
    data = load_data()
    user = data['users'].get(uid)
    if user is None:
        return jsonify({"status":"error","message":"User not found"}), 404
    tasks = user.get('tasks', {})
    if tid not in tasks:
        return jsonify({"status":"error","message":"Task not found"}), 404
    del tasks[tid]
    save_data(data)
    return jsonify({"status":"ok"})

@app.route('/api/sort_tasks', methods=['POST'])
def api_sort_tasks():
    if 'user_id' not in session:
        return jsonify({"status":"error"}), 401
    uid = session['user_id']
    sort_type = request.json.get('sort_type', 'priority')
    data = load_data()
    user = data['users'].get(uid)
    if not user:
        return jsonify({"status":"error"}), 404
    tasks = user.get('tasks', {})
    if sort_type == 'priority':
        rank = {'High': 3, 'Medium': 2, 'Low': 1}
        sorted_tasks = sorted(tasks.items(), key=lambda x: rank.get(x[1]['priority'], 0), reverse=True)
    elif sort_type == 'due_date':
        sorted_tasks = sorted(tasks.items(), key=lambda x: x[1].get('dueDate', '9999-12-31'))
    elif sort_type == 'status':
        sorted_tasks = sorted(tasks.items(), key=lambda x: x[1].get('completed', False))
    elif sort_type == 'revert':
        sorted_tasks = sorted(tasks.items(), key=lambda x: x[1].get('order', 9999))
    else:
        return jsonify({"status":"error", "message":"Invalid sort type"}), 400
    # update order
    for i, (tid, _) in enumerate(sorted_tasks):
        tasks[tid]['order'] = i
    save_data(data)
    # return sorted list
    sorted_list = [{"id": tid, **task} for tid, task in sorted_tasks]
    return jsonify({"tasks": sorted_list})

# ---------- API: Profile & Preferences ----------
@app.route('/api/get_profile')
def api_get_profile():
    if 'user_id' not in session:
        return jsonify({"status":"error"}), 401
    uid = session['user_id']
    data = load_data()
    u = data['users'].get(uid)
    if not u:
        return jsonify({"status":"error"}), 404
    
    profile = {k:v for k,v in u.items() if k != 'password'}
    return jsonify(profile)

@app.route('/api/edit_profile', methods=['POST'])
def api_edit_profile():
    if 'user_id' not in session:
        return jsonify({"status":"error"}), 401
    uid = session['user_id']
    p = request.json
    data = load_data()
    user = data['users'].get(uid)
    if not user:
        return jsonify({"status":"error"}), 404

    newUsername = p.get('username', user['username']).strip()
    newEmail = p.get('email', user['email']).strip()
    newPassword = p.get('password','').strip()
    newTheme = p.get('theme', user.get('themePref','light'))

    # uniqueness checks
    for other_id, other in data['users'].items():
        if other_id == uid: continue
        if other.get('username') == newUsername:
            return jsonify({"status":"error","message":"Username taken"}), 400
        if other.get('email') == newEmail:
            return jsonify({"status":"error","message":"Email taken"}), 400

    if '@' not in newEmail:
        return jsonify({"status":"error","message":"Invalid email"}), 400

    user['username'] = newUsername
    user['email'] = newEmail
    if newPassword:
        user['password'] = generate_password_hash(newPassword)
    user['themePref'] = newTheme
    user['lastEdited'] = current_iso()
    save_data(data)
    return jsonify({"status":"ok"})

# ---------- API: Reminders & Recurring ----------
@app.route('/api/check_reminders')
def api_check_reminders():
    # returns list of due tasks for current user 41 67 
    if 'user_id' not in session:
        return jsonify([]), 401
    uid = session['user_id']
    data = load_data()
    user = data['users'].get(uid)
    if not user:
        return jsonify([]), 404
    now = datetime.datetime.utcnow()
    due = []
    for tid, t in user.get('tasks', {}).items():
        rem = t.get('reminder') or ""
        if rem:
            try:
                rt = datetime.datetime.fromisoformat(rem)
                if not t.get('reminderTriggered', False) and t.get('status') != 'Completed' and now >= rt:
                    due.append({"taskID": tid, "title": t.get('title'), "reminder": rem})
                    t['reminderTriggered'] = True
            except:
                pass
    save_data(data)
    return jsonify(due)

@app.route('/api/check_recurring')
def api_check_recurring():
    if 'user_id' not in session:
        return jsonify([]), 401
    uid = session['user_id']
    data = load_data()
    user = data['users'].get(uid)
    if not user:
        return jsonify([]), 404
    tasks = user.get('tasks', {})
    created = []
    for tid, t in list(tasks.items()):
        rec = t.get('recurrence', 'none')
        if rec != 'none' and t.get('status') == 'Completed' and not t.get('recurrenceGenerated', False):
            # calculate next due
            try:
                due = datetime.datetime.fromisoformat(t.get('dueDate'))
            except:
                continue
            if rec == 'daily':
                next_due = (due + datetime.timedelta(days=1)).isoformat()
            elif rec == 'weekly':
                next_due = (due + datetime.timedelta(weeks=1)).isoformat()
            elif rec == 'monthly':
                # naive monthly: add 30 days
                next_due = (due + datetime.timedelta(days=30)).isoformat()
            else:
                continue
            new_tid = generate_task_id(tasks)
            tasks[new_tid] = {
                "title": t.get('title'),
                "description": t.get('description',''),
                "dueDate": next_due,
                "priority": t.get('priority','Medium'),
                "status": "Pending",
                "tags": t.get('tags',[]),
                "reminder": t.get('reminder',''),
                "createdAt": current_iso(),
                "lastEdited": None,
                "recurrence": t.get('recurrence','none'),
                "recurrenceGenerated": False,
                "reminderTriggered": False
            }
            t['recurrenceGenerated'] = True
            created.append(new_tid)
    save_data(data)
    return jsonify(created)

# Run the thing innit
if __name__ == '__main__':
    # ensure data file exists
    if not os.path.exists(DATA_FILE):
        save_data({"users": {}})
    app.run(debug=True, host='0.0.0.0', port=5000)