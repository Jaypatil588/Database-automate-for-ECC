# User Management Web App (`app.py`)

## How to run this file
- On the database VM, as root (or with sudo):
  ```bash
  cd /opt/db-ecc/user_creation_tool   # or wherever this folder lives
  pip install flask
  sudo FLASK_ENV=production python3 app.py
  ```
- Then open in a browser:
  ```text
  http://<vm-ip>:5000/
  ```

## What this file does
- Serves the dashboard defined in `templates/index.html`, which has these main sections:
  - **Create Users**: manually add username/password pairs or upload a JSON file; when you click the buttons, it creates Linux users and matching MariaDB databases.
  - **Current Users**: shows each user, DB size, and lock status; lets you reset passwords, lock/unlock accounts, delete single users, delete selected users, and export the list to CSV.
  - **Shared Database Management**: create shared databases, grant/revoke access for existing users, and run limited SQL queries against those shared DBs.
  - **Configuration**: set the MariaDB bind-address/IP range the server listens on.
  - **Action Log**: expandable log that shows recent actions (creates, deletes, grants, etc.).
- All actions are executed locally on the VM (useradd, mysql, systemctl, etc.) and require the app to be running with root privileges. 

