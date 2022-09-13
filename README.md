# Online Library System

## Description
This is my Final Project for CS50’s Introduction to Computer Science course.
My project is a web application made with Python (Flask, Jinja), HTML, CSS and SQL for managing library.

## Folder "templates"
Folder called "templates" includes HTML files. There are templates for homepage, homepage with navigate bar, login, register, contact admin, search for a book, reserve book, display user's reservations, admin's homepage, add new book to system, view archives, view books, view reservations or render apology if something goes wrong. The name of each template suggests what it renders on the page.

## Folder "static"
In folder called "static" there are images used to improve the view of the site. For instance there are navigate-bar's icons, background photo and CS50 logo. In the same folder there is a file called "styles.css" which has the same function - better look.

## File "library.db"
File called "library.db" is database with 5 tables (users, admins, books, reservations, history) on which the entire application relies:
- ```users```: (user_id, phone_number, email, hash),
- ```admins```: (admin_id, email, hash),
- ```books```: (book_id, title, description, genre, photo_adress),
- ```reservations```: (reservation_id, book_id, deadline, user_id),
- ```history```: (history_id, reservation_id, book_id, date_returned, deadline, user_id, email).

**Application uses sqlite3**

## File "app.py"
All these templates and database are controlled by Python (Flask) app called "app.py".
At the beginning there is configuration. In "app.py" there are many app routes that render page. Most of them require user to be logged in ```@login_required``` or have admin access as well ```@admin_access_required```. There is brief description of each (admin's) route:
- Route ```@app.route("/admin")``` displays homepage for admin.
- Route ```@app.route("/books_admin")``` renders all books from library collection.
- Route ```@app.route("/admin_search_books")``` searches through all books from library collection.
- Route ```@app.route("/add_new_book_admin")```  adds new book(s) to collection. Photo adress is a link to specific book cover, for example: <https://www.bookcity.pl/bigcovers/1/2/2/9/9780395071229.jpg>
- Route ```@app.route("/admin_reservations")``` shows all reservations.
- Route ```@app.route("/returned_to_collection")``` returns specific book to collection.
- Route ```@app.route("/send_reminder")``` send email notification to user (warning).
- Route ```@app.route("/admin_search")``` searches through reservations.
- Route ```@app.route("/admin_history")``` shows everything from archives.
- Route ```@app.route("/admin_history_search")``` searches archives with some filters.

That's all for admin's backend, especially routes. Afterwards there is user's backend:
- Route ```@app.route("/")``` just renders user's homepage.
- Route ```@app.route("/personal_data")``` shows user's personal data.
- Route ```@app.route("/search")``` enables user to search books by genres.
- Route ```@app.route("/reserve_book")``` enables user to reserve book and get email with QR Code with specific reservation data.
- Route ```@app.route("/reservations")``` shows user's reservations.
- Route ```@app.route("/contact_us")``` sends help form to administrator's email.
- Route ```@app.route("/login")``` enables user to log in.
- Route ```@app.route("/register")``` enables user to register.
- Route ```@app.route("/logout")``` logs user out.

**New account's email must be associated with "poczta.onet.pl" domain! Otherwise email system will not work properly.**

## File "helpers.py"
In "helpers.py" as its name suggests there are functions that help "app.py" work.
- Function ```login_required``` requires being logged in.
- Function ```admin_access_required``` requires administrator access.
- Function ```apology``` renders apology image if something goes wrong.
- Function ```generate_qrcode_for_reservation``` generates QR Code for specific reservation and creates file called "reservation.jpg".
- Function ```send_reservation_details``` sends email to user with QR Code attached and reservation details.
## File "add_admin_to_db.py"
The last file is called "add_admin_to_db.py". It was used only once to add administrator to database with hash.

**I assumed that there is only one admin with admin_id equal to 1.**

## Snippets (more in "snippets" folder)

![alt text](https://github.com/Resmakor/Online-Library-System/blob/main/snippets/Przechwytywanie.PNG?raw=true)
##

![alt text](https://github.com/Resmakor/Online-Library-System/blob/main/snippets/Przechwytywanie3.PNG?raw=true)
##

![alt text](https://github.com/Resmakor/Online-Library-System/blob/main/snippets/Przechwytywanie4.PNG?raw=true)
##

![alt text](https://github.com/Resmakor/Online-Library-System/blob/main/snippets/Przechwytywanie5.PNG?raw=true)
##

![alt text](https://github.com/Resmakor/Online-Library-System/blob/main/snippets/Przechwytywanie6.PNG?raw=true)
##

![alt text](https://github.com/Resmakor/Online-Library-System/blob/main/snippets/Przechwytywanie8.PNG?raw=true)
