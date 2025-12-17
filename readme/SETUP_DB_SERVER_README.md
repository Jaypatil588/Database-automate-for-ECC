# Setup Database Server Playbook (setup_db_server.yml)

## Overview
Complete Ansible playbook for configuring a Rocky Linux VM as a secure database server. This playbook installs MariaDB, secures it, and optionally creates users and databases.

## Purpose
Use this playbook for **initial server setup** when you have a fresh Rocky Linux installation and need to:
- Install and configure MariaDB
- Secure the database server
- Set up SSH key authentication
- Optionally create users and databases

## Prerequisites

1. **Target Server Requirements**:
   - Fresh Rocky Linux / RHEL / CentOS installation
   - Network connectivity
   - SSH access (password authentication initially)
   - Minimum 2GB RAM recommended
   - 20GB+ disk space

2. **Control Machine Requirements**:
   - Ansible installed (version 2.9+)
   - Python 3
   - `expect` package installed
   - Network access to target server

3. **Required Files**:
   - `inventory_test.ini` - Inventory file
   - `users_to_create.json` - (Optional) User credentials file
   - `roles/create_users/` - (Optional) Role directory

---

## Configuration

### 1. Edit Variables (Lines 10-18)

```yaml
vars:
  initial_ssh_user: "j"                          # SSH username
  initial_ssh_password: "root"                   # SSH password for sudo
  initial_ssh_port: 22                           # SSH port
  db_root_password: "TheBetaSantaStore05!"       # MariaDB root password
  base_ssh_users: ["root", "j"]                  # Users allowed SSH access
  users_json_path: "./users_to_create.json"      # Path to users JSON file
```

**Critical**: 
- Update `initial_ssh_user` and `initial_ssh_password` to match your server
- Change `db_root_password` to a strong, unique password
- Add any existing SSH users to `base_ssh_users` to preserve their access

---

### 2. Update Inventory File

Edit `inventory_test.ini`:

```ini
[myhosts]
10.16.1.71
```

Add your target server(s). Multiple servers can be configured simultaneously.

---

## Usage

### Basic Server Setup (Without Users)

```bash
ansible-playbook -i inventory_test.ini setup_db_server.yml
```

This will:
1. Set up SSH keys
2. Install MariaDB server and client
3. Install Python 3 and MySQL libraries
4. Configure MariaDB security
5. Set bind-address to localhost (127.0.0.1)
6. **NOT** create users

**Use this when**: You want to set up the server infrastructure first, then add users later.

---

### Complete Setup (With Users)

```bash
ansible-playbook -i inventory_test.ini setup_db_server.yml -e add_users=true
```

This performs basic setup **PLUS** creates users from `users_to_create.json`.

**Use this when**: You want to set up the server and create users in one go.

---

### Custom Configuration

```bash
ansible-playbook -i inventory_test.ini setup_db_server.yml \
  -e add_users=true \
  -e users_json_path="./production_users.json" \
  -e db_root_password="MySecurePassword123!"
```

Override default variables on the command line.

---

### Verbose Output

```bash
ansible-playbook -i inventory_test.ini setup_db_server.yml -v
```

Add `-v`, `-vv`, or `-vvv` for debugging.

---

## What the Playbook Does

### Phase 1: SSH Key Setup (Lines 5-150)

1. **Generates SSH keys**: Creates unique SSH key pair per host
   - Location: `~/.ssh/id_rsa_ansible_<hostname>`
   - Type: RSA 2048-bit

2. **Tests connectivity**: Checks if key-based auth already works

3. **Installs public key**: Uses `expect` to handle password authentication and install SSH key

4. **Sets permissions**: Ensures proper SSH key permissions

5. **Updates connection**: Switches Ansible to use SSH key authentication

---

### Phase 2: Database Server Configuration (Lines 152-386)

#### Step 1: Package Management (Lines 162-178)

**Actions**:
- Updates DNF package cache
- Installs `mariadb-server` and `mariadb`
- Installs Python 3, pip, and PyMySQL

**Why**: These packages are required for MariaDB operation and Ansible database modules.

---

#### Step 2: Start MariaDB Service (Lines 180-190)

**Actions**:
- Starts MariaDB service
- Enables MariaDB to start on boot
- Waits for port 3306 to be ready

**Verification**:
```bash
systemctl status mariadb
ss -tlnp | grep 3306
```

---

#### Step 3: Configure MariaDB Server Config (Lines 192-240)

**Actions**:
- Detects and validates `/etc/my.cnf.d/server.cnf`
- Creates/fixes `[mysqld]` section
- Sets `bind-address = 127.0.0.1` (localhost only)
- Removes malformed configuration lines
- Restarts MariaDB if config changed

**Security**: Binding to 127.0.0.1 prevents external database access.

**Config file location**:
```
/etc/my.cnf.d/server.cnf
```

**Example content**:
```ini
[mysqld]
bind-address = 127.0.0.1
```

---

#### Step 4: Secure MariaDB Installation (Lines 242-279)

**Actions**:
1. Sets root password using `ALTER USER` command
2. Verifies password authentication works
3. Enables `unix_socket` authentication for root user
4. Removes root login from non-localhost
5. Tests root can access MariaDB without password (unix socket)

**Security Features**:
- Root can only login from localhost
- Root uses unix_socket authentication (no password needed when logged in as root user)
- Remote root access completely disabled

**Verification**:
```bash
# As root user on server
mysql -e "SELECT USER();"
# Should connect without password
```

---

#### Step 5: Network Security (Lines 282-299)

