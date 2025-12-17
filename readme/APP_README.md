# User Management Web Application (app.py)

## Overview
A Flask-based web application for managing system users, MariaDB databases, and shared database access through an intuitive web interface.

## Prerequisites
- Python 3
- Flask
- Root/sudo privileges (required for system operations)
- MariaDB server installed and running

## Installation

1. Install dependencies:
```bash
pip3 install flask
```

2. Start the application:
```bash
sudo python3 app.py
```

3. Access the web interface:
```
http://<your-server-ip>:5000
```

## Functions and Usage

### 1. Create Users

#### **Manual Entry (Option 1)**
**Location**: Main page → "Create Users" card

**Steps**:
1. Enter username in the "Username" field
2. Enter password in the "Password" field
3. Click **"Add to List"** button
4. Repeat for multiple users
5. Click **"Execute User Creation"** to create all users in the list

**What it does**:
- Creates system user with home directory
- Creates MariaDB database named after the user
- Creates MariaDB user with full access to their database
- Updates SSH configuration to allow user login

**Backend Function**: `add_users()` → POST `/add_users`

---

#### **File Upload (Option 2)**
**Location**: Main page → "Create Users" card → "Upload JSON File"

**Steps**:
1. Prepare a JSON file with format: `{"username1": "password1", "username2": "password2"}`
2. Click **"Choose File"** and select your JSON file
3. Click **"Upload & Create Users"** button

**What it does**:
- Validates JSON file format and size (max 1MB)
- Creates all users from the file in batch
- Performs same operations as manual entry for each user

**Backend Function**: `upload_users_file()` → POST `/upload_users_file`

---

### 2. Current Users Management

#### **View Users**
**Location**: Main page → "Current Users" card → Table display

**What you see**:
- Username
- Password (masked as ****)
- Database size
- Status (Active/Locked)
- Action buttons

---

#### **Delete Single User**
**Location**: User table → "Delete" button for each user

**Steps**:
1. Click **"Delete"** button next to the user
2. Confirm deletion in the popup dialog

**What it does**:
- Removes system user and home directory
- Drops MariaDB database
- Drops MariaDB user
- Updates SSH configuration

**Backend Function**: `delete_user()` → POST `/delete_user`

---

#### **Delete Multiple Users**
**Location**: User table → Select checkboxes → "Delete Selected" button

**Steps**:
1. Check the checkbox next to each user you want to delete
2. (Optional) Check "Select All" box to select all users
3. Click **"Delete Selected"** button
4. Confirm deletion

**What it does**:
- Batch deletion of selected users
- Same operations as single delete for each user

**Backend Function**: `delete_multiple()` → POST `/delete_multiple`

---

#### **Reset Password**
**Location**: User table → "Reset" button for each user

**Steps**:
1. Click **"Reset"** button next to the user
2. Enter new password in the popup prompt
3. Click OK

**What it does**:
- Changes system user password
- Changes MariaDB user password

**Backend Function**: `reset_password()` → POST `/reset_password`

---

#### **Lock/Unlock User**
**Location**: User table → "Lock" or "Unlock" button for each user

**Steps**:
1. Click **"Lock"** to disable user login (or **"Unlock"** to enable)

**What it does**:
- Locks: Prevents user from logging in via SSH (MariaDB access remains)
- Unlocks: Restores SSH login ability

**Backend Function**: `toggle_lock()` → POST `/toggle_lock`

---

#### **Export to CSV**
**Location**: "Current Users" card → "Export CSV" button

**Steps**:
1. Click **"Export CSV"** button
2. File `users.csv` will be downloaded

**What it does**:
- Exports user data (username, database size, locked status)
- Does NOT export passwords (security)

**Backend Function**: `export_csv()` → GET `/export_csv`

---

### 3. Shared Database Management

#### **Create Shared Database**
**Location**: "Shared Database Management" card → "Create New Shared DB" section

**Steps**:
1. Enter database name in the text field
2. Click **"Create Database"** button

