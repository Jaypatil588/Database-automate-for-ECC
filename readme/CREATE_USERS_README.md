# Create Users Playbook (create_users.yml)

## Overview
Ansible playbook to create system users and MariaDB databases on a pre-configured database server. This is a standalone playbook that assumes MariaDB is already installed and running.

## Purpose
Use this playbook when you need to create multiple users and databases on an existing database server without reconfiguring the entire server.

## Prerequisites

1. **Target Server Requirements**:
   - Rocky Linux / RHEL / CentOS (or similar)
   - MariaDB server installed and running
   - SSH access configured
   - sudo/root privileges

2. **Control Machine Requirements**:
   - Ansible installed
   - Python 3
   - `expect` package installed (for SSH key setup)
   - Network connectivity to target server

3. **Required Files**:
   - `inventory_test.ini` - Inventory file with target hosts
   - `users_to_create.json` - JSON file with user credentials
   - `roles/create_users/` - Role directory

## Configuration

### 1. Edit Variables (Lines 19-25)

```yaml
vars:
  initial_ssh_user: "j"              # SSH username for connecting
  initial_ssh_password: "root"        # SSH password for sudo
  initial_ssh_port: 22                # SSH port (default: 22)
  users_json_path: "./users_to_create.json"  # Path to users JSON file
```

**Important**: Update these values to match your server configuration.

---

### 2. Prepare Users JSON File

Create or edit `users_to_create.json`:

```json
{
  "student1": "password123",
  "student2": "password456",
  "student3": "password789"
}
```

**Format**: `{"username": "password", ...}`

**Custom path**: Use `-e users_json_path="./custom_users.json"` when running the playbook.

---

### 3. Update Inventory File

Edit `inventory_test.ini`:

```ini
[myhosts]
10.16.1.71
192.168.1.100
db-server.example.com
```

Add your target server IP addresses or hostnames.

---

## Usage

### Basic Usage

```bash
ansible-playbook -i inventory_test.ini create_users.yml
```

This will:
1. Connect to servers listed in inventory
2. Set up SSH key authentication
3. Read users from `users_to_create.json`
4. Create system users with home directories
5. Create MariaDB databases (one per user)
6. Create MariaDB users with access to their own database
7. Update SSH configuration

---

### Custom Users File

```bash
ansible-playbook -i inventory_test.ini create_users.yml -e users_json_path="./custom_users.json"
```

Use this to specify a different JSON file with user credentials.

---

### Verbose Output

```bash
ansible-playbook -i inventory_test.ini create_users.yml -v
```

Add `-v`, `-vv`, or `-vvv` for increasing levels of verbosity.

---

## What the Playbook Does

### Phase 1: SSH Key Setup (Lines 14-154)

1. **Generates SSH keys**: Creates unique SSH key pair for each target host
   - Key location: `~/.ssh/id_rsa_ansible_<hostname>`
   - Type: RSA 2048-bit

2. **Tests existing keys**: Checks if SSH key authentication already works

3. **Installs SSH keys**: Uses `expect` to authenticate with password and install public key

4. **Sets permissions**: Ensures proper permissions on SSH keys (700 for directory, 600 for private key, 644 for public key)

5. **Updates connection**: Switches from password to key-based authentication

---

### Phase 2: User Creation (Lines 156-189)

1. **Verifies MariaDB**: Checks that MariaDB service is running

2. **Tests connectivity**: Ensures MariaDB is accessible

3. **Runs create_users role**: Executes the role from `roles/create_users/`
   - Creates system users
   - Sets passwords
   - Creates MariaDB databases
   - Creates MariaDB users
   - Grants database privileges
   - Creates `.my.cnf` config files for auto-login

4. **Displays summary**: Shows completion message

---

## Output Example

```
PLAY [Setup SSH keys for hosts in inventory] ***********************************

TASK [Generate SSH key pair for host if it doesn't exist] *********************
changed: [10.16.1.71]

TASK [Add SSH key to authorized_keys on first login] ***************************
changed: [10.16.1.71]

PLAY [Create Users and Databases] **********************************************

TASK [Include create_users role] ***********************************************
included: roles/create_users/tasks/main.yml

TASK [Create system users] *****************************************************
changed: [10.16.1.71] => (item=student1)
changed: [10.16.1.71] => (item=student2)

TASK [Create MariaDB databases] ************************************************
changed: [10.16.1.71] => (item=student1)
changed: [10.16.1.71] => (item=student2)

PLAY RECAP *********************************************************************
10.16.1.71                 : ok=15   changed=8    unreachable=0    failed=0
```

---

## Files Created on Target Server

For each user (e.g., `student1`):

1. **System User**:
   - Username: `student1`
   - Home directory: `/home/student1`
   - Shell: `/bin/bash`

2. **MariaDB Database**: 
   - Database name: `student1`
   - Owner: `student1`@`localhost`

3. **MariaDB User**:
   - Username: `student1`@`localhost`
   - Privileges: ALL on `student1` database

4. **MySQL Config File**:
   - Location: `/home/student1/.my.cnf`
   - Contains: Auto-login credentials
   ```ini
   [client]
   user=student1
   password=<password>
   ```

---

## Troubleshooting

### Error: "SSH key already exists"
**Solution**: This is normal. The playbook will use the existing key.

---

### Error: "MariaDB not running"
**Solution**: Run `setup_db_server.yml` first to install and configure MariaDB:
```bash
ansible-playbook -i inventory_test.ini setup_db_server.yml
```

---

### Error: "expect not found"
**Solution**: Install expect on your control machine:
```bash
# Ubuntu/Debian
sudo apt-get install expect

# RHEL/CentOS
sudo yum install expect

# macOS
brew install expect
```

---

### Error: "User already exists"
**Solution**: The playbook will skip existing users. To recreate users, delete them first with `wipe_users.yml`.

---

### Error: "Connection refused"
**Solution**: 
1. Verify target server is reachable: `ping <target-ip>`
2. Verify SSH port is correct (default: 22)
3. Check firewall allows SSH connections

---

### Error: "Permission denied"
**Solution**: Ensure the `initial_ssh_user` has sudo privileges on the target server.

---

## Security Notes

1. **SSH Keys**: Unique key generated per host for security
2. **Passwords**: Not exposed in playbook output (use `-e` for sensitive vars)
3. **Sudo Required**: User must have sudo privileges on target server
4. **Key Storage**: Private keys stored in `~/.ssh/` with 600 permissions

---

## Related Files

- `setup_db_server.yml` - Complete server setup (includes MariaDB installation)
- `wipe_users.yml` - Remove all users and databases
- `roles/create_users/` - Role containing user creation logic
- `inventory_test.ini` - Inventory file with target hosts
- `users_to_create.json` - User credentials JSON file

---

## Integration with Web App

After running this playbook, users can be managed through the web interface (`app.py`) at:
```
http://<your-server-ip>:5000
```

The web app provides additional features like password resets, user locking, and shared database management.
