from flask import Flask, request, redirect
import cloudinary
import cloudinary.uploader
import sqlite3
import os

app = Flask(__name__)

cloudinary.config(
    cloud_name="dkbc4mvcm",
    api_key="655223884414587",
    api_secret="9lzc7StgLJtNnUP69bqBmgpPsII"
)

conn = sqlite3.connect("/tmp/final.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, public_id TEXT, hidden INTEGER DEFAULT 0)")
conn.commit()

# MAIN PAGE
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            result = cloudinary.uploader.upload(file)
            cursor.execute("INSERT INTO photos (url, public_id, hidden) VALUES (?,?,0)",
                           (result["secure_url"], result["public_id"]))
            conn.commit()

    # normal photos
    cursor.execute("SELECT * FROM photos WHERE hidden=0")
    normal = cursor.fetchall()

    # hidden photos
    cursor.execute("SELECT * FROM photos WHERE hidden=1")
    hidden = cursor.fetchall()

    html = "<h2>Photo Vault 📸</h2>"

    html += '''
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file"><br><br>
        <button>Upload</button>
    </form>
    '''

    # NORMAL FILES
    html += "<h3>Normal Files:</h3>"
    for row in normal:
        html += f"""
        <div>
            <img src='{row[1]}' width='150'><br>
            <a href='/hide/{row[0]}'>Hide 🙈</a> |
            <a href='/delete/{row[0]}'>Delete ❌</a>
        </div><br>
        """

    # HIDDEN FILES
    html += "<h3>Hidden Files 🔐:</h3>"
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
    return redirect("/")

# UNHIDE
@app.route("/unhide/<int:id>")
def unhide(id):
    cursor.execute("UPDATE photos SET hidden=0 WHERE id=?", (id,))
    conn.commit()
    return redirect("/")

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    cursor.execute("SELECT public_id FROM photos WHERE id=?", (id,))
    result = cursor.fetchone()

    if result:
        cloudinary.uploader.destroy(result[0])
        cursor.execute("DELETE FROM photos WHERE id=?", (id,))
        conn.commit()

    return redirect("/")

# RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
