from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3

app = Flask(_name_)
DATABASE = 'membership.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            iid INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            phone TEXT,
            birthdate TEXT
        );
        INSERT OR IGNORE INTO members (username, email, password)
        VALUES ('admin', 'admin@example.com', 'admin');
        """)
        db.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone')
        birthdate = request.form.get('birthdate')

        if not username or not email or not password:
            return render_template('error.html', message='請輸入用戶名、電子郵件和密碼')

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM members WHERE username=? OR email=?", (username, email))
        if cursor.fetchone():
            return render_template('error.html', message='用戶名或電子郵件已存在')

        cursor.execute("INSERT INTO members (username, email, password, phone, birthdate) VALUES (?, ?, ?, ?, ?)",
                       (username, email, password, phone, birthdate))
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            return render_template('error.html', message='請輸入電子郵件和密碼')

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM members WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        if user:
            username = user[1]
            iid = user[0]
            return render_template('welcome.html', username=add_stars(username), iid=iid)
        else:
            return render_template('error.html', message='電子郵件或密碼錯誤')
    return render_template('login.html')

@app.route('/edit_profile/<int:iid>', methods=['GET', 'POST'])
def edit_profile(iid):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone')
        birthdate = request.form.get('birthdate')

        if not email or not password:
            return render_template('error.html', message='請輸入電子郵件和密碼')

        cursor.execute("SELECT * FROM members WHERE email=? AND iid != ?", (email, iid))
        if cursor.fetchone():
            return render_template('error.html', message='電子郵件已被使用')

        cursor.execute("UPDATE members SET email=?, password=?, phone=?, birthdate=? WHERE iid=?",
                       (email, password, phone, birthdate, iid))
        db.commit()
        cursor.execute("SELECT username FROM members WHERE iid=?", (iid,))
        username = cursor.fetchone()[0]
        return render_template('welcome.html', username=add_stars(username), iid=iid)

    cursor.execute("SELECT * FROM members WHERE iid=?", (iid,))
    user = cursor.fetchone()
    if not user:
        return render_template('error.html', message='使用者不存在')

    user_data = {
        'iid': user[0],
        'username': user[1],
        'email': user[2],
        'password': user[3],
        'phone': user[4],
        'birthdate': user[5]
    }
    return render_template('edit_profile.html', user=user_data)

@app.route('/delete/<int:iid>')
def delete_user(iid):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM members WHERE iid=?", (iid,))
    db.commit()
    return redirect(url_for('index'))

@app.route('/welcome/<int:iid>')
def welcome_back(iid):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username FROM members WHERE iid=?", (iid,))
    user = cursor.fetchone()
    if user:
        return render_template('welcome.html', username=add_stars(user[0]), iid=iid)
    else:
        return render_template('error.html', message='使用者不存在')

@app.template_filter('add_stars')
def add_stars(username):
    return f"★{username}★"

if _name_ == '_main_':
    init_db()
    app.run(debug=True)
