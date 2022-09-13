import os
from flask import redirect, render_template, session
from flask_mail import Mail, Message
from functools import wraps

import qrcode
import magic

def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def admin_access_required(f):
    """
    Decorate routes to require admin access. I assume that we have only 1 admin with unique user_id = 1.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") != 1:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def generate_qrcode_for_reservation(book_id, book_title, reservation_id, user_email, user_id):
    """Generates QR Code for specific reservation and saves it as reservation.jpg"""
    book_id = str(book_id)
    user_email = str(user_email)
    final = f'Book ID: {book_id}; Book title: {book_title}; Reservation id: {reservation_id}; Email: {user_email}; User ID: {user_id};'
    img = qrcode.make(final)
    img.save("reservation.jpg")

def send_reservation_details(book_id, book_title, reservation_id, user_email, mail):
    """Sends QR Code to specific user and reservation details, removes resevation.jpg afterwards"""
    subject = f'Your QR Code for {book_title} reservation!'
    beginning_of_message = f'Here is your QR Code for {book_title} with id {book_id}. Your reservation_id is {reservation_id}. Show QR Code to our staff.'
    admin_email = str(os.environ['admin_email'])
    msg = Message(subject, sender=admin_email, recipients=[user_email])
    msg.body = beginning_of_message
    mime = magic.from_file("reservation.jpg", mime=True)
    with open("reservation.jpg", 'rb') as f:
        msg.attach(filename="reservation.jpg", content_type=mime, data=f.read(), disposition=None, headers=None)
    mail.send(msg)
    if os.path.exists("reservation.jpg"):
        os.remove("reservation.jpg")