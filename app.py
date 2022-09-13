import os

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_mail import Mail, Message

from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, apology, send_reservation_details, admin_access_required, generate_qrcode_for_reservation
from datetime import datetime, timedelta


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Configure administator's mail
app.config['MAIL_SERVER']= 'smtp.poczta.onet.pl'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = str(os.environ['admin_email'])
app.config['MAIL_PASSWORD'] = str(os.environ['admin_password'])
app.config['MAIL_USE_TLS'] = False
mail = Mail(app)

Session(app)

# Configure CS50 Library to use SQLite database called library.db
db = SQL("sqlite:///library.db")

MAX_AMOUNT_OF_CHARACTERS = 1000
MAX_AMOUNT_OF_RESERVATIONS = 5

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Admin's backend!

@app.route("/admin")
@login_required
@admin_access_required
def homepage_admin():
    return render_template("home_admin.html")

@app.route("/books_admin")
@login_required
@admin_access_required
def books_admin():
    """Render all books from library collection"""
    books = db.execute(
        "SELECT book_id, title, description, genre, photo_adress FROM books")
    occupied_books = db.execute(
        "SELECT books.book_id, title, description, genre, photo_adress FROM books INNER JOIN reservations ON books.book_id=reservations.book_id WHERE books.book_id IN (SELECT reservations.book_id FROM reservations)")
    occupied_books_ids_only = []
    for occupied_book in occupied_books:
        occupied_books_ids_only.append(occupied_book["book_id"])
    return render_template("books_admin.html", books=books, occupied_books_ids_only=occupied_books_ids_only)


@app.route("/admin_search_books", methods=["GET", "POST"])
@admin_access_required
@login_required
def admin_search_books():
    """Search through all books from library collection"""
    if request.method == "POST":
        if not request.form.get("search_type_books") or not request.form.get("ID"):
            return redirect("/books_admin")
        search_type = request.form.get("search_type_books")
        search_id_title = request.form.get("ID")
        if search_type == "Book":
            books = db.execute("SELECT book_id, title, description, genre, photo_adress FROM books WHERE book_id = ?", search_id_title)
            return render_template("books_admin.html", books=books)
        elif search_type == "Title":
            sql_search_id_title = "%" + search_id_title + "%"
            books = db.execute(f"SELECT book_id, title, description, genre, photo_adress FROM books WHERE title LIKE ?", sql_search_id_title)
            return render_template("books_admin.html", books=books)
        elif search_type == "Genre":
            sql_search_id_title = "%" + search_id_title + "%"
            books = db.execute(f"SELECT book_id, title, description, genre, photo_adress FROM books WHERE genre LIKE ?", sql_search_id_title)
            return render_template("books_admin.html", books=books)
    else:
        return redirect("/books_admin")

@app.route("/add_new_book_admin", methods=["GET", "POST"])
@login_required
@admin_access_required
def add_new_book():
    """Add new book(s) to collection"""
    if request.method == "POST":
        if not request.form.get("title"):
            return apology("must provide title", 400)
        elif not request.form.get("description"):
            return apology("must provide description", 400)
        elif not request.form.get("genre"):
            return apology("must provide genre", 400)
        elif not request.form.get("photo_adress"):
            return apology("must provide photo adress", 400)
        elif not request.form.get("ammount"):
            return apology("must provide ammount", 400)

        title = str(request.form.get("title"))
        description = str(request.form.get("description"))
        genre = str(request.form.get("genre"))
        photo_adress = request.form.get("photo_adress")
        ammount = int(request.form.get("ammount"))

        if ammount < 1:
            return apology("must provide ammount >= 1", 400)
        elif len(description) > MAX_AMOUNT_OF_CHARACTERS:
            return apology(f"must provide description with no more than {MAX_AMOUNT_OF_CHARACTERS} characters", 400)

        for i in range(ammount):
            db.execute(
                "INSERT INTO books (description, title, genre, photo_adress) VALUES(?, ?, ?, ?)", description, title, genre, photo_adress)
        return redirect("/books_admin")
    else:
        return render_template("add_new_book_admin.html")

@app.route("/admin_reservations", methods=["GET", "POST"])
@admin_access_required
@login_required
def admin_reservations():
    """Show all reservations"""
    reservations_dict = db.execute(
        "SELECT reservation_id, book_id, deadline, users.user_id, users.email, users.phone_number FROM reservations INNER JOIN users ON users.user_id=reservations.user_id")
    return render_template("admin_reservations.html", reservations=reservations_dict)