**What it does**:
- Creates a new MariaDB database
- No user has access by default (grant access separately)
- Tracks database in shared database list

**Backend Function**: `create_shared_db()` → POST `/create_shared_db`

---

#### **Grant User Access to Shared DB**
**Location**: "Shared Database Management" card → Select database → "Manage Access" section

**Steps**:
1. Select a shared database from the dropdown menu
2. Find the user in the access list
3. Click **"Grant"** button next to the user

**What it does**:
- Grants comprehensive privileges (SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, etc.)
- User can create/modify tables and objects within the database
- Cannot drop the database itself

**Backend Function**: `grant_access()` → POST `/grant_access`

---

#### **Revoke User Access from Shared DB**
**Location**: Same location as Grant Access

**Steps**:
1. Select the shared database
2. Click **"Revoke"** button next to the user

**What it does**:
- Removes all privileges from the user for that database
- User can no longer access the database

**Backend Function**: `revoke_access()` → POST `/revoke_access`

---

#### **Execute SQL Query on Shared DB**
**Location**: "Shared Database Management" card → "Execute Query" section

**Steps**:
1. Select a shared database from the dropdown
2. Enter SQL query in the textarea (e.g., `SELECT * FROM table_name;`)
3. Click **"Execute Query"** button

**What it does**:
- Executes SQL query on the selected database
- Displays results in formatted output
- Only allows safe operations: SELECT, INSERT, UPDATE, DELETE, SHOW, DESCRIBE
- Blocks dangerous operations: DROP DATABASE, ALTER, CREATE, TRUNCATE, GRANT, REVOKE

**Backend Function**: `query_shared_db()` → POST `/query_shared_db`

---

### 4. Configuration

#### **Set MariaDB Bind-Address**
**Location**: "Configuration" card

**Steps**:
1. Enter IP address in the field (e.g., `127.0.0.1` for localhost only, or `10.16.1.71` for specific IP)
2. Leave empty to allow all connections (`0.0.0.0`)
3. Click **"Set IP Range"** button
4. Confirm the restart prompt

**What it does**:
- Modifies MariaDB configuration file (`/etc/my.cnf.d/server.cnf` or similar)
- Sets `bind-address` parameter
- Restarts MariaDB service
- Controls which network interfaces MariaDB listens on

**Backend Function**: `set_ip_range()` → POST `/set_ip_range`

---

### 5. Action Log

#### **View Activity Logs**
**Location**: "Action Log" card (collapsible)

**Steps**:
1. Click the "Action Log" header to expand

**What you see**:
- Timestamp of action
- Action type (create_user, delete_user, reset_password, etc.)
- Target user/database
- Result (success/failed)

**What it does**:
- Displays last 50 actions performed through the web interface
- Stored persistently in `/var/lib/user_manager_actions.log`

**Backend Function**: `get_logs()` → GET `/get_logs`

---

## Security Features

1. **Root Privileges Required**: Most operations require root/sudo access
2. **Input Validation**: 
   - Usernames: Only alphanumeric and underscore characters
   - IP addresses: Validated format
   - SQL queries: Filtered to prevent dangerous operations
3. **Password Handling**: Passwords never stored in plain text or exposed in logs
4. **File Upload Security**: 
   - Max 1MB file size
   - UTF-8 encoding required
   - JSON format validation

## Data Storage

- **User data**: `/var/lib/user_manager_data.json`
- **Action logs**: `/var/lib/user_manager_actions.log`

## Troubleshooting

**Issue**: Cannot access web interface
- **Solution**: Ensure running as root: `sudo python3 app.py`

**Issue**: MariaDB operations fail
- **Solution**: Verify MariaDB is running: `systemctl status mariadb`

**Issue**: "Root privileges required" error
- **Solution**: Start application with sudo: `sudo python3 app.py`

**Issue**: File upload fails
- **Solution**: Check JSON format is correct: `{"user1": "pass1", "user2": "pass2"}`
