# Create Users (`create_users.yml`)

## How to run this file
-# Usage:
#   ansible-playbook -i inventory_test.ini create_users.yml
#   ansible-playbook -i inventory_test.ini create_users.yml -e users_json_path="./custom_users.json"

- To use a different SSH user/password or JSON file:
  ```bash
  ansible-playbook -i inventory_test.ini create_users.yml \
    -e initial_ssh_user=admin \
    -e initial_ssh_password='Sup3rSecret' \
    -e users_json_path=./my_students.json
  ```

## What this file does
- Reads a JSON file like:
  ```json
  { "student1": "Password1", "student2": "Password2" }
  ```
- For each entry:
  - Creates a Linux user with that name.
  - Creates a MariaDB database with the same name.
  - Creates a local MariaDB user with full access to that database.
- Uses SSH password once to install an SSH key, then connects with key-based auth for subsequent tasks.

