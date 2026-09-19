import hashlib
import secrets as pysecrets
from datetime import date

import pymysql
import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide",
)


# -----------------------------
# Database
# -----------------------------
def get_db():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        port=int(st.secrets["mysql"].get("port", 3306)),
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        cursorclass=pymysql.cursors.Cursor,
        autocommit=False,
        ssl={"check_hostname": False},
    )


def fetch_all(query, params=()):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        db.close()


def execute_query(query, params=()):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(query, params)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def ensure_request_table():
    """Create the book request table if it does not already exist."""
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    book_id INT NOT NULL,
                    username VARCHAR(100) NOT NULL,
                    student_name VARCHAR(150) NOT NULL,
                    reg_no VARCHAR(100) NOT NULL,
                    request_date DATE NOT NULL,
                    status ENUM('Pending', 'Accepted', 'Rejected') NOT NULL DEFAULT 'Pending',
                    admin_note VARCHAR(255) DEFAULT NULL,
                    issue_id INT DEFAULT NULL,
                    INDEX idx_request_username (username),
                    INDEX idx_request_status (status),
                    INDEX idx_request_book (book_id)
                )
            """)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def ensure_issue_schema():
    """Make issue_books compatible with library registration numbers and issue source."""
    db = get_db()
    try:
        with db.cursor() as cursor:
            # Older databases may have reg_no as INT. Convert it to text so values
            # such as LIB03144126 and OFF12345678 can be stored.
            cursor.execute(
                "SELECT DATA_TYPE FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='issue_books' AND COLUMN_NAME='reg_no'",
                (st.secrets["mysql"]["database"],),
            )
            reg_row = cursor.fetchone()
            if reg_row and reg_row[0].lower() not in {"varchar", "char", "text"}:
                cursor.execute(
                    "ALTER TABLE issue_books MODIFY COLUMN reg_no VARCHAR(30) NOT NULL"
                )

            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='issue_books' AND COLUMN_NAME='issue_type'",
                (st.secrets["mysql"]["database"],),
            )
            has_issue_type = cursor.fetchone()[0]
            if not has_issue_type:
                cursor.execute(
                    "ALTER TABLE issue_books ADD COLUMN issue_type VARCHAR(20) NOT NULL DEFAULT 'Online'"
                )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def generate_offline_reg_no():
    """Generate a unique registration number for an offline customer."""
    while True:
        reg_no = "OFF" + str(pysecrets.randbelow(100_000_000)).zfill(8)
        if not fetch_all("SELECT id FROM issue_books WHERE reg_no=%s", (reg_no,)):
            return reg_no


# -----------------------------
# Password helpers
# -----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def password_matches(password, stored_password):
    # Supports existing plaintext accounts and new hashed accounts.
    # New signup accounts are always stored as SHA-256 hashes.
    return stored_password == password or stored_password == hash_password(password)


# -----------------------------
# Session state
# -----------------------------
for key, default in {
    "logged_in": False,
    "username": "",
    "role": "",
    "reg_no": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# -----------------------------
# User registration number
# -----------------------------
def ensure_user_reg_no_column():
    """Add a unique library registration number column to the existing users table."""
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users' AND COLUMN_NAME='reg_no'",
                (st.secrets["mysql"]["database"],),
            )
            exists = cursor.fetchone()[0]
            if not exists:
                cursor.execute("ALTER TABLE users ADD COLUMN reg_no VARCHAR(30) NULL UNIQUE")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def generate_reg_no():
    """Generate a unique library registration number."""
    while True:
        reg_no = "LIB" + str(pysecrets.randbelow(100_000_000)).zfill(8)
        if not fetch_all("SELECT username FROM users WHERE reg_no=%s", (reg_no,)):
            return reg_no


def get_or_create_reg_no(username):
    """Give an old account a registration number if it does not have one."""
    rows = fetch_all("SELECT reg_no FROM users WHERE username=%s", (username,))
    if not rows:
        return None
    reg_no = rows[0][0]
    if reg_no:
        return reg_no

    reg_no = generate_reg_no()
    execute_query(
        "UPDATE users SET reg_no=%s WHERE username=%s AND (reg_no IS NULL OR reg_no='')",
        (reg_no, username),
    )
    return reg_no


# -----------------------------
# Setup database tables
# -----------------------------
try:
    ensure_user_reg_no_column()
    ensure_request_table()
    ensure_issue_schema()
except Exception as e:
    st.error(f"Could not prepare the database tables: {e}")
    st.stop()


# -----------------------------
# Public book collection
# -----------------------------
st.title("📚 Library Management System")
st.caption("Browse the library collection without logging in.")

try:
    books = fetch_all(
        "SELECT id, title, author, quantity FROM books ORDER BY id"
    )
except Exception as e:
    st.error(f"Could not load books: {e}")
    st.stop()

total_copies = sum(int(row[3]) for row in books) if books else 0
available_titles = sum(1 for row in books if int(row[3]) > 0)

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total Copies", total_copies)
with c2:
    st.metric("Book Titles", len(books))
with c3:
    st.metric("Available Titles", available_titles)

st.subheader("🔎 Book Collection")
search = st.text_input(
    "Search by title or author",
    placeholder="Enter a title or author",
    key="public_search",
)

if search.strip():
    search_value = "%" + search.strip() + "%"
    books_display = fetch_all(
        "SELECT id, title, author, quantity "
        "FROM books WHERE title LIKE %s OR author LIKE %s ORDER BY id",
        (search_value, search_value),
    )
else:
    books_display = books

if books_display:
    table_rows = [
        {
            "ID": row[0],
            "Title": row[1],
            "Author": row[2],
            "Quantity": row[3],
            "Availability": "Available" if int(row[3]) > 0 else "Not Available",
        }
        for row in books_display
    ]

    df = pd.DataFrame(table_rows)

    # Center the complete table
    st.markdown(
        """
        <style>
        .book-table {
            width: 100%;
            border-collapse: collapse;
            text-align: center;
        }

        .book-table th,
        .book-table td {
            text-align: center !important;
            padding: 10px;
            border: 1px solid #333;
        }

        .book-table th {
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        df.to_html(
            index=False,
            classes="book-table",
            escape=True
        ),
        unsafe_allow_html=True
    )

