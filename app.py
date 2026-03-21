from flask import Flask, request, redirect, session
import cloudinary
import cloudinary.uploader
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# Cloudinary
cloudinary.config(
    cloud_name="dkbc4mvcm",
    api_key="655223884414587",
    api_secret="9lzc7StgLJtNnUP69bqBmgpPsII"
)

# DB
conn = sqlite3.connect("/tmp/final.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY,
password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS photos (
id INTEGER PRIMARY KEY AUTOINCREMENT,
url TEXT,
public_id TEXT,
hidden INTEGER DEFAULT 0
)
""")

# default password
cursor.execute("SELECT * FROM users WHERE id=1")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users VALUES (1, 'akm12345')")
    conn.commit()

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("logged"):
        return redirect("/vault")

    if request.method == "POST":
        p = request.form["password"]

        cursor.execute("SELECT password FROM users WHERE id=1")
        real = cursor.fetchone()[0]

        if p == real:
            session["logged"] = True
            return redirect("/vault")

    return '''
    <h2>🔐 Enter Password</h2>
    <form method="post">
        <input type="password" name="password"><br><br>
        <button>Login</button>
    </form>
    <a href="/forgot">Forgot Password</a>
    '''

# FORGOT
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        newpass = request.form["password"]
        cursor.execute("UPDATE users SET password=?", (newpass,))
        conn.commit()
        return redirect("/")

    return '''
    <h2>Reset Password 🔁</h2>
    <form method="post">
        <input name="password"><br><br>
        <button>Reset</button>
    </form>
    <a href="/">Back to Login</a>
    '''

# VAULT
@app.route("/vault", methods=["GET", "POST"])
def vault():
    if not session.get("logged"):
        return redirect("/")

    # upload
    if request.method == "POST":
        file = request.files["file"]
        if file:
            r = cloudinary.uploader.upload(file)
            cursor.execute(
                "INSERT INTO photos (url, public_id, hidden) VALUES (?,?,0)",
                (r["secure_url"], r["public_id"])
            )
            conn.commit()

    # fetch
    cursor.execute("SELECT * FROM photos WHERE hidden=0")
    normal = cursor.fetchall()

    cursor.execute("SELECT * FROM photos WHERE hidden=1")
    hidden = cursor.fetchall()

    html = "<h2>📸 My Vault</h2>"
    html += '''
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file"><br><br>
        <button>Upload</button>
    </form>
    <a href="/logout">Logout</a><br><br>
    '''

    # normal
    html += "<h3>Normal Files</h3>"
    for row in normal:
        html += f"""
        <div>
            <img src='{row[1]}' width='150'><br>
            <a href='/hide/{row[0]}'>Hide 🙈</a> |
            <a href='/delete/{row[0]}'>Delete ❌</a>
        </div><br>
        """

    # hidden (same page)
    html += "<h3>Hidden Files 🔐</h3>"
    for row in hidden:
        html += f"""
        <div>
            <img src='{row[1]}' width='150'><br>
            <a href='/unhide/{row[0]}'>Unhide 👁</a> |
            <a href='/delete/{row[0]}'>Delete ❌</a>
        </div><br>
        """

    return html

# HIDE
@app.route("/hide/<int:id>")
def hide(id):
    cursor.execute("UPDATE photos SET hidden=1 WHERE id=?", (id,))
    conn.commit()
    return redirect("/vault")

# UNHIDE
@app.route("/unhide/<int:id>")
def unhide(id):
    cursor.execute("UPDATE photos SET hidden=0 WHERE id=?", (id,))
    conn.commit()
    return redirect("/vault")

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    cursor.execute("SELECT public_id FROM photos WHERE id=?", (id,))
    r = cursor.fetchone()

    if r:
        cloudinary.uploader.destroy(r[0])
        cursor.execute("DELETE FROM photos WHERE id=?", (id,))
        conn.commit()

    return redirect("/vault")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