@app.route("/returned_to_collection", methods=["GET", "POST"])
@admin_access_required
@login_required
def returned_to_collection():
    """Return specific book to collection (book is free)"""
    if request.method == "POST":
        reservation_id = request.form.get("reservation_id")
        rows = db.execute("SELECT book_id, deadline, users.user_id, email FROM reservations INNER JOIN users ON users.user_id=reservations.user_id WHERE reservation_id = ?", reservation_id)[0]
        book_id = rows["book_id"]
        user_id = rows["user_id"]
        user_email = rows["email"]
        deadline = rows["deadline"]
        end_datetime = datetime.now().strftime("%Y-%m-%d")
        end_date = datetime.strptime(end_datetime, "%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")
        db.execute("INSERT INTO history (reservation_id, book_id, user_id, email, deadline, date_returned) VALUES(?, ?, ?, ?, ?, ?)", reservation_id, book_id, user_id, user_email, deadline, end_date)
        db.execute("DELETE FROM reservations WHERE reservation_id = ?", reservation_id)
    return redirect("/admin_reservations")


@app.route("/send_reminder", methods=["GET", "POST"])
@admin_access_required
@login_required
def send_reminder():
    """Warn user"""
    if request.method == "POST":
        reservation_id = request.form.get("reservation_id")
        specific_reservation = db.execute("SELECT book_id, deadline FROM reservations WHERE reservation_id = ?", reservation_id)[0]
        book_id = specific_reservation["book_id"]
        deadline = specific_reservation["deadline"]
        user_email = db.execute("SELECT email FROM users INNER JOIN reservations on users.user_id=reservations.user_id WHERE reservation_id = ?", reservation_id)[0]["email"]
        admin_email = str(os.environ['admin_email'])
        subject = f'Return book to the library! Reminder for reservation ID {reservation_id}'
        beginning_of_message = f'Please return borrowed book within 5 days. Book id : {book_id}, Reservation ID : {reservation_id}. Your first deadline was {deadline}.\n'
        msg = Message(subject, sender=admin_email, recipients=[user_email])
        msg.body = beginning_of_message
        try:
            mail.send(msg)
        except:
            return apology("Something went wrong", 400)
    return redirect("/admin_reservations")

@app.route("/admin_search", methods=["GET", "POST"])
@admin_access_required
@login_required
def admin_search():
    """Search through reservations"""
    if request.method == "POST":
        if not request.form.get("search_type") or not request.form.get("ID"):
            return redirect("/admin_reservations")
        search_type = request.form.get("search_type")
        search_id = request.form.get("ID")
        if search_type == "User":
            reservations_dict = db.execute(
                                "SELECT reservation_id, book_id, deadline, users.user_id, users.email, users.phone_number FROM reservations INNER JOIN users ON users.user_id=reservations.user_id WHERE reservations.user_id = ? ", search_id)
            return render_template("admin_reservations.html", reservations=reservations_dict)

        elif search_type == "Reservation":
            reservations_dict = db.execute(
                                "SELECT reservation_id, book_id, deadline, users.user_id, users.email, users.phone_number FROM reservations INNER JOIN users ON users.user_id=reservations.user_id WHERE reservations.reservation_id = ? ", search_id)
            return render_template("admin_reservations.html", reservations=reservations_dict)
        elif search_type == "Book":
            reservations_dict = db.execute(
                                "SELECT reservation_id, book_id, deadline, users.user_id, users.email, users.phone_number FROM reservations INNER JOIN users ON users.user_id=reservations.user_id WHERE reservations.book_id = ? ", search_id)
            return render_template("admin_reservations.html", reservations=reservations_dict)
    else:
        return redirect("/admin_reservations")


@app.route("/admin_history", methods=["GET", "POST"])
@admin_access_required
@login_required
def admin_history():
    """Show everything from archives"""
    rows = db.execute("SELECT * FROM history")
    return render_template("admin_history.html", rows=rows)


@app.route("/admin_history_search", methods=["GET", "POST"])
@admin_access_required
@login_required
def admin_history_search():
    """Search archives by admin"""
    if request.method == "POST":
        if not request.form.get("search_type_history") or not request.form.get("ID"):
            return redirect("/admin_history")
        search_type = request.form.get("search_type_history")
        search_id = request.form.get("ID")
        if search_type == "User":
            rows = db.execute("SELECT * FROM history WHERE user_id = ? ", search_id)
            return render_template("admin_history.html", rows=rows)
        elif search_type == "Book":
            rows = db.execute("SELECT * FROM history WHERE book_id = ? ", search_id)
            return render_template("admin_history.html", rows=rows)
        elif search_type == "Reservation":
            rows = db.execute("SELECT * FROM history WHERE reservation_id = ? ", search_id)
            return render_template("admin_history.html", rows=rows)
    else:
        return redirect("/admin_reservations")

# User's backend!

@app.route("/")
@login_required
def homepage():
    return render_template("home.html")


