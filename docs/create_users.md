# Create Users Playbook (`create_users.yml`)

## Purpose
- Provisions per-student Linux accounts, MariaDB databases, and local-only DB users based on a JSON manifest.
- Can be run standalone after the VM is configured or chained from `setup_db_server.yml`.

## Prerequisites
- Control node with Ansible 2.13+ and `python3`, `expect`, and `openssh` utilities.
- Managed hosts listed under the `myhosts` group in `inventory_test.ini`.
- SSH password access to the initial user (default `j` / `root`) so key-based auth can be bootstrapped.
- Local JSON file describing users and passwords (default `./users_to_create.json`).

## Input Files
- `inventory_test.ini` – INI inventory with reachable hosts under `[myhosts]`.
- `users_to_create.json` – flat JSON dict mapping `username: password`. Example:
  ```json
  {
    "student1": "SecurePass123",
    "student2": "AnotherPass!"
  }
  ```

## How It Works
1. **SSH key bootstrap** (local connection block)
   - Generates per-host SSH key pairs under `~/.ssh/id_rsa_ansible_<host>`.
   - Uses `expect` to log in with the provided password and append the public key to `authorized_keys`.
   - Adds adhoc host variables (`add_host`) so the second play reuses the freshly created key.
2. **User/database provisioning** (remote play)
   - Ensures MariaDB is up and reachable.
   - Includes the `create_users` role, which:
     - Reads `users_to_create.json`.
     - Creates Linux users + home dirs, MariaDB databases, and DB logins.
     - Drops `.my.cnf` files per student for passwordless CLI access.

## Key Variables
| Variable | Location | Default | Description |
| --- | --- | --- | --- |
| `initial_ssh_user` | play vars | `j` | Remote user for first login. |
| `initial_ssh_password` | play vars | `root` | Password used only until SSH keys exist. |
| `initial_ssh_port` | play vars | `22` | TCP port for SSH. |
| `users_json_path` | play vars / role variable | `./users_to_create.json` | Path (local to controller) for the user manifest. |

Override vars at runtime via `-e`:
```
ansible-playbook -i inventory_test.ini create_users.yml \
  -e initial_ssh_user=admin \
  -e initial_ssh_password='Sup3rSecret' \
  -e users_json_path=./cohort_fall.json
```

## Typical Workflow
1. Confirm `inventory_test.ini` targets are reachable with password SSH.
2. Populate or generate `users_to_create.json`.
3. Run the playbook:
   ```
   ansible-playbook -i inventory_test.ini create_users.yml
   ```
4. Inspect the debug summary at the end or log into MariaDB to verify.

## Troubleshooting Tips
- **Key bootstrap fails**: ensure password SSH is enabled temporarily for `initial_ssh_user`.
- **MariaDB connection errors**: verify `systemctl status mariadb` on the host and rerun once fixed.
- **User manifests**: invalid JSON or missing file raises `lookup('file', users_json_path)` errors; validate with `jq . users_to_create.json`.

