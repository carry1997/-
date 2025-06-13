
from flask import Flask, request, redirect, session, send_from_directory
import os

app = Flask(__name__)
app.secret_key = 'secret123'

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

tickets = {
    "五月天演唱會": {
        "搖滾區 A 區": [5000, 5525],
        "搖滾區 B 區": [5000, 4525],
        "搖滾區 C 區": [5000, 3880],
        "看台區": [4000, 1880]
    },
    "周杰倫演唱會": {
        "搖滾區 A 區": [5000, 5525],
        "搖滾區 B 區": [5000, 4525],
        "搖滾區 C 區": [5000, 3880],
        "看台區": [4000, 1880]
    }
}

users = {
    "admin": "admin123"
}

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route('/')
def index():
    user = session.get('user')
    html = """<html><head>
    <meta charset='utf-8'>
    <style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 20px;
        background: #f2f3f5;
        color: #333;
    }
    .event-card {
        background: #fff;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    table {
        border-collapse: collapse;
        width: 100%%;
        margin-top: 15px;
    }
    th {
        background-color: #004085;
        color: white;
    }
    th, td {
        padding: 12px;
        border: 1px solid #ccc;
        text-align: center;
    }
    td.price span {
        background: #dc3545;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
    }
    a.button {
        background: #007bff;
        color: white;
        padding: 6px 14px;
        text-decoration: none;
        border-radius: 5px;
        transition: 0.3s;
    }
    a.button:hover {
        background: #0056b3;
    }
    .map {
        margin-top: 15px;
        max-width: 100%%;
        border: 2px solid #aaa;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    </style></head><body>
    <h1>🎫 演唱會搶票系統</h1>
    """

    if user:
        html += "<p>👋 歡迎 " + user + " | <a href='/logout'>登出</a></p>"
    else:
        html += "<p><a href='/login'>登入</a> | <a href='/register'>註冊</a></p>"

    for event, zones in tickets.items():
        html += "<div class='event-card'>"
        html += "<h2>" + event + "</h2><table><tr><th>區域</th><th>票價</th><th>剩餘票數</th><th>操作</th></tr>"
        for zone, (count, price) in zones.items():
            html += "<tr><td>" + zone + "</td><td class='price'><span>" + str(price) + " 元</span></td><td>" + str(count) + "</td><td>"
            if user:
                html += "<a class='button' href='/buy?event=" + event + "&zone=" + zone + "'>搶票</a>"
            else:
                html += "請先登入"
            html += "</td></tr>"
        html += "</table>"
        html += "<img class='map' src='/static/taipei_dome_map.jpg' alt='大巨蛋座位圖'>"
        html += "</div>"

    if user == "admin":
        html += "<p><a class='button' href='/admin'>🎛️ 進入後台</a></p>"

    html += "</body></html>"
    return html

@app.route('/buy')
def buy():
    user = session.get('user')
    if not user:
        return redirect('/login')

    event = request.args.get("event")
    zone = request.args.get("zone")

    if event not in tickets or zone not in tickets[event]:
        return "<h1>❌ 活動或區域不存在</h1><a href='/'>回首頁</a>"

    if tickets[event][zone][0] > 0:
        tickets[event][zone][0] -= 1
        return f"<h1>✅ {user} 成功搶到《{event}》{zone}門票！</h1><a href='/'>回首頁</a>"
    return f"<h1>❌ 《{event}》{zone} 票已售完！</h1><a href='/'>回首頁</a>"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "<h1>⚠️ 帳號已存在</h1><a href='/register'>重新註冊</a>"
        users[username] = password
        return "<h1>✅ 註冊成功</h1><a href='/login'>前往登入</a>"

    return """<h1>註冊帳號</h1>
    <form method="post">
        帳號：<input name="username"><br>
        密碼：<input name="password" type="password"><br>
        <input type="submit" value="註冊">
    </form>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['user'] = username
            return redirect('/')
        return "<h1>❌ 登入失敗</h1><a href='/login'>重試</a>"

    return """<h1>使用者登入</h1>
    <form method="post">
        帳號：<input name="username"><br>
        密碼：<input name="password" type="password"><br>
        <input type="submit" value="登入">
    </form>"""

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/admin')
def admin():
    if session.get('user') != 'admin':
        return "<h1>🚫 未授權</h1><a href='/'>回首頁</a>"

    html = "<h1>🎛️ 管理者後台</h1><ul>"
    for event, zones in tickets.items():
        html += "<li><strong>" + event + "</strong><ul>"
        for zone, (count, price) in zones.items():
            html += "<li>" + zone + "：剩 " + str(count) + " 張，票價 " + str(price) + " 元</li>"
        html += "</ul></li>"
    html += "</ul><a href='/'>回首頁</a>"
    return html

if __name__ == '__main__':
    app.run(debug=True)
