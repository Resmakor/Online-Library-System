"""Program used to add administrator to database"""
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

db = SQL("sqlite:///library.db")

def save_hash():
    #hash = generate_password_hash(paste password)
    db.execute("INSERT INTO admins (email, hash) VALUES(?, ?)", "dafas123@poczta.onet.pl", hash)

#save_hash()
