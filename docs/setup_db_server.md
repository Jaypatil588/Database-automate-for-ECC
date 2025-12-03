# Setup DB Server (`setup_db_server.yml`)

## How to run this file
- From the `user_creation_tool` directory, to just configure the DB server:
  ```bash
  ansible-playbook -i inventory_test.ini setup_db_server.yml
  ```
- To configure the server and create student users in one go:
  ```bash
  ansible-playbook -i inventory_test.ini setup_db_server.yml \
    -e add_users=true \
    -e users_json_path=./users_to_create.json
  ```

## What this file does
- Connects to the VM(s) in `inventory_test.ini` and:
  - Sets up SSH key-based access for Ansible.
  - Installs MariaDB server + client and required Python packages.
  - Secures MariaDB (root account, local-only bind address, firewall rules).
- Optionally calls the `create_users` role (when `add_users=true`) to create Linux users and matching MariaDB databases from `users_to_create.json`.

