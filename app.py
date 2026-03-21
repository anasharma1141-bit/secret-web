from flask import Flask, request, redirect
import cloudinary
import cloudinary.uploader
import sqlite3
import os

app = Flask(__name__)

# 🔐 Hidden password + answer
PASSWORD = "9999"
ANSWER = "mydog"

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
CREATE TABLE IF NOT EXISTS photos (
id INTEGER PRIMARY KEY AUTOINCREMENT,
url TEXT,
public_id TEXT,
hidden INTEGER DEFAULT 0
)
""")
conn.commit()

# MAIN VAULT
@app.route("/", methods=["GET","POST"])
def vault():
    if request.method=="POST":
        file = request.files["file"]
        if file:
            r = cloudinary.uploader.upload(file)
            cursor.execute("INSERT INTO photos (url, public_id, hidden) VALUES (?,?,0)",
                           (r["secure_url"], r["public_id"]))
            conn.commit()

    cursor.execute("SELECT * FROM photos")
    data = cursor.fetchall()

    html = "<h2>📸 Vault</h2>"
    html += '''
    <form method="post" enctype="multipart/form-data">
    <input type="file" name="file"><br><br>
    <button>Upload</button>
    </form><br>
    <a href="/forgot">Forgot Password</a><br><br>
    '''

    for row in data:
        if row[3] == 0:
            html += f"""
            <img src='{row[1]}' width='150'><br>
            <a href='/hide/{row[0]}'>Hide</a><br><br>
            """
        else:
            html += f"""
            <img src='{row[1]}' width='150' style='filter:blur(15px);'><br>
            🔐 Hidden File<br>

            <a href='/unlock/{row[0]}'>🔓 Password</a><br>

            ⬇ Swipe to open
            <div id="s{row[0]}" style="background:#ccc;height:30px;">
            <div id="b{row[0]}" style="background:green;width:0%;height:30px;"></div>
            </div>

            <script>
            let st{row[0]}=0;
            document.getElementById("s{row[0]}").addEventListener("touchstart",e=>{{
                st{row[0]}=e.touches[0].clientY;
            }});
            document.getElementById("s{row[0]}").addEventListener("touchmove",e=>{{
                let d=e.touches[0].clientY-st{row[0]};
                if(d>0){{
                    let p=Math.min(d,100);
                    document.getElementById("b{row[0]}").style.width=p+"%";
                    if(p>80) window.location="/unlock/{row[0]}";
                }}
            }});
            </script><br><br>
            """

    return html

# HIDE
@app.route("/hide/<int:id>")
def hide(id):
    cursor.execute("UPDATE photos SET hidden=1 WHERE id=?", (id,))
    conn.commit()
    return redirect("/")

# UNLOCK
@app.route("/unlock/<int:id>", methods=["GET","POST"])
def unlock(id):
    global PASSWORD
    if request.method=="POST":
        if request.form["password"] == PASSWORD:
            cursor.execute("SELECT url FROM photos WHERE id=?", (id,))
            url = cursor.fetchone()[0]
            return f"<img src='{url}' width='300'>"
        else:
            return "❌ Wrong Password"

    return '''
    <h2>Enter Password</h2>
    <form method="post">
    <input type="password" name="password"><br><br>
    <button>Open</button>
    </form>
    <br><a href="/forgot">Forgot Password</a>
    '''

# FORGOT PASSWORD (WITH ANSWER)
@app.route("/forgot", methods=["GET","POST"])
def forgot():
    global PASSWORD
    if request.method=="POST":
        if request.form["answer"] == ANSWER:
            PASSWORD = request.form["password"]
            return "✅ Password Changed <br><a href='/'>Back</a>"
        else:
            return "❌ Wrong Answer"

    return '''
    <h2>Reset Password</h2>
    <form method="post">
    <input name="answer" placeholder="Secret Answer"><br><br>
    <input name="password" placeholder="New Password"><br><br>
    <button>Reset</button>
    </form>
    '''

# RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
