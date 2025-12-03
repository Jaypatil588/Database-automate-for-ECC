# User Management Web App (`app.py`)

## Overview
Flask-based admin UI for managing classroom accounts directly on the database VM. It must run as `root` (or via `sudo`) because it:
- Creates/removes Linux users and MariaDB accounts
- Restarts `sshd` when the allowed user list changes
- Writes audit logs under `/var/lib`

## Features & Routes
- `/` – dashboard listing student users, database sizes, and lock status.
- `POST /add_users` – JSON payload to create multiple Linux + DB accounts.
- `POST /upload_users_file` – upload `{ "username": "password" }` JSON file (<=1 MB) for bulk creation.
- `POST /delete_user` & `/delete_multiple` – remove users, DBs, and privileges.
- `POST /reset_password` – reset Linux + MariaDB passwords coherently.
- `POST /toggle_lock` – lock/unlock a Linux account.
- `POST /create_shared_db` – create shared databases stored in `DATA_FILE`.
- `POST /grant_access` / `/revoke_access` – manage privileges for shared DBs.
- `POST /query_shared_db` – run limited SQL (SELECT/INSERT/UPDATE/DELETE/SHOW/DESCRIBE) inside a shared DB.
- `POST /set_ip_range` – change the MariaDB `bind-address`.
- `GET /get_shared_dbs`, `/get_logs`, `/export_csv` – supporting APIs.

## File Paths & Persistence
| Constant | Default | Purpose |
| --- | --- | --- |
| `DATA_FILE` | `/var/lib/user_manager_data.json` | Persists shared DB metadata. |
| `LOG_FILE` | `/var/lib/user_manager_actions.log` | Stores last 50 actions for audit. |

Ensure `/var/lib` is writable by the user running the app (root).

## Security Measures
- Input validation helpers (`is_safe_input`, `is_safe_ip`, `is_safe_sql_query`) to mitigate injection.
- `@root_required` decorator blocks requests unless the process is running as UID 0.
- Strict command whitelisting using system binaries (`useradd`, `mysql`, `usermod`, etc.).
- Uploaded JSON capped at 1 MB and validated before processing.

## Requirements
- Python 3.9+
- System packages: `mariadb-client`, `passwd`, `usermod`, `systemctl`, etc. (already present on the VM configured by Ansible).
- Python packages:
  ```
  pip install flask
  ```
  (No additional dependencies are imported.)

## Running the App
1. SSH into the database VM as root (or a sudoer).
2. Navigate to the project folder, e.g.:
   ```
   cd /opt/db-ecc/user_creation_tool
   ```
3. Install Flask if needed: `pip install flask`.
4. Launch:
   ```
   sudo FLASK_ENV=production python3 app.py
   ```
5. Access via browser: `http://<vm-ip>:5000/`.

## Usage Flow
1. Generate the JSON payload (manually or export from the UI).
2. Use the UI or `curl` against `/add_users` to provision accounts.
3. Export CSV snapshots via `/export_csv` to monitor DB sizes/locks.
4. When the course ends, either run `wipe_users.yml` or use bulk-delete endpoints.

## Troubleshooting
- **403 Root required**: ensure you run `app.py` with `sudo`.
- **MySQL errors**: verify `mysql` CLI runs locally; check `/var/log/mariadb/mariadb.log`.
- **SSHD restart failures**: review `journalctl -u sshd` and confirm `AllowUsers` line in `/etc/ssh/sshd_config` is correct.
- **File permission issues**: delete/recreate `/var/lib/user_manager_*` with root ownership.

