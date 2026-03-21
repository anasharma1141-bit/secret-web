from flask import Flask, request, redirect, session
import cloudinary
import cloudinary.uploader
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# Passwords
MAIN_PASSWORD = "akm12345"
HIDDEN_PASSWORD = "9999"   # 👈 hidden vault password

# Cloudinary
cloudinary.config(
    cloud_name="dkbc4mvcm",
    api_key="655223884414587",
    api_secret="9lzc7StgLJtNnUP69bqBmgpPsII"
)

# Database
conn = sqlite3.connect("//tmp/final.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, public_id TEXT, type TEXT)")
conn.commit()

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form["password"]

        if password == MAIN_PASSWORD:
            session["mode"] = "main"
            return redirect("/vault")

        elif password == HIDDEN_PASSWORD:
            session["mode"] = "hidden"
            return redirect("/vault")

    return '''
    <h2>🔐 Enter Password</h2>
    <form method="post">
        <input type="password" name="password"><br><br>
        <button>Enter</button>
    </form>
    '''

# VAULT
@app.route("/vault", methods=["GET", "POST"])
def vault():
    if "mode" not in session:
        return redirect("/")

    mode = session["mode"]

    if request.method == "POST":
        file = request.files["file"]
        if file:
            result = cloudinary.uploader.upload(file)
            cursor.execute(
                "INSERT INTO photos (url, public_id, type) VALUES (?,?,?)",
                (result["secure_url"], result["public_id"], mode)
            )
            conn.commit()

    cursor.execute("SELECT * FROM photos WHERE type=?", (mode,))
    data = cursor.fetchall()

    title = "📸 Main Vault" if mode == "main" else "🕵️ Hidden Vault"

    html = f"<h2>{title}</h2>"
    html += '''
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file"><br><br>
        <button>Upload</button>
    </form>
    <a href="/logout">Logout</a><br><br>
    '''

    for row in data:
        html += f"""
        <div>
            <img src='{row[1]}' width='150'><br>
            <a href='/delete/{row[0]}'>❌ Delete</a>
        </div><br>
        """

    return html

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    if "mode" not in session:
        return redirect("/")

    cursor.execute("SELECT public_id FROM photos WHERE id=?", (id,))
    result = cursor.fetchone()

    if result:
        cloudinary.uploader.destroy(result[0])
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
