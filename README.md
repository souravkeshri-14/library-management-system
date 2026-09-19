# 📚 Library Management System

> A full-stack library management application built with **Python, Streamlit, MySQL, and PyMySQL**, designed to manage books, users, requests, issue/return operations, and library history from a single web interface.

## 🚀 Live Demo

**Live App:** [https://movie-recommender-system-4t4wa7jnhhcaedeuz9e8ed.streamlit.app/](https://library-management-system-kyzeblsisibbmvmbnrccuc.streamlit.app/)

👉 **Try the Library Management System**

---

<p align="left">
  <a href="https://github.com/souravkeshri-14/library-management-system">
    <img src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github" alt="GitHub Repository">
  </a>
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/Aiven%20MySQL-Cloud-FF5A3D?style=for-the-badge" alt="Aiven MySQL">
</p>

---

## ✨ Overview

The **Library Management System** is a web-based application that digitizes common library operations such as book management, user registration, online book requests, book issuing, returns, availability tracking, and history management.

The application supports two major workflows:

- 👤 **Online Registered Users** — users can create accounts, search books, request books, and track their request/issue history.
- 🛡️ **Administrators** — admins can manage books, approve or reject requests, issue and return books, and handle offline customers.

The project uses **MySQL** as the database layer and can be deployed online using **Streamlit Community Cloud**.

---

## 🚀 Key Features

### 👤 User Features

| Feature | Description |
|---|---|
| 📝 User Registration | Create a new library account |
| 🔐 User Login | Secure login for registered users |
| 🆔 Library Registration Number | Automatically generated registration number |
| 📚 Browse Books | View books available in the library |
| 🔎 Search Books | Search by title or author |
| 📩 Book Requests | Request books directly from the application |
| 📌 Request Status | Track pending, accepted, and rejected requests |
| 🕘 History | View personal request and issue history |

### 🛡️ Admin Features

| Feature | Description |
|---|---|
| 🔐 Admin Login | Dedicated administrator access |
| ➕ Add Books | Add new books to the database |
| ✏️ Update Books | Modify book details and quantity |
| 🗑️ Delete Books | Remove books from the system |
| 📥 Request Management | View and manage pending requests |
| ✅ Approve Requests | Accept and issue requested books |
| ❌ Reject Requests | Reject requests with optional admin notes |
| ↩️ Return Books | Process returned books |
| 📊 Issue History | Track issued and returned books |
| 🧑‍💼 Offline Customers | Issue books to customers without online accounts |

---

## 🧑‍💼 Offline Customer Support

The system also supports **offline book issuing**, allowing administrators to lend books to customers who do not have an online account.

Admins can manage:

- Customer name
- Registration number
- Automatically generated offline registration number
- Book issue details
- Return details
- Book quantity and availability

This makes the system useful for both **digital and traditional library workflows**.

---

## 🧠 How the System Works

### 🌐 Online User Flow

```text
┌──────────────┐
│  User Login  │
└──────┬───────┘
       ↓
┌──────────────┐
│ Browse Books │
└──────┬───────┘
       ↓
┌──────────────┐
│ Request Book │
└──────┬───────┘
       ↓
┌────────────────────┐
│ Admin Reviews      │
│ Request             │
└──────────┬─────────┘
           ↓
     ┌────────────┐
     │  Accepted  │
     └─────┬──────┘
           ↓
     ┌────────────┐
     │ Book Issued│
     └─────┬──────┘
           ↓
     ┌────────────┐
     │   Return   │
     └────────────┘
```

### 🧾 Offline Customer Flow

```text
┌────────────┐
│    Admin   │
└─────┬──────┘
      ↓
┌────────────────────┐
│ Enter Customer Info│
└──────────┬─────────┘
           ↓
┌────────────────────┐
│ Select Available   │
│ Book                │
└──────────┬─────────┘
           ↓
      ┌──────────┐
      │  Issue   │
      │  Book    │
      └────┬─────┘
           ↓
      ┌──────────┐
      │  Return  │
      │  Book    │
      └──────────┘
```

---

## 📊 Book Availability

Book quantity is updated automatically whenever a book is issued or returned.

```text
Quantity > 0  →  ✅ Available
Quantity = 0  →  ❌ Not Available
```

This helps prevent issuing unavailable books and keeps inventory information up to date.

---

## 🗄️ Database Design

The application uses **MySQL** for persistent data storage.

### Main Tables

```text
users
books
book_requests
issue_books
```

### 👥 `users`

Stores information such as:

- User credentials
- User role
- Library registration number

### 📚 `books`

Stores:

- Book ID
- Book title
- Author
- Quantity

### 📩 `book_requests`

Stores online book request details and request status.

Possible request states:

```text
Pending
Accepted
Rejected
```

### 📖 `issue_books`

Stores:

- Issued book information
- Registration number
- Issue details
- Return details
- Offline customer information where applicable

---

## 🔐 Authentication & Security

The application provides separate access for:

```text
👤 User
🛡️ Admin
```

New user passwords are stored using **SHA-256 hashing**.

> ⚠️ For production-grade applications, password hashing with a dedicated password-hashing algorithm such as **bcrypt, Argon2, or PBKDF2** is generally preferred over plain SHA-256.

Database credentials should never be hard-coded or committed to GitHub.

---

## 🛠️ Tech Stack

### Backend & Application

- 🐍 **Python**
- 🎈 **Streamlit**
- 🔌 **PyMySQL**

### Database

- 🐬 **MySQL**
- ☁️ **Aiven MySQL**

### Data Handling

- 🐼 **Pandas**

### Deployment

- ☁️ **Streamlit Community Cloud**

---

## ☁️ Deployment Architecture

```text
                ┌─────────────────────┐
                │        User         │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Streamlit Community │
                │        Cloud        │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Python + Streamlit  │
                │    Application      │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │     Aiven MySQL     │
                │   Cloud Database    │
                └─────────────────────┘
```

---

## 📁 Project Structure

```text
library-management-system/
│
├── app.py
├── requirements.txt
├── setup.sql
├── README.md
├── .gitignore
│
└── .streamlit/
    └── secrets.toml
```

### 📌 File Description

| File / Folder | Purpose |
|---|---|
| `app.py` | Main Streamlit application |
| `requirements.txt` | Required Python packages |
| `setup.sql` | SQL/database setup script |
| `.streamlit/secrets.toml` | Local database credentials and secrets |
| `.gitignore` | Prevents sensitive/unnecessary files from being committed |
| `README.md` | Project documentation |

---

## ⚙️ Run Locally

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/souravkeshri-14/library-management-system.git
```

### 2️⃣ Enter the Project Directory

```bash
cd library-management-system
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure MySQL

Create the following file:

```text
.streamlit/secrets.toml
```

Add your MySQL credentials:

```toml
[mysql]
host = "YOUR_DATABASE_HOST"
port = 3306
user = "YOUR_DATABASE_USER"
password = "YOUR_DATABASE_PASSWORD"
database = "YOUR_DATABASE_NAME"
```

> 🔒 Never upload `secrets.toml` to a public GitHub repository.

### 5️⃣ Run the Application

```bash
streamlit run app.py
```

The application will start locally and open in your browser.

---

## 🔒 Environment & Secret Management

For local development, store database credentials in:

```text
.streamlit/secrets.toml
```

For Streamlit Community Cloud, add the same values through the app's **Secrets** settings.

Recommended `.gitignore` entry:

```gitignore
.streamlit/secrets.toml
```

---

## 🌐 Project Links

### 📦 GitHub Repository

https://github.com/souravkeshri-14/library-management-system

---

## 🔮 Future Improvements

Planned enhancements include:

- 📅 Due dates and automatic overdue tracking
- 🔔 Email or in-app notifications
- 💳 Fine/penalty management
- 📊 Admin dashboard with charts and analytics
- 🔎 Advanced filtering and sorting
- 📚 Book categories and genres
- 🖼️ Book cover images
- 👤 Improved user profile management
- 📱 More responsive mobile UI
- 🔐 Stronger production-grade password hashing
- 📈 Detailed library usage reports

---

## 🎯 Project Highlights

This project demonstrates practical experience in:

```text
Python
   +
Streamlit
   +
MySQL
   +
CRUD Operations
   +
Authentication
   +
Database Integration
   +
Cloud Deployment
```

It combines **frontend UI, backend logic, database operations, authentication, inventory management, and cloud deployment** into one complete application.

---

## 👨‍💻 Author

### **Sourav Keshri**

🎓 B.Tech | Electronics & Communication Engineering

🔗 **GitHub:**  
https://github.com/souravkeshri-14

🔗 **Project Repository:**  
https://github.com/souravkeshri-14/library-management-system

---

## ⭐ Support the Project

If you found this project useful or interesting, consider giving the repository a **⭐ Star** on GitHub.

<p align="center">
  Made with ❤️ using Python & Streamlit
</p>
