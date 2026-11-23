# Banking Management and Fraud Detection System

## 📌 Project Overview

The **Banking Management and Fraud Detection System** is a Python-based desktop application designed to simulate essential banking operations while integrating fraud detection and transaction monitoring functionalities.

The project combines database management, financial operations, user authentication, and a graphical user interface to demonstrate how software engineering principles can be applied to banking systems.

## 🚀 Features

- **User Authentication:** User registration and login functionality.
- **Account Management:** Management of customer banking accounts.
- **Transaction Management:** Processing and tracking banking transactions.
- **Fraud Detection:** Monitoring financial transactions for potentially suspicious activities.
- **Credit Card Management:** Management of credit card information and related operations.
- **Customer Management:** Organization and management of customer records.
- **Dashboard:** Graphical interface for accessing banking functionalities.
- **Notifications:** Application notifications related to banking operations.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| SQL Server | Database management |
| PyODBC | Python–SQL Server connectivity |
| CustomTkinter / Tkinter | Desktop graphical user interface |
| Argon2 | Password hashing |
| Git & GitHub | Version control and project hosting |

## 📂 Project Structure

```text
Banking-Management-and-Fraud-Detection-System/
│
├── app.py
├── core.py
├── auth.py
├── accounts.py
├── bank.py
├── customers.py
├── transactions.py
├── credit_cards.py
├── fraud.py
├── dashboard.py
├── notifications.py
├── ui.py
│
├── 01_schema.sql
├── 02_constraints_indexes.sql
├── 03_seed_data.sql
├── 04_views.sql
├── 05_procedures.sql
├── 06_verify.sql
│
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sevdezeynp/Banking-Management-and-Fraud-Detection-System.git
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the Database

Install Microsoft SQL Server and execute the SQL scripts in numerical order:

1. `01_schema.sql`
2. `02_constraints_indexes.sql`
3. `03_seed_data.sql`
4. `04_views.sql`
5. `05_procedures.sql`
6. `06_verify.sql`

### 4. Configure Environment Variables

Set the required database connection settings and administrator credentials.

In particular, configure `DB_PASSWORD` and `ADMIN_PASSWORD` securely through environment variables.

**Never commit real passwords or credentials to the repository.**

### 5. Run the Application

```bash
python app.py
```

## 🔐 Security

The project incorporates security-related concepts such as:

- Password hashing using Argon2.
- User authentication.
- Database access management.
- Transaction monitoring.
- Fraud detection functionality.

**Disclaimer:** This project is intended for educational and demonstration purposes. It is not designed for real-world financial transactions or production banking environments.

## 👩‍💻 Development

This project was developed as a collaborative software engineering project, combining Python application development, relational database management, and banking-related functionality.

## 📄 License

No license has been specified for this repository.
