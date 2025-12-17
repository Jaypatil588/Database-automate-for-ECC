# Wipe Users Playbook (wipe_users.yml)

## Overview
Ansible playbook to completely remove all student users, their databases, and associated files from the database server. This is a **destructive operation** that cleans the server for reuse.

## Purpose
Use this playbook when you need to:
- Remove all student users from the server
- Clean up all databases before a new semester/class
- Reset the server to a clean state
- Delete test users after testing

## ⚠️ WARNING
This playbook performs **IRREVERSIBLE DELETIONS**:
- Deletes system users
- Removes home directories and all files
- Drops MariaDB databases
- Drops MariaDB users

**SSH users are preserved** (root, j, or other users specified in the playbook).

---

## Prerequisites

1. **Target Server**:
   - Rocky Linux / RHEL / CentOS
   - MariaDB installed and running
   - SSH access configured
   - SSH key authentication set up (from previous playbook runs)

2. **Control Machine**:
   - Ansible installed
   - SSH keys for target server
   - `users_to_create.json` file available

3. **Required Files**:
   - `inventory_test.ini` - Inventory file
   - `users_to_create.json` - File with users to remove

---

## Configuration

### 1. Edit Variables (Lines 9-10)

```yaml
vars:
  ssh_user: "j"                # SSH username for connection
  ssh_password: "root"         # SSH password for sudo
```

**Update these** to match your server's SSH credentials.

---

### 2. Specify Users File (Line 47)

```yaml
vars:
  users_json_path: "./users_to_create.json"
```

**Path to users file**: The playbook reads the same JSON file used to create users.

**Override at runtime**:
```bash
ansible-playbook -i inventory_test.ini wipe_users.yml -e users_json_path="./custom_users.json"
```

---

### 3. Update Inventory File

Edit `inventory_test.ini`:

```ini
[myhosts]
10.16.1.71
```

---

## Usage

### Basic Usage

```bash
ansible-playbook -i inventory_test.ini wipe_users.yml
```

This will:
1. Connect to target servers via SSH key
2. Read `users_to_create.json`
3. Remove all users listed in the file
4. Preserve SSH users (root, j)

---

### Custom Users File

```bash
ansible-playbook -i inventory_test.ini wipe_users.yml -e users_json_path="./test_users.json"
```

Use a different JSON file to specify which users to remove.

---

### Dry Run (Check Mode)

```bash
ansible-playbook -i inventory_test.ini wipe_users.yml --check
```

**Check mode** shows what **would** be deleted without actually deleting anything.

**Note**: Some tasks may show "changed" in check mode even though nothing is actually modified.

---

### Verbose Output

```bash
ansible-playbook -i inventory_test.ini wipe_users.yml -v
```

Add `-v`, `-vv`, or `-vvv` for more detailed output.

---

## What the Playbook Does

### Phase 1: Configure SSH Connection (Lines 4-41)

**Actions**:
1. Determines SSH key path from previous setup
   - Key location: `~/.ssh/id_rsa_ansible_<hostname>`
2. Configures Ansible connection to use SSH keys
3. Sets up sudo authentication
4. Adds host to Ansible inventory with proper connection parameters

**Purpose**: Establishes secure connection using existing SSH keys.

---

### Phase 2: Read User Data (Lines 50-54)

**Actions**:
1. Reads `users_to_create.json` file
2. Parses JSON into dictionary
3. Stores user list in `student_users` variable

**Example JSON**:
```json
{
  "student1": "password123",
  "student2": "password456",
  "alice": "securepass",
  "bob": "testpass"
}
```

**Users read**: student1, student2, alice, bob

---

### Phase 3: Remove MariaDB Databases (Lines 56-63)

**Actions**:
- Drops MariaDB database for each user
- Command: `DROP DATABASE IF EXISTS <username>;`
- Skips SSH users (j, root)

**Example**:
```sql
DROP DATABASE IF EXISTS student1;
DROP DATABASE IF EXISTS student2;
```

**What is deleted**:
- All tables in the database
- All data in those tables
- Database itself

**Preserved**:
- Databases not in the JSON file
- System databases (mysql, information_schema, etc.)

---

### Phase 4: Remove MariaDB Users (Lines 65-72)

**Actions**:
- Drops MariaDB user accounts
- Command: `DROP USER IF EXISTS '<username>'@'localhost';`
- Flushes privileges
- Skips SSH users (j, root)

**Example**:
```sql
DROP USER IF EXISTS 'student1'@'localhost';
DROP USER IF EXISTS 'student2'@'localhost';
FLUSH PRIVILEGES;
```

**What is deleted**:
- User account
- All privileges
- Authentication credentials

---

### Phase 5: Remove System Users (Lines 74-82)

**Actions**:
- Removes Linux system user accounts
- Removes home directories
- Forces removal even if user has running processes
- Skips SSH users (j, root)

**Command equivalent**:
```bash
userdel -r -f student1
userdel -r -f student2
```

**What is deleted**:
- User account from `/etc/passwd`
- User group
- Home directory (`/home/<username>/`)
- All files in home directory
- Mail spool
- Cron jobs

**Preserved**:
- SSH users (root, j)
- System users (mysql, nobody, etc.)

---

### Phase 6: Remove MySQL Config Files (Lines 84-90)

**Actions**:
- Removes `.my.cnf` files from home directories
- Path: `/home/<username>/.my.cnf`
- Skips SSH users

**Purpose**: Cleans up auto-login configuration files created during user creation.

**Note**: This step is redundant since home directories are already deleted, but ensures cleanup even if home directory removal fails.

---

### Phase 7: Display Summary (Lines 92-101)