else:
    st.info("No books found.")

st.divider()


# -----------------------------
# Login / Signup for visitors
# -----------------------------
if not st.session_state.logged_in:
    st.subheader("🔐 Account Access")
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_clicked = st.form_submit_button("Login", type="primary")

        if login_clicked:
            if not username.strip() or not password:
                st.error("Enter both username and password.")
            else:
                try:
                    rows = fetch_all(
                        "SELECT password, role, reg_no FROM users WHERE username=%s",
                        (username.strip(),),
                    )

                    if rows and password_matches(password, rows[0][0]):
                        stored_password, role, reg_no = rows[0]

                        # Upgrade old plaintext accounts to a hash after successful login.
                        if stored_password == password:
                            execute_query(
                                "UPDATE users SET password=%s WHERE username=%s",
                                (hash_password(password), username.strip()),
                            )

                        st.session_state.logged_in = True
                        st.session_state.username = username.strip()
                        st.session_state.role = role
                        st.session_state.reg_no = reg_no or get_or_create_reg_no(username.strip())
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                except Exception as e:
                    st.error(f"Login error: {e}")

    with signup_tab:
        st.write("Create a user account to request books.")

        with st.form("signup_form"):
            new_username = st.text_input("Username", key="signup_username")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input(
                "Confirm Password", type="password", key="signup_confirm"
            )
            signup_clicked = st.form_submit_button("Create Account", type="primary")

        if signup_clicked:
            username_clean = new_username.strip()

            if len(username_clean) < 3:
                st.error("Username must contain at least 3 characters.")
            elif len(new_password) < 6:
                st.error("Password must contain at least 6 characters.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    existing = fetch_all(
                        "SELECT username FROM users WHERE username=%s",
                        (username_clean,),
                    )

                    if existing:
                        st.error("Username already exists. Choose another username.")
                    else:
                        new_reg_no = generate_reg_no()
                        execute_query(
                            "INSERT INTO users (username, password, role, reg_no) VALUES (%s, %s, %s, %s)",
                            (username_clean, hash_password(new_password), "user", new_reg_no),
                        )
                        st.success(
                            f"Account created successfully. Your Library Registration No. is **{new_reg_no}**. "
                            "Use this number for future library requests."
                        )
                except Exception as e:
                    st.error(f"Could not create account: {e}")

    st.info("You can browse the book collection above without logging in. Login is required only to request a book.")
    st.stop()


