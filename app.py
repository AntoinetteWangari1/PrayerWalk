from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import os, json
import sqlite3
from datetime import datetime
from flask import send_from_directory


app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = 'database.db'

# Ensure results folder exists
os.makedirs("results", exist_ok=True)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Setup DB
def init_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
init_db()

@app.route('/', methods=['GET'])
def root_redirect():
    return redirect(url_for('login'))

@app.route('/home', methods=['GET'])
def home():
    if "user" in session:
        return render_template('index.html', username=session["user"])
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']

        if user.lower() == 'admin':
            return "You cannot sign up as 'admin'"
        
        with get_db() as db:
            try:
                db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (user, pw))
                os.makedirs(f"results/{user}", exist_ok=True)
                session["user"] = user
                return redirect(url_for('home'))
            except sqlite3.IntegrityError:
                return "Username already exists"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        db = get_db()
        result = db.execute('SELECT * FROM users WHERE username=? AND password=?', (user, pw)).fetchone()
        if result:
            session["user"] = user
            if user == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for('login'))

@app.route('/save_geojson', methods=['POST'])
def save_geojson():
    if "user" not in session:
        return "Unauthorized", 401
    data = request.get_json()
    username = session["user"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"results/{username}/walk_{timestamp}.geojson"
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return jsonify({"message": "GeoJSON saved", "path": filepath})

@app.route('/my_walks')
def my_walks():
    if "user" not in session:
        return redirect(url_for('login'))

    user_folder = f"results/{session['user']}"
    walks = os.listdir(user_folder) if os.path.exists(user_folder) else []
    return jsonify(walks)

@app.route('/admin_dashboard')
def admin_dashboard():
    if "user" not in session or session['user'] != 'admin':
        return "Access denied", 403

    user_folders = [u for u in os.listdir("results") if os.path.isdir(os.path.join("results", u))]
    walks = []
    for user in user_folders:
        user_path = os.path.join("results", user)
        for file in os.listdir(user_path):
            if file.endswith(".geojson"):
                file_path = os.path.join(user_path, file)
                with open(file_path) as f:
                    data = json.load(f)
                    props = data.get("properties", {})
                walks.append({
                    "user": user,
                    "file": file,
                    "steps": props.get("steps", "N/A"),
                    "duration": props.get("duration", "N/A"),
                    "date": props.get("date", "N/A"),
                    "path": f"{user}/{file}"
                })
    return render_template('admin_dashboard.html', walks=walks)

@app.route('/view_geojson/<user>/<filename>')
def view_geojson(user, filename):
    filepath = os.path.join("results", user, filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    with open(filepath) as f:
        geojson = json.load(f)
    return jsonify(geojson)

@app.route('/download/<user>/<filename>')
def download_geojson(user, filename):
    path = os.path.join('results', user)
    return send_from_directory(path, filename, as_attachment=True)

@app.route('/delete/<user>/<filename>', methods=['POST'])
def delete_geojson(user, filename):
    filepath = os.path.join("results", user, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return redirect(url_for('admin_dashboard'))
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)
