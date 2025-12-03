# Wipe Users (`wipe_users.yml`)

## How to run this file
- From the `user_creation_tool` directory:
  ```bash
  ansible-playbook -i inventory_test.ini wipe_users.yml
  ```
- To use a different JSON manifest for the cohort to remove:
  ```bash
  ansible-playbook -i inventory_test.ini wipe_users.yml \
    -e users_json_path=./spring_students.json
  ```

## What this file does
- Reads a JSON file (same format as `users_to_create.json`) to get a list of usernames.
- For each listed user (excluding core SSH users like `j` and `root`):
  - Drops their MariaDB database.
  - Drops their MariaDB account on `localhost`.
  - Deletes the Linux user and their home directory.
  - Removes any `/home/<user>/.my.cnf` file left behind.

