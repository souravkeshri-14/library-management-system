# Library Management System — Streamlit

A web-based Library Management System built with **Streamlit + MySQL + PyMySQL**.

## Features

### Public
- View the **book collection without logging in**
- Search books by title or author
- See available quantity/status

### User
- **Sign up** and create a user account
- **Login / Logout**
- Send a **book request** with student name and registration number
- View request status: **Pending / Accepted / Rejected**
- See the Issue ID after an admin accepts the request
- Users cannot directly issue, return, add, update, or delete books

### Admin
- Login using an admin account already present in the `users` table
- Add, update, and delete books
- View pending requests
- **Accept & Issue** a request
- Reject a request with an optional note
- Return books using the Issue ID
- View request history and issue history

## Database

Existing tables expected by the project:

- `users(username, password, role)`
- `books(id, title, author, quantity)`
- `issue_books(id, book_id, student_name, reg_no, issue_date, return_date)`

The app creates the new `book_requests` table automatically. If your MySQL account cannot create tables, run `setup.sql` manually.

`book_requests` stores:

- request ID
- book ID
- username
- student name
- registration number
- request date
- request status
- admin note
- issue ID after acceptance

## Local setup

Create `.streamlit/secrets.toml`:

```toml
[mysql]
host = "localhost"
port = 3306
user = "YOUR_MYSQL_USER"
password = "YOUR_MYSQL_PASSWORD"
database = "librarybooks"
```

Do **not** upload `secrets.toml` to GitHub.

Then run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

1. Push this project to GitHub.
2. Deploy `app.py` from Streamlit Community Cloud.
3. Add the MySQL values under the deployment's **Secrets** settings.
4. Use a MySQL database reachable from the cloud app; `localhost` refers to the cloud machine, not your personal computer.

## Important security note

The app stores **new signup passwords as SHA-256 hashes**. Existing accounts using older plaintext passwords can still log in once; after a successful login, their password is upgraded to a hash.

For a real production system, use a password-hashing algorithm designed for passwords such as Argon2 or bcrypt and use HTTPS/TLS for the database connection where required.


### Automatic Library Registration Number
- Every user account gets a permanent **Library Registration No.** automatically.
- New accounts receive it during signup.
- Existing accounts without one receive it automatically on their next login.
- The number is shown in the user dashboard and is automatically used when sending book requests.
- Users cannot manually change the registration number.

### Offline Customer Book Issue
- Admins can directly issue an available book to a customer who visits the library without logging in.
- The admin enters the customer name and can enter a registration number or leave it blank to generate an `OFF########` number automatically.
- The book quantity decreases immediately and an Issue ID is created.
- Offline issues are marked as **Offline** in Issue History.
- Online requests accepted by an admin are marked as **Online**.
