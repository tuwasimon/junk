from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Letters Dictionary ---
letters = {
    "sad": "Hey, I know you're feeling low right now. Just remember you're amazing, strong, and I care about you more than words can say. 💖",
    "miss": "I miss you too! You're always on my mind, and I can't wait till we talk or hang out again. 💌",
    "bored": "Here's a tiny mission: count 5 things you love about yourself. Or... message me 😉",
    "happy": "Yay! I'm glad you're smiling. You deserve all the joy in the world 🌞💫",
}

# --- Users ---
USERS = {
    "tuwa": "tuwaspec1",
    "naomi": "naomi_1"
}

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    receiver TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/open/<mood>')
def open_letter(mood):
    message = letters.get(mood, "No letter found for this mood 😢")
    return render_template('letter.html', mood=mood, message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in USERS and USERS[username] == password:
            session["username"] = username
            return redirect(url_for("chat"))
        return render_template("login.html", error="Invalid login")
    return render_template("login.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "username" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        msg = request.form["message"]
        receiver = "tuwa" if session["username"] == "her" else "her"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect("messages.db")
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, receiver, content, timestamp) VALUES (?, ?, ?, ?)",
                  (session["username"], receiver, msg, timestamp))
        conn.commit()
        conn.close()
        return redirect(url_for("chat"))
    
    return render_template("chat.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))

@app.route("/messages")
def get_messages():
    if "username" not in session:
        return jsonify({"success": False})
    
    current_user = session["username"]
    other_user = "her" if current_user == "tuwa" else "tuwa"
    since_id = request.args.get('since', default=0, type=int)

    conn = sqlite3.connect("messages.db")
    conn.row_factory = sqlite3.Row  # Allows dictionary-style access
    c = conn.cursor()
    
    # Get only new messages since last check
    c.execute('''SELECT id, sender, content, timestamp 
                 FROM messages 
                 WHERE ((sender=? AND receiver=?) OR (sender=? AND receiver=?))
                 AND id > ?
                 ORDER BY id ASC''',
              (current_user, other_user, other_user, current_user, since_id))
    
    messages = [{
        "id": row["id"],
        "sender": row["sender"],
        "content": row["content"],
        "timestamp": row["timestamp"],
        "isMe": row["sender"] == current_user
    } for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        "success": True,
        "currentUser": current_user,
        "messages": messages
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("Created templates directory - please add your template files")
    
    app.run(debug=True)