# Wipe Users Playbook (`wipe_users.yml`)

## Purpose
- Safely removes all student-facing artifacts from the VM:
  - MariaDB databases and accounts
  - Linux user accounts + home directories
  - Residual `.my.cnf` files
- Preserves core SSH accounts defined in the manifest (`j`, `root` by default).

## Prerequisites
- Controller can already connect over SSH key auth (keys created by other playbooks).
- `inventory_test.ini` defines the hosts grouped under `myhosts`.
- `users_to_create.json` (or alternate JSON file) matches the cohort that should be removed.

## Input Files & Structure
- `users_to_create.json`: same format used for creation. Sample:
  ```json
  {
    "student1": "ignored_during_wipe",
    "student2": "ignored_during_wipe"
  }
  ```
  Password values are ignored; only the keys (usernames) matter.

## Workflow
1. **SSH context setup**
   - Local play calculates the previously generated key path (`~/.ssh/id_rsa_ansible_<host>`).
   - Calls `add_host` so the second play connects using that key plus sudo escalation.
2. **Destructive actions on remote hosts**
   - Reads the JSON once (delegated to localhost) to get the list of student usernames.
   - For each user (excluding `j` and `root`):
     - Drops their MariaDB database.
     - Drops their MariaDB account (`user@localhost`) and flushes privileges.
     - Removes the Linux account and home directory.
     - Deletes `/home/<user>/.my.cnf` if it remains.
   - Prints a summary showing how many entries were processed.

## Key Variables
| Variable | Default | Description |
| --- | --- | --- |
| `ssh_user` | `j` | SSH username for key-based access. |
| `ssh_password` | `root` | Sudo password for privilege escalation (used by `become`). |
| `users_json_path` | `./users_to_create.json` | JSON manifest used to determine which accounts to delete. |

Override `users_json_path` to point at a different cohort file if needed:
```
ansible-playbook -i inventory_test.ini wipe_users.yml \
  -e users_json_path=./spring_students.json
```

## Safety Notes
- The manifest drives deletions. Double-check its contents before running.
- Non-existent users/databases are skipped gracefully (`failed_when: false`).
- Use `--check` first if you want to preview changes that Ansible would make.

## Verification
- Run `mysql -e "SHOW DATABASES LIKE 'student1';"` to ensure DBs are gone.
- `getent passwd student1` should return nothing.
- `.my.cnf` files should no longer be present under the removed home directories.

