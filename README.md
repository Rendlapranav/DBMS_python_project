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