@app.route("/personal_data")
@login_required
def personal_data():
    """Show user's personal data"""
    rows = db.execute("SELECT  user_id, email, phone_number FROM users WHERE user_id = ?", session["user_id"])
    user_id = rows[0]["user_id"]
    email = rows[0]["email"]
    phone_number = rows[0]["phone_number"]
    return render_template("personal_data.html", user_id=user_id, email=email, phone_number=phone_number)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search books by genres"""
    genres = db.execute("SELECT DISTINCT genre FROM books WHERE book_id NOT IN (SELECT book_id FROM reservations)")
    if request.method == "POST":
        chosen_genre = request.form.get("chosen_genre")
        if chosen_genre == "All":
            books_dict = db.execute(
            "SELECT book_id, title, description, genre, photo_adress FROM books WHERE book_id NOT IN (SELECT book_id FROM reservations)")
        else:
            books_dict = db.execute(
                "SELECT book_id, title, description, genre, photo_adress FROM books WHERE book_id NOT IN (SELECT book_id FROM reservations) AND genre LIKE ?", chosen_genre)
    else:
        books_dict = db.execute(
            "SELECT book_id, title, description, genre, photo_adress FROM books WHERE book_id NOT IN (SELECT book_id FROM reservations)")
    return render_template("search.html", books=books_dict, genres=genres)


@app.route("/reserve_book", methods=["GET", "POST"])
@login_required
def reserve_book():
    """Reserve book for user"""
    if request.method == "POST":
        reservations_dict = db.execute("SELECT reservation_id FROM reservations WHERE user_id = ?", session["user_id"])
        if len(reservations_dict) >= MAX_AMOUNT_OF_RESERVATIONS:
            return apology(f"One student can borrow only {MAX_AMOUNT_OF_RESERVATIONS} books!", 400)

        user_rows = db.execute("SELECT email FROM users WHERE user_id = ?", session["user_id"])
        user_id = session["user_id"]
        user_email = user_rows[0]["email"]
        book_id = request.form.get("reserved_book")

        begin_datetime = datetime.now().strftime("%Y-%m-%d")
        begin_date = datetime.strptime(begin_datetime, "%Y-%m-%d")
        
        # Deadline is 30 days later
        deadline = (begin_date + timedelta(days=30)).strftime("%Y-%m-%d")
        begin_date = begin_date.strftime("%Y-%m-%d")
        db.execute(
            "INSERT INTO reservations (book_id, user_id, deadline) VALUES(?, ?, ?)", book_id, user_id, deadline)

        reservation_id = db.execute("SELECT reservation_id FROM reservations ORDER BY reservation_id DESC LIMIT 1")[0]["reservation_id"]
        book_title = db.execute("SELECT title FROM books WHERE book_id = ?", book_id)[0]["title"]

        generate_qrcode_for_reservation(book_id, book_title, reservation_id, user_email, user_id)
        send_reservation_details(book_id, book_title, reservation_id, user_email, mail)
        return redirect("/reservations")
    else:
        return redirect("/reservations")

@app.route("/reservations", methods=["GET", "POST"])
@login_required
def reservations():
    """Show user's reservations"""
    reservations_dict = db.execute(
        "SELECT reservation_id, reservations.book_id, title, photo_adress, deadline FROM reservations INNER JOIN books ON books.book_id=reservations.book_id WHERE user_id = ?", session["user_id"])
    return render_template("reservations.html", reservations=reservations_dict)

@app.route("/contact_us", methods=["GET", "POST"])
@login_required
def contact_us():
    """Send help form to administrator"""
    if request.method == "POST":
        if not request.form.get("message"):
            return apology("must provide message", 400)

        message = str(request.form.get("message"))
        if len(message) > MAX_AMOUNT_OF_CHARACTERS:
            return apology(f"Your message is too long! Max {MAX_AMOUNT_OF_CHARACTERS} characters", 400)

        rows = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])

        admin_email = str(os.environ['admin_email'])
        user_email = str(rows[0]['email'])
        user_phone = str(rows[0]['phone_number'])

        subject = f'New library message from {user_email} appears!'
        beginning_of_message = f'User {user_email} (ID {session["user_id"]}) with phone number {user_phone} wrote to you: \n'
        message = beginning_of_message + message
        msg = Message(subject, sender=admin_email, recipients=[admin_email])
        msg.body = message
        try:
            mail.send(msg)
        except:
            return apology("Something went wrong", 400)
        return redirect("/")

    else:
        return render_template("contact_us.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        if not request.form.get("email"):
            return apology("must provide email", 400)

        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Check if user is an admin
        admin_rows = db.execute("SELECT * FROM admins WHERE email = ?", request.form.get("email"))
        if len(admin_rows) == 1 and check_password_hash(admin_rows[0]["hash"], request.form.get("password")):
            session["user_id"] = admin_rows[0]["admin_id"]
            return redirect("/admin")

        rows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""
    if request.method == "POST":
        if not request.form.get("email"):
            return apology("must provide email", 400)
        elif not request.form.get("phone_number"):
            return apology("must provide phone number", 400)
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif not request.form.get("check_password"):
            return apology("must confirm password", 400)

        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        password = request.form.get("password")
        confirmation = request.form.get("check_password")

        if password != confirmation:
            return apology("passwords do not match", 400)

        rows = db.execute("SELECT * FROM users WHERE email = ?", email)
        if len(rows) >= 1:
            return apology("username with that email already exists", 400)

        hash = generate_password_hash(password)
        db.execute("INSERT INTO users (phone_number, email, hash) VALUES(?, ?, ?)", phone_number, email, hash)
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")