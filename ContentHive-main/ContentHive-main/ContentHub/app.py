from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask import jsonify
import sqlite3, os, uuid, random
from werkzeug.utils import secure_filename
from PIL import Image
import PyPDF2
import docx





app = Flask(__name__)
app.secret_key = "secret123"

# Upload folder configuration
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Limit max upload size to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB












def get_db_connection():
    conn=sqlite3.connect("ContentInfo.db")
    conn.row_factory=sqlite3.Row
    return conn


@app.route("/signin(email).html",methods=("GET","POST"))
def sign():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()
        conn.close()
        
        if user:
            if user["two_factor_enabled"]:
                session["temp_user_id"] = user["id"]
                # Generate a mock 6-digit code
                code = str(random.randint(100000, 999999))
                session["2fa_code"] = code
                print(f"\n[2FA] Verification code for {email}: {code}\n")
                return redirect(url_for("verify_2fa"))
            else:
                session["user_id"] = user["id"]
                return redirect((url_for("library")))
        else:
            return redirect((url_for("incorrect")))
            
    return render_template("signin(email).html")




@app.route("/Create.html",methods=("GET","POST"))
def create():
    error = None
    if request.method=="POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            error = "Passwords do not match. Please try again."
        else:
            conn = get_db_connection()
            existing_user = conn.execute(
                "SELECT id FROM users WHERE email=?",
                (email,)
            ).fetchone()

            if existing_user:
                conn.close()
                error = "An account with this email already exists. Please sign in or use a different email."
            else:
                conn.execute(
                    "INSERT INTO users (name,email,password) VALUES(?,?,?)",
                    (name, email, password)
                )
                conn.commit()
                user = conn.execute(
                    "SELECT id FROM users WHERE email=?",
                    (email,)
                ).fetchone()
                conn.close()

                session["user_id"] = user["id"]
                return render_template("successFul.html", user_name=name)

    return render_template("Create.html", error=error)







@app.route("/interest", methods=["GET","POST"])
def interest():
    if "user_id" not in session:
        return redirect("/sign")

    if request.method == "POST":
        selected = request.form.get("interest")

        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET interests=? WHERE id=?",
            (selected, session["user_id"])
        )
        conn.commit()
        conn.close()

        return redirect("/item")

    return render_template("Interest.html")