**Output Example**:
```
========================================
User Wipe Complete!
========================================
Removed 4 users
Removed 4 databases
Removed 4 MariaDB users
========================================
```

---

## Protected Users

The following users are **NEVER** deleted:

| Username | Reason |
|----------|--------|
| root | System administrator account |
| j | SSH access user (configurable) |

**Modify protected users**: Edit line 59, 68, 81, 89 to change protected user list:

```yaml
when: item.key not in ['j', 'root', 'admin']
```

Add any users you want to protect.

---

## Verification After Running

### Check System Users Were Removed

```bash
ssh <user>@<server-ip>
cat /etc/passwd | grep student
# Expected: No output

ls /home/
# Expected: Only SSH users remain (root, j)
```

---

### Check MariaDB Users Were Removed

```bash
ssh <user>@<server-ip>
sudo mysql -e "SELECT user, host FROM mysql.user WHERE user NOT IN ('root', 'mysql', 'mariadb.sys');"
# Expected: No student users
```

---

### Check Databases Were Removed

```bash
ssh <user>@<server-ip>
sudo mysql -e "SHOW DATABASES;"
# Expected: Only system databases (mysql, information_schema, performance_schema)
```

---

## Troubleshooting

### Error: "User <username> is currently used by process <PID>"
**Solution**: This is handled by the `force: yes` parameter. The playbook will kill processes and remove the user.

If issues persist:
```bash
ssh <user>@<server-ip>
sudo pkill -u student1
sudo userdel -r -f student1
```

---

### Error: "Database does not exist"
**Solution**: This is normal and expected if the database was already deleted. The playbook uses `IF EXISTS` to prevent errors.

---

### Error: "Cannot connect to MariaDB"
**Solution**: Verify MariaDB is running:
```bash
ssh <user>@<server-ip>
sudo systemctl status mariadb
sudo systemctl start mariadb
```

---

### Error: "SSH key not found"
**Solution**: SSH key from `setup_db_server.yml` is missing. Generate it:
```bash
ansible-playbook -i inventory_test.ini setup_db_server.yml
```

Or manually specify password authentication:
```bash
ansible-playbook -i inventory_test.ini wipe_users.yml -k
# -k prompts for SSH password
```

---

### Warning: "Home directory not found"
**Solution**: This is normal if the user was already partially deleted. The playbook handles this gracefully.

---

## Safety Features

1. **Protected Users**: SSH users (root, j) are never deleted
2. **IF EXISTS Clauses**: Prevents errors if resources don't exist
3. **Force Parameter**: Ensures complete removal even with running processes
4. **No-log Sensitive Data**: Password-related operations are hidden from logs

---

## What is NOT Deleted

| Item | Reason |
|------|--------|
| SSH users (root, j) | Needed for server access |
| System users (mysql, nobody) | System services |
| MariaDB installation | Server infrastructure |
| MariaDB configuration | Server settings |
| System databases | MariaDB system tables |
| SSH keys | Authentication credentials |
| Web application data | `/var/lib/user_manager_*.json` |

---

## Typical Use Cases

### 1. Clean Server Between Classes

```bash
# End of semester - remove all students
ansible-playbook -i inventory_test.ini wipe_users.yml

# Start of new semester - create new students
ansible-playbook -i inventory_test.ini create_users.yml -e users_json_path="./spring_2024.json"
```

---

### 2. Remove Test Users

```bash
# Create test users
ansible-playbook -i inventory_test.ini create_users.yml -e users_json_path="./test_users.json"

# Test functionality...

# Remove test users
ansible-playbook -i inventory_test.ini wipe_users.yml -e users_json_path="./test_users.json"
```

---

### 3. Reset Server After Corruption

```bash
# Remove all users
ansible-playbook -i inventory_test.ini wipe_users.yml

# Reconfigure server
ansible-playbook -i inventory_test.ini setup_db_server.yml

# Recreate users
ansible-playbook -i inventory_test.ini create_users.yml
```

---

## Best Practices

1. **Backup First**: Always backup important data before running:
   ```bash
   ssh <user>@<server-ip>
   sudo mysqldump --all-databases > backup.sql
   ```

2. **Use Check Mode**: Test with `--check` before actual deletion

3. **Document Users**: Keep a copy of `users_to_create.json` for records

4. **Verify Results**: Check that users were removed after running

5. **Schedule Carefully**: Run during maintenance windows when users are offline

---

## Recovery

If you accidentally delete users:

### 1. Restore from users_to_create.json

```bash
ansible-playbook -i inventory_test.ini create_users.yml
```

This recreates users with the same credentials.

**Note**: User data (files, database contents) is **NOT** restored.

---

### 2. Restore Database from Backup

```bash
ssh <user>@<server-ip>
sudo mysql < backup.sql
```

Restores databases if you have a backup.

---

## Related Playbooks

- **setup_db_server.yml** - Initial server setup
- **create_users.yml** - Create users and databases

---

## Summary

| Action | Command |
|--------|---------|
| **Wipe all users** | `ansible-playbook -i inventory_test.ini wipe_users.yml` |
| **Wipe specific users** | `ansible-playbook -i inventory_test.ini wipe_users.yml -e users_json_path="./file.json"` |
| **Check what would be deleted** | `ansible-playbook -i inventory_test.ini wipe_users.yml --check` |
| **Verbose output** | `ansible-playbook -i inventory_test.ini wipe_users.yml -v` |
| **Recreate users after wipe** | `ansible-playbook -i inventory_test.ini create_users.yml` |

---

## Exit Status

- **Exit 0**: All users removed successfully
- **Exit 2**: Some users failed to remove (check output for details)
- **Exit 1**: Playbook error (SSH failure, file not found, etc.)