**Actions**:
- Verifies bind-address in config
- Checks MariaDB is listening on 127.0.0.1 only
- Restarts if needed

**Verification**:
```bash
ss -tlnp | grep 3306
# Should show: 127.0.0.1:3306 (NOT 0.0.0.0:3306)
```

---

#### Step 6: SSH Configuration (Lines 304-322)

**Actions**:
- Backs up SSH config
- Verifies SSH config syntax
- Restores backup if syntax check fails
- Does NOT modify AllowUsers (handled by user creation role)

**Safety**: Backup prevents SSH lockout from config errors.

---

#### Step 7: Firewall Configuration (Lines 324-345)

**Actions**:
- Checks if firewalld is running
- Ensures SSH port is allowed
- Removes MariaDB port (3306) from external access

**Security**: MariaDB is not accessible from outside the server.

---

#### Step 8: Final Verification (Lines 347-351)

**Actions**:
- Tests MariaDB root access
- Displays status message

---

#### Step 9: Optional User Creation (Lines 354-359)

**Actions** (only if `-e add_users=true`):
- Includes `create_users` role
- Creates users from JSON file
- Sets up databases and permissions

---

### Phase 3: Display Summary (Lines 361-376)

**Output**:
```
========================================
Database Server Setup Complete!
========================================
Host: 10.16.1.71
MariaDB Status: OK
========================================
Next steps:
1. SSH into VM: ssh <user>@10.16.1.71
2. To create users and databases, run:
   ansible-playbook -i inventory_test.ini create_users.yml
```

---

## Security Configuration Summary

| Feature | Configuration | Purpose |
|---------|--------------|---------|
| MariaDB bind-address | 127.0.0.1 | Only localhost can connect to MariaDB |
| Root authentication | unix_socket | Root user uses OS authentication (no password) |
| Root remote access | DISABLED | Root cannot login from network |
| Firewall | Port 3306 blocked | MariaDB not accessible externally |
| SSH | Key-based auth | Secure SSH access |

---

## Files Modified on Target Server

1. **MariaDB Configuration**:
   - `/etc/my.cnf.d/server.cnf` - MariaDB settings
   - Backup: `/etc/my.cnf.d/server.cnf.bak`

2. **SSH Configuration**:
   - `/etc/ssh/sshd_config` - SSH daemon settings
   - Backup: `/etc/ssh/sshd_config.backup.ansible`

3. **SSH Keys**:
   - `/home/<user>/.ssh/authorized_keys` - SSH public keys

---

## Troubleshooting

### Error: "Package mariadb-server not found"
**Solution**: Update repository cache:
```bash
ansible -i inventory_test.ini myhosts -m shell -a "dnf makecache" --become
```

---

### Error: "MariaDB won't start"
**Solution**: Check MariaDB logs:
```bash
ansible -i inventory_test.ini myhosts -m shell -a "journalctl -u mariadb -n 50" --become
```

---

### Error: "bind-address not set correctly"
**Solution**: Manually verify config file:
```bash
ssh <user>@<server-ip>
sudo grep bind-address /etc/my.cnf.d/server.cnf
# Should show: bind-address = 127.0.0.1
```

If incorrect, re-run playbook:
```bash
ansible-playbook -i inventory_test.ini setup_db_server.yml
```

---

### Error: "Root password authentication failed"
**Solution**: The playbook uses unix_socket authentication. Login as root OS user:
```bash
ssh <user>@<server-ip>
sudo su -
mysql
```

---

### Error: "Connection timeout"
**Solutions**:
1. Verify server is reachable: `ping <server-ip>`
2. Check SSH port: `ssh -p 22 <user>@<server-ip>`
3. Verify firewall allows SSH
4. Check `initial_ssh_port` variable matches actual SSH port

---

### Error: "Permission denied (publickey)"
**Solution**: SSH key setup may have failed. Re-run playbook to retry key installation.

---

### Warning: "expect not found"
**Solution**: Install expect on control machine:
```bash
# Ubuntu/Debian
sudo apt-get install expect

# RHEL/CentOS  
sudo yum install expect

# macOS
brew install expect
```

---

## Post-Installation Steps

### 1. Verify MariaDB Security

```bash
ssh <user>@<server-ip>

# Test localhost binding
sudo ss -tlnp | grep 3306
# Expected: 127.0.0.1:3306 LISTEN

# Test root access
sudo mysql -e "SELECT USER(), CURRENT_USER();"
# Expected: Connects successfully

# Test MariaDB users
sudo mysql -e "SELECT user, host FROM mysql.user;"
```

---

### 2. Create Users (if not done during setup)

```bash
ansible-playbook -i inventory_test.ini create_users.yml
```

---

### 3. Start Web Management Interface

```bash
ssh <user>@<server-ip>
sudo python3 app.py
# Access at: http://<server-ip>:5000
```

---

## Related Playbooks

- **create_users.yml** - Create users on existing server
- **wipe_users.yml** - Remove all users and databases

---

## When to Use This Playbook

**Use setup_db_server.yml when**:
- Setting up a NEW server from scratch
- Need to install MariaDB
- Want to configure security settings
- Initial server deployment

**Use create_users.yml instead when**:
- Server is already set up
- MariaDB already installed and running
- Just need to add/manage users

---

## Idempotency

This playbook is **idempotent** - safe to run multiple times:
- Won't reinstall packages if already present
- Won't reset root password if already set
- Won't overwrite SSH keys if they exist
- Will fix misconfigurations if detected

**Safe to re-run** if something fails partway through.
