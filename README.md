# DBMS_python_project
"Python/Tkinter GUI for managing a company MySQL database with transaction support"
# Company DB - MySQL Management Console

A Python/Tkinter desktop application for managing a company MySQL database. Replaces the original command-line script with a structured GUI.

---

## Requirements

- Python 3.8+
- MySQL Server 5.7+
- `mysql-connector-python` package
- `tkinter` (bundled with Python on Windows/macOS; Linux users may need to install separately)

---

## Installation

**1. Install the Python dependency**

```bash
pip install mysql-connector-python
```

**2. Linux only: install Tkinter**

```bash
sudo apt-get install python3-tk
```

**3. Ensure your MySQL server is running** and the target database exists (default: `companydb`).

---

## Running

```bash
python company_db_gui.py
```

The connection screen will appear. Enter your credentials and click Connect.

---

## Features

### Employee Directory
Displays all employee records in a scrollable table: SSN, First/Middle/Last Name, Birth Date, Sex, Salary, and Department Number.

### Insert Employee
A form for inserting a new employee and a `works_on` assignment in a single transaction.

- If hours > 0, the transaction is **committed**
- If hours <= 0, the transaction is **rolled back**
- Any database error triggers an automatic rollback

Required fields: SSN, Project Number, Hours. Dates must be `YYYY-MM-DD`. Salary, Dept Number, and Hours must be numeric.

### Dependents Report
Lists all employees with dependents. Shows dependent name, relationship, sex, and birth date, grouped by employee.

### Disconnect
Closes the connection and returns to the connection screen.

---

## Database Schema

| Table | Primary Key | Description |
|---|---|---|
| `employee` | `ssn` | Core employee records |
| `department` | `dnumber` | Company departments |
| `dependent` | `essn, dependent_name` | Employee dependents |
| `works_on` | `essn, pno` | Project assignments |
| `project` | `pnumber` | Project records |
| `dept_locations` | `dnumber, dlocation` | Department locations |

### employee

| Column | Type | Nullable |
|---|---|---|
| `ssn` | char(9) | No (PK) |
| `fname` | varchar(30) | Yes |
| `minit` | char(1) | Yes |
| `lname` | varchar(30) | Yes |
| `bdate` | date | Yes |
| `address` | varchar(30) | Yes |
| `sex` | char(1) | Yes |
| `salary` | decimal(10,2) | Yes |
| `super_ssn` | char(9) | Yes |
| `dno` | smallint | Yes |

---

## Security Notes

- All queries use parameterized statements (no SQL injection risk)
- Passwords are masked on the connection screen
- Credentials are held in memory only for the session

---

## Known Limitations

- No support for editing or deleting existing records (read + insert only)
- Only one `works_on` entry can be added per employee insert
- No pagination on large result sets
Based on the technical specifications and setup instructions provided, here is the `README.md` file.
---

## Installation & Setup

### 1. Initialize the Schema
Import the database structure and sample data.

```sql
-- Create the database
CREATE DATABASE companydb;
```

From your terminal, import the provided SQL dump:
```bash
mysql -u root -p companydb < companydb.sql
```
### 2. Authentication Plugin Fix
If you encounter the error `Plugin 'auth_socket' is not supported` on Linux/Ubuntu, switch the root user to password authentication:

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
FLUSH PRIVILEGES;
```

---

## Database Logic
The application implements strict **Atomic** and **Consistent** operations:
* **Atomic Inserts:** Every new employee must be linked to a `works_on` project assignment in a single transaction.
* **Validation:** If `hours` are recorded as $\le 0$, the script executes `db.rollback()` to prevent partial data entry.

---

## Project Structure
```plaintext
├── main.py            # Entry point; contains Tkinter GUI and App logic
├── companydb.sql      # Database schema and sample data dump 
└── README.md          # Documentation
```

