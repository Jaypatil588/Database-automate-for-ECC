# Database Server Bootstrap (`setup_db_server.yml`)

## Purpose
- Hardens and configures a Rocky/RHEL-based VM as a teaching MariaDB server.
- Handles SSH key distribution, package installs, MariaDB hardening, firewall updates, and (optionally) batch student provisioning via the `create_users` role.

## Prerequisites
- Control node with Ansible 2.13+, ability to run Expect scripts, and access to the `inventory_test.ini` inventory.
- Target VM reachable over SSH with password access for `initial_ssh_user`.
- Sudo privileges for that user so Ansible can escalate.
- Optional: `users_to_create.json` present when `add_users=true` is used.

## Files/Dependencies
- `inventory_test.ini` – defines `myhosts` with one or more VM IPs.
- `roles/create_users` – invoked when `add_users` is true.
- `users_to_create.json` – consumed by the role for student data.

## Key Variables
| Variable | Default | Description |
| --- | --- | --- |
| `initial_ssh_user` | `j` | Account used for the first (password-based) login. |
| `initial_ssh_password` | `root` | Password for `initial_ssh_user`. |
| `initial_ssh_port` | `22` | SSH port for bootstrap. |
| `db_root_password` | `TheBetaSantaStore05!` | Temporary MariaDB root password before switching back to `unix_socket`. |
| `base_ssh_users` | `["root", "j"]` | Accounts that must be preserved when wiping/creating users. |
| `users_json_path` | `./users_to_create.json` | JSON manifest for optional user creation. |
| `add_users` | `false` | When `true`, runs `create_users` role after DB setup. |

Override any variable with `-e VAR=value` or via an inventory/group vars file.

## Major Steps
1. **SSH key bootstrap** – identical flow to `create_users.yml`, ensuring the controller can use key-based auth for all subsequent tasks.
2. **System prep**
   - Refreshes `dnf` metadata.
   - Installs `mariadb-server`, client tools, and Python deps (`python3-PyMySQL`).
3. **MariaDB configuration**
   - Starts/enables the service, waits for port `3306`.
   - Validates `/etc/my.cnf.d/server.cnf`; repairs if missing/garbled and enforces `bind-address = 127.0.0.1`.
   - Sets a temporary root password and verifies both password and `unix_socket` authentication paths.
   - Ensures root logins are limited to localhost and the port listens only on loopback.
4. **Security extras**
   - Backs up `/etc/ssh/sshd_config`, runs a syntax check, and restores on failure.
   - If `firewalld` is active, ensures SSH is open and 3306 is closed externally.
5. **Verification**
   - Runs a sample `SELECT` query as root to confirm DB health.
6. **Optional user provisioning**
   - When `add_users=true`, includes the `create_users` role with the shared `users_json_path`.

## Usage Examples
- **Base server prep only**:
  ```
  ansible-playbook -i inventory_test.ini setup_db_server.yml
  ```
- **Prep + student creation in one run**:
  ```
  ansible-playbook -i inventory_test.ini setup_db_server.yml \
    -e add_users=true \
    -e users_json_path=./cohort_fall.json
  ```
- **Custom credentials/ports**:
  ```
  ansible-playbook -i inventory_test.ini setup_db_server.yml \
    -e initial_ssh_user=admin \
    -e initial_ssh_password='Sup3rSecret' \
    -e initial_ssh_port=2222
  ```

## Expected File/Directory Structure
```
user_creation_tool/
├── inventory_test.ini
├── setup_db_server.yml
├── users_to_create.json
└── roles/
    └── create_users/
        ├── defaults/main.yml
        └── tasks/main.yml
```

## Validation & Troubleshooting
- **MariaDB won’t start**: rerun with `-vvv` to inspect the `systemd` output; check `/var/log/mariadb/mariadb.log`.
- **Firewall commands fail**: ensure `firewalld` is installed or ignore errors (playbook already marks them non-fatal).
- **`add_users` skipped**: confirm flag is a boolean (`-e add_users=true`) and JSON file is readable by the controller.