# -----------------------------
# Logged-in account
# -----------------------------
role = st.session_state.role
username = st.session_state.username

with st.sidebar:
    st.header("👤 Account")
    st.write(f"**User:** {username}")
    st.write(f"**Role:** {role}")
    st.write(f"**Library Registration No.:** {st.session_state.reg_no}")

    if st.button("Logout", width="stretch"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.reg_no = ""
        st.rerun()

st.success(f"Logged in as **{username}** ({role})")


# -----------------------------
# Admin: manage books
# -----------------------------
if role == "admin":
    st.subheader("🛠️ Manage Books")

    selected_book = None
    if books:
        book_options = {
            f"{row[0]} — {row[1]} — {row[2]}": row
            for row in books
        }
        selected_label = st.selectbox(
            "Select a book to edit/delete",
            ["None"] + list(book_options.keys()),
            key="admin_book_select",
        )
        if selected_label != "None":
            selected_book = book_options[selected_label]

    default_title = selected_book[1] if selected_book else ""
    default_author = selected_book[2] if selected_book else ""
    default_qty = int(selected_book[3]) if selected_book else 1

    with st.form("book_form"):
        title = st.text_input("Book Title", value=default_title)
        author = st.text_input("Author", value=default_author)
        quantity = st.number_input(
            "Quantity",
            min_value=0,
            value=default_qty,
            step=1,
        )

        b1, b2, b3 = st.columns(3)
        add_clicked = b1.form_submit_button("➕ Add Book", type="primary")
        update_clicked = b2.form_submit_button("✏️ Update Book")
        delete_clicked = b3.form_submit_button("🗑️ Delete Book")

    if add_clicked:
        if not title.strip() or not author.strip() or quantity <= 0:
            st.error("All fields are required and quantity must be greater than 0.")
        else:
            try:
                execute_query(
                    "INSERT INTO books (title, author, quantity) VALUES (%s, %s, %s)",
                    (title.strip(), author.strip(), int(quantity)),
                )
                st.success("Book added successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not add book: {e}")

    if update_clicked:
        if selected_book is None:
            st.error("Please select a book to update.")
        elif not title.strip() or not author.strip() or quantity < 0:
            st.error("Enter valid book details.")
        else:
            try:
                execute_query(
                    "UPDATE books SET title=%s, author=%s, quantity=%s WHERE id=%s",
                    (title.strip(), author.strip(), int(quantity), selected_book[0]),
                )
                st.success("Book updated successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not update book: {e}")

    if delete_clicked:
        if selected_book is None:
            st.error("Select a book to delete.")
        else:
            try:
                execute_query("DELETE FROM books WHERE id=%s", (selected_book[0],))
                st.success("Book deleted successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not delete book: {e}")

    st.divider()

    # -----------------------------
    # Admin: pending requests
    # -----------------------------
    st.subheader("📨 Book Requests")

    pending_requests = fetch_all("""
        SELECT
            r.id,
            r.username,
            r.student_name,
            r.reg_no,
            b.title,
            b.author,
            r.request_date,
            r.status,
            r.admin_note
        FROM book_requests r
        JOIN books b ON r.book_id = b.id
        WHERE r.status = 'Pending'
        ORDER BY r.id DESC
    """)

    if pending_requests:
        st.dataframe(
            [
                {
                    "Request ID": r[0],
                    "Username": r[1],
                    "Student Name": r[2],
                    "Reg No.": r[3],
                    "Book": r[4],
                    "Author": r[5],
                    "Request Date": r[6],
                    "Status": r[7],
                    "Admin Note": r[8] or "",
                }
                for r in pending_requests
            ],
            hide_index=True,
            width="stretch",
        )

        request_options = {
            f"Request #{r[0]} — {r[4]} — {r[2]} ({r[3]})": r
            for r in pending_requests
        }
        selected_request_label = st.selectbox(
            "Select a request",
            list(request_options.keys()),
            key="request_select",
        )
        selected_request = request_options[selected_request_label]

        admin_note = st.text_input(
            "Admin note (optional)",
            key="admin_request_note",
            placeholder="Example: Please collect from the library counter.",
        )

        a1, a2 = st.columns(2)
        accept_clicked = a1.button("✅ Accept & Issue", type="primary", width="stretch")
        reject_clicked = a2.button("❌ Reject Request", width="stretch")

        if accept_clicked:
            request_id = selected_request[0]
            book_id = fetch_all(
                "SELECT book_id FROM book_requests WHERE id=%s AND status='Pending'",
                (request_id,),
            )

            if not book_id:
                st.error("This request is no longer pending.")
                st.rerun()

            db = get_db()
            try:
                with db.cursor() as cursor:
                    # Lock the request and book rows during acceptance.
                    cursor.execute(
                        "SELECT book_id, username FROM book_requests "
                        "WHERE id=%s AND status='Pending' FOR UPDATE",
                        (request_id,),
                    )
                    request_row = cursor.fetchone()

                    if not request_row:
                        raise ValueError("This request is no longer pending.")

                    locked_book_id, request_username = request_row
                    cursor.execute(
                        "SELECT title, quantity FROM books WHERE id=%s FOR UPDATE",
                        (locked_book_id,),
                    )
                    book_row = cursor.fetchone()

                    if not book_row:
                        raise ValueError("The requested book no longer exists.")
                    if int(book_row[1]) <= 0:
                        raise ValueError("This book is currently out of stock.")

                    cursor.execute(
                        "SELECT student_name, reg_no FROM book_requests WHERE id=%s",
                        (request_id,),
                    )
                    student_row = cursor.fetchone()

                    cursor.execute(
                        "INSERT INTO issue_books "
                        "(book_id, student_name, reg_no, issue_date, issue_type) "
                        "VALUES (%s, %s, %s, %s, 'Online')",
                        (
                            locked_book_id,
                            student_row[0],
                            student_row[1],
                            date.today(),
                        ),
                    )
                    issue_id = cursor.lastrowid

                    cursor.execute(
                        "UPDATE books SET quantity = quantity - 1 WHERE id=%s",
                        (locked_book_id,),
                    )

                    cursor.execute(
                        "UPDATE book_requests "
                        "SET status='Accepted', admin_note=%s, issue_id=%s "
                        "WHERE id=%s",
                        (admin_note.strip() or None, issue_id, request_id),
                    )

                db.commit()
                st.success(
                    f"Request #{request_id} accepted. Book issued to {request_username}. "
                    f"Issue ID: {issue_id}"
                )
                st.rerun()
            except Exception as e:
                db.rollback()
                st.error(f"Could not accept request: {e}")
            finally:
                db.close()

        if reject_clicked:
            try:
                execute_query(
                    "UPDATE book_requests SET status='Rejected', admin_note=%s "
                    "WHERE id=%s AND status='Pending'",
                    (admin_note.strip() or None, selected_request[0]),
                )
                st.success(f"Request #{selected_request[0]} rejected.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not reject request: {e}")
    else:
        st.info("No pending book requests.")

    st.divider()

    # -----------------------------
    # Admin: offline customer issue
    # -----------------------------
    st.subheader("🏪 Issue Book to Offline Customer")
    st.caption("Use this when a customer visits the library in person and does not have a website account.")

    available_offline_books = [row for row in books if int(row[3]) > 0]
    if available_offline_books:
        offline_options = {
            f"{row[0]} — {row[1]} — {row[2]} (Available: {row[3]})": row
            for row in available_offline_books
        }

        with st.form("offline_issue_form"):
            offline_book_label = st.selectbox(
                "Select Book",
                list(offline_options.keys()),
                key="offline_book_select",
            )
            offline_book = offline_options[offline_book_label]
            offline_customer_name = st.text_input("Customer Name")
            offline_reg_no = st.text_input(
                "Customer Registration No. (optional)",
                placeholder="Leave blank to generate automatically",
            )
            offline_issue_clicked = st.form_submit_button(
                "📚 Issue Book",
                type="primary",
            )

        if offline_issue_clicked:
            if not offline_customer_name.strip():
                st.error("Enter the customer's name.")
            else:
                try:
                    customer_reg_no = offline_reg_no.strip() or generate_offline_reg_no()
                    db = get_db()
                    try:
                        with db.cursor() as cursor:
                            cursor.execute(
                                "SELECT quantity FROM books WHERE id=%s FOR UPDATE",
                                (offline_book[0],),
                            )
                            book_row = cursor.fetchone()

                            if not book_row:
                                raise ValueError("The selected book no longer exists.")
                            if int(book_row[0]) <= 0:
                                raise ValueError("This book is currently out of stock.")

                            cursor.execute(
                                "INSERT INTO issue_books "
                                "(book_id, student_name, reg_no, issue_date, issue_type) "
                                "VALUES (%s, %s, %s, %s, 'Offline')",
                                (
                                    offline_book[0],
                                    offline_customer_name.strip(),
                                    customer_reg_no,
                                    date.today(),
                                ),
                            )
                            issue_id = cursor.lastrowid

                            cursor.execute(
                                "UPDATE books SET quantity=quantity-1 WHERE id=%s",
                                (offline_book[0],),
                            )
                        db.commit()
                        st.success(
                            f"Book issued successfully. Issue ID: {issue_id} | "
                            f"Customer Reg. No.: {customer_reg_no}"
                        )
                        st.rerun()
                    except Exception:
                        db.rollback()
                        raise
                    finally:
                        db.close()
                except Exception as e:
                    st.error(f"Could not issue book: {e}")
    else:
        st.warning("No books are currently available for offline issue.")

    st.divider()

    # -----------------------------
    # Admin: return book
    # -----------------------------
    st.subheader("📥 Return Book")
    with st.form("return_form"):
        issue_id = st.number_input("Issue ID", min_value=1, value=1, step=1)
        return_clicked = st.form_submit_button("Return Book", type="primary")

    if return_clicked:
        try:
            result = fetch_all(
                "SELECT book_id FROM issue_books "
                "WHERE id=%s AND return_date IS NULL",
                (int(issue_id),),
            )

            if not result:
                st.error("Invalid or already returned Issue ID.")
            else:
                book_id = result[0][0]
                db = get_db()
                try:
                    with db.cursor() as cursor:
                        cursor.execute(
                            "UPDATE issue_books SET return_date=%s WHERE id=%s",
                            (date.today(), int(issue_id)),
                        )
                        cursor.execute(
                            "UPDATE books SET quantity = quantity + 1 WHERE id=%s",
                            (book_id,),
                        )
                    db.commit()
                    st.success("Book returned successfully.")
                    st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(f"Could not return book: {e}")
                finally:
                    db.close()
        except Exception as e:
            st.error(f"Database error: {e}")

    st.divider()

    # -----------------------------
    # Admin: all request history
    # -----------------------------
    st.subheader("📋 Request History")
    request_history = fetch_all("""
        SELECT
            r.id,
            r.username,
            r.student_name,
            r.reg_no,
            b.title,
            r.request_date,
            r.status,
            r.admin_note,
            r.issue_id
        FROM book_requests r
        JOIN books b ON r.book_id = b.id
        ORDER BY r.id DESC
    """)

    if request_history:
        st.dataframe(
            [
                {
                    "Request ID": r[0],
                    "Username": r[1],
                    "Student Name": r[2],
                    "Reg No.": r[3],
                    "Book": r[4],
                    "Request Date": r[5],
                    "Status": r[6],
                    "Admin Note": r[7] or "",
                    "Issue ID": r[8] or "",
                }
                for r in request_history
            ],
            hide_index=True,
            width="stretch",
        )

    st.divider()

    # -----------------------------
    # Admin: issue history
    # -----------------------------
    st.subheader("📚 Issue History")
    history = fetch_all("""
        SELECT
            i.id,
            b.title,
            i.student_name,
            i.reg_no,
            i.issue_date,
            i.return_date,
            i.issue_type
        FROM issue_books i
        JOIN books b ON i.book_id = b.id
        ORDER BY i.id DESC
    """)

    if history:
        st.dataframe(
            [
                {
                    "Issue ID": r[0],
                    "Book Title": r[1],
                    "Student Name": r[2],
                    "Reg No.": r[3],
                    "Issue Date": r[4],
                    "Return Date": r[5] or "Not Returned",
                    "Type": r[6],
                }
                for r in history
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No issue history available.")


# -----------------------------
# User: request books and view requests
# -----------------------------
else:
    st.subheader("👤 User Dashboard")
    st.info(
        "As a user, you can browse books and send requests. A book is issued only after an admin accepts your request."
    )
    st.write(f"**Your Library Registration No.:** `{st.session_state.reg_no}`")

    available_books = [row for row in books if int(row[3]) > 0]

    if available_books:
        issue_options = {
            f"{row[1]} — {row[2]} (Available: {row[3]})": row
            for row in available_books
        }

        with st.form("request_book_form"):
            selected_label = st.selectbox("Select a book", list(issue_options.keys()))
            selected_book = issue_options[selected_label]
            student_name = st.text_input("Student Name")
            st.text_input(
                "Registration No.",
                value=st.session_state.reg_no,
                disabled=True,
                help="Automatically assigned to your account.",
            )
            request_clicked = st.form_submit_button("📨 Send Book Request", type="primary")

        if request_clicked:
            if not student_name.strip():
                st.error("Enter your student name.")
            else:
                try:
                    duplicate = fetch_all(
                        "SELECT id FROM book_requests "
                        "WHERE username=%s AND book_id=%s AND status='Pending'",
                        (username, selected_book[0]),
                    )

                    if duplicate:
                        st.warning("You already have a pending request for this book.")
                    else:
                        execute_query(
                            "INSERT INTO book_requests "
                            "(book_id, username, student_name, reg_no, request_date, status) "
                            "VALUES (%s, %s, %s, %s, %s, 'Pending')",
                            (
                                selected_book[0],
                                username,
                                student_name.strip(),
                                st.session_state.reg_no,
                                date.today(),
                            ),
                        )
                        st.success("Book request sent to the admin.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Could not send request: {e}")
    else:
        st.warning("No books are currently available for request.")

    st.divider()
    st.subheader("📨 My Book Requests")

    my_requests = fetch_all("""
        SELECT
            r.id,
            b.title,
            b.author,
            r.student_name,
            r.reg_no,
            r.request_date,
            r.status,
            r.admin_note,
            r.issue_id
        FROM book_requests r
        JOIN books b ON r.book_id = b.id
        WHERE r.username=%s
        ORDER BY r.id DESC
    """, (username,))

    if my_requests:
        st.dataframe(
            [
                {
                    "Request ID": r[0],
                    "Book": r[1],
                    "Author": r[2],
                    "Student Name": r[3],
                    "Reg No.": r[4],
                    "Request Date": r[5],
                    "Status": r[6],
                    "Admin Note": r[7] or "",
                    "Issue ID": r[8] or "",
                }
                for r in my_requests
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("You have not sent any book requests yet.")

    st.caption("Your request remains Pending until an admin accepts or rejects it. On acceptance, the book is automatically issued to you.")