@app.route("/item")
def item():
    if "user_id" not in session:
        return redirect("/sign")
    conn = get_db_connection()
    user_id = session.get("user_id")

    user = conn.execute(
        "SELECT name, profile_pic FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    
    return render_template("ItemShare.html",user=user) 


def save_image(file):
    filename = str(uuid.uuid4()) + ".jpg"
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    img = Image.open(file)
    img = img.resize((300,300))
    img.save(path)

    return "uploads/" + filename

@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user_id" not in session:
        return redirect("/sign")

    conn = get_db_connection()

    if request.method == "POST":
        name = request.form["name"]
        file = request.files["profile_pic"]

        if file and file.filename != "":
            image_path = save_image(file)

            conn.execute(
                "UPDATE users SET name=?, profile_pic=? WHERE id=?",
                (name, image_path, session["user_id"])
            )
        else:
            conn.execute(
                "UPDATE users SET name=? WHERE id=?",
                (name, session["user_id"])
            )

        conn.commit()
        conn.close()
        return redirect("/item")

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    conn.close()
    return render_template("profile.html", user=user)



@app.route("/logout")
def logout():
    session.clear()
    return render_template("logout.html")




@app.route("/setting", methods=["GET", "POST"])
def setting():

    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    user_id = session["user_id"]

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    user_info = conn.execute(
        "SELECT * FROM users_info WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if request.method == "POST":

        # 🔴 DELETE ACCOUNT
        if "delete_account" in request.form:
            password = request.form.get("delete_password")

            if password == user["password"]:

                conn.execute("DELETE FROM users WHERE id=?", (user_id,))
                conn.execute("DELETE FROM users_info WHERE user_id=?", (user_id,))

                conn.commit()
                conn.close()

                session.clear()
                return redirect("/sign")

            else:
                return "Wrong password! Cannot delete account"

        # 🟢 NORMAL UPDATE
        email = request.form.get("email")
        current_password = request.form.get("password")
        newpassword = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        phone = request.form.get("phone")
        card = request.form.get("card")
        expiry = request.form.get("expiry")

        # update email
        if email:
            conn.execute(
                "UPDATE users SET email=? WHERE id=?",
                (email, user_id)
            )

        # update password
        if newpassword:
            if newpassword == confirm_password:
                if user["password"] == current_password:
                    conn.execute(
                        "UPDATE users SET password=? WHERE id=?",
                        (newpassword, user_id)
                    )
                else:
                    return "Wrong current password"
            else:
                return "Passwords do not match"

        # update or insert user info
        if user_info:
            conn.execute("""
                UPDATE users_info
                SET phone=?, card_number=?, expiry=?
                WHERE user_id=?
            """, (phone, card, expiry, user_id))
        else:
            conn.execute("""
                INSERT INTO users_info (user_id, phone, card_number, expiry)
                VALUES (?, ?, ?, ?)
            """, (user_id, phone, card, expiry))

        conn.commit()
        conn.close()

        return redirect("/setting")

    conn.close()

    return render_template("Setting.html", user=user, user_info=user_info)
































@app.route("/")
def index():
    return render_template("FirstPage/index.html")

@app.route("/installExtension/Download")
def download():
    return render_template("installExtension/Download.html")

@app.route("/sign")
def sign_page():
    return render_template("signin.html")

@app.route("/signin.html")
def signin():
    return render_template("signin.html")

@app.route("/Password_Incorrect.html")
def incorrect():
    return render_template("Password_Incorrect.html")





    
    

    

















@app.route("/privacy")
def privacy():
    
    if "user_id" not in session:
        return redirect("/sign")
    conn = get_db_connection()
    user_id = session.get("user_id")

    user = conn.execute(
        "SELECT name, profile_pic FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    
    
    
    return render_template("Privacy.html",user=user)

@app.route("/terms")
def terms():
    
    if "user_id" not in session:
        return redirect("/sign")
    conn = get_db_connection()
    user_id = session.get("user_id")

    user = conn.execute(
        "SELECT name, profile_pic FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    
    
    return render_template("Terms.html",user=user)





















@app.route("/verify_2fa", methods=["GET", "POST"])
def verify_2fa():
    if "temp_user_id" not in session:
        return redirect(url_for("sign"))
    
    if request.method == "POST":
        # Concatenate code from 6 inputs if needed, but for simplicity let's assume one field for now or handle list
        entered_code = request.form.get("code")
        if not entered_code:
            # Handle multi-input case
            entered_code = "".join([request.form.get(f"c{i}") for i in range(1, 7)])
            
        if entered_code == session.get("2fa_code"):
            session["user_id"] = session.pop("temp_user_id")
            session.pop("2fa_code")
            return redirect(url_for("library"))
        else:
            return render_template("verify_2fa.html", error="Invalid verification code")
            
    return render_template("verify_2fa.html")

@app.route("/toggle_2fa", methods=["POST"])
def toggle_2fa():
    if "user_id" not in session:
        return redirect(url_for("sign"))
    
    enabled = request.form.get("enabled") == "true"
    conn = get_db_connection()
    conn.execute("UPDATE users SET two_factor_enabled=? WHERE id=?", (1 if enabled else 0, session["user_id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/Pricing/pricing.html")
def pricing():
    return render_template("Pricing/pricing.html")

@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect("/sign")
    return render_template("Pricing/checkout.html")

@app.route("/process_payment", methods=["POST"])
def process_payment():
    if "user_id" not in session:
        return redirect("/sign")
    return render_template("Pricing/PaymentSuccess.html")

@app.route("/SuccessFul.html")
def successful():
    return render_template("SuccessFul.html")







@app.route("/library")
def library():
    
    if "user_id" not in session:
        return redirect("/sign")
    conn = get_db_connection()
    user_id = session.get("user_id")

    user = conn.execute(
        "SELECT name, profile_pic FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    
    
    return render_template("library.html",user=user)





import g4f

def call_model(prompt):
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}

@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.json.get("prompt", "")
    response = call_model(prompt)
    return jsonify(response)


@app.route("/upload_document", methods=["POST"])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    content = ""
    
    try:
        if ext == 'pdf':
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        elif ext == 'docx':
            doc = docx.Document(file)
            for para in doc.paragraphs:
                content += para.text + "\n"
        elif ext in ['txt', 'md', 'py', 'js', 'html', 'css']:
            content = file.read().decode('utf-8', errors='ignore')
        else:
            return jsonify({"error": f"Unsupported file type: {ext}"}), 400
        
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500













@app.route("/Save1.html" )
def save1():
    return render_template("Save1.html")


@app.route("/video_save.html" )
def video():
    return render_template("video_save.html")





@app.route("/save_notes", methods=["GET", "POST"])
def save_notes():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        tags = request.form["tags"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)",
            (title, content, tags)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("notes"))  # go back after saving

    return render_template("save_notes.html")
















@app.route("/notes")
def notes():
    query = request.args.get("q")

    conn = get_db_connection()

    if query:
        notes = conn.execute(
            "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ?",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
    else:
        notes = conn.execute("SELECT * FROM notes").fetchall()

    conn.close()
    return render_template("notes.html", notes=notes)



@app.route("/edit_note/<int:id>", methods=["GET","POST"])
def edit_note(id):
    conn = get_db_connection()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        tags = request.form["tags"]

        conn.execute(
            "UPDATE notes SET title=?, content=?, tags=? WHERE id=?",
            (title, content, tags, id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("notes"))

    note = conn.execute("SELECT * FROM notes WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("edit_note.html", note=note)


@app.route("/delete_note/<int:id>")
def delete_note(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM notes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("notes"))
















@app.route("/save")
def save():
    
    if "user_id" not in session:
        return redirect("/sign")

    conn = get_db_connection()
    user_id = session["user_id"]

    user = conn.execute(
        "SELECT name, profile_pic FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    contents = conn.execute(
        "SELECT * FROM content WHERE user_id=? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()

    conn.close()

    return render_template("Save.html", user=user, contents=contents)

@app.route("/save_all", methods=["POST"])
def save_all():

    if "user_id" not in session:
        return redirect("/sign")

    user_id = session["user_id"]

    title = request.form.get("title")
    category = request.form.get("category")
    type_ = request.form.get("type")

    link = request.form.get("link")
    video_link = request.form.get("video_link")
    notes = request.form.get("notes")

    date = request.form.get("date")
    time = request.form.get("time")

    file_path = None

    conn = get_db_connection()

    # -------------------------
    # FILE UPLOAD HANDLING
    # -------------------------

    if type_ == "pdf" and "pdf" in request.files:
        file = request.files["pdf"]
        if file and file.filename != "":
            filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

    elif type_ == "video" and "video" in request.files:
        file = request.files["video"]
        if file and file.filename != "":
            filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

    # -------------------------
    # INSERT INTO DATABASE
    # -------------------------

    conn.execute("""
        INSERT INTO content (
            user_id, title, category, type,
            file, link, notes,
            schedule_date, schedule_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        title,
        category,
        type_,
        file_path,
        video_link if type_ == "video" else link,
        notes,
        date,
        time
    ))

    conn.commit()
    conn.close()

    return redirect("/save")





@app.route("/delete/<int:id>")
def delete(id):

    if "user_id" not in session:
        return redirect("/sign")

    conn = get_db_connection()

    # OPTIONAL: delete only user's own content (IMPORTANT SECURITY)
    conn.execute(
        "DELETE FROM content WHERE id=? AND user_id=?",
        (id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/save")



@app.route("/update/<int:id>", methods=["POST"])
def update(id):

    if "user_id" not in session:
        return redirect("/sign")

    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    notes = request.form.get("notes", "").strip()

    if not title:
        return redirect(f"/edit/{id}")

    conn = get_db_connection()

    conn.execute("""
        UPDATE content
        SET title = ?, category = ?, notes = ?
        WHERE id = ? AND user_id = ?
    """, (
        title,
        category,
        notes,
        id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect("/save")


@app.route("/edit/<int:id>")
def edit(id):

    if "user_id" not in session:
        return redirect("/sign")

    conn = get_db_connection()

    item = conn.execute("""
        SELECT * FROM content
        WHERE id=? AND user_id=?
    """, (id, session["user_id"])).fetchone()

    conn.close()

    if item is None:
        return redirect("/save")

    return render_template("edit.html", item=item)






@app.route("/scheduling")
def schedule():

    if "user_id" not in session:
        return redirect("/sign")
    conn = get_db_connection()
    user_id = session.get("user_id")

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    return render_template("Scheduling.html",user=user)




@app.route("/api/calendar-events")
def calendar_events():

    if "user_id" not in session:
        return jsonify([])

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT title, category, schedule_date
        FROM content
        WHERE user_id = ?
    """, (session["user_id"],)).fetchall()

    conn.close()

    events = []

    for r in rows:
        events.append({
            "date": r["schedule_date"],   # must match JS format
            "title": r["title"],
            "type": r["category"] or "work"
        })

    return jsonify(events)


@app.route("/api/delete-event/<int:id>", methods=["DELETE"])
def delete_event(id):

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM content
        WHERE id = ? AND user_id = ?
    """, (id, session["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})








































if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)


