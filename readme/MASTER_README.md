# Database User Management System - Complete Manual

## Overview
A comprehensive system for managing Linux system users and MariaDB databases through both Ansible playbooks and a web interface.

---

## System Components

| Component | File | Purpose | Documentation |
|-----------|------|---------|---------------|
| **Web Interface** | `app.py` | Web-based user management | [APP_README.md](./APP_README.md) |
| **Server Setup** | `setup_db_server.yml` | Initial MariaDB installation & config | [SETUP_DB_SERVER_README.md](./SETUP_DB_SERVER_README.md) |
| **User Creation** | `create_users.yml` | Create users on existing server | [CREATE_USERS_README.md](./CREATE_USERS_README.md) |
| **User Removal** | `wipe_users.yml` | Remove all users and databases | [WIPE_USERS_README.md](./WIPE_USERS_README.md) |

---

## Quick Start Guide

### First-Time Setup (New Server)

**Step 1**: Prepare inventory file
```bash
nano inventory_test.ini
```
Add your server IP:
```ini
[myhosts]
10.16.1.71
```

**Step 2**: Prepare users file
```bash
nano users_to_create.json
```
Add users:
```json
{
  "student1": "password123",
  "student2": "password456"
}
```

**Step 3**: Configure server (installs MariaDB)
```bash
ansible-playbook -i inventory_test.ini setup_db_server.yml
```

**Step 4**: Create users
```bash
ansible-playbook -i inventory_test.ini create_users.yml
```

**Step 5**: (Optional) Start web interface
```bash
ssh <user>@<server-ip>
sudo python3 app.py
# Access: http://<server-ip>:5000
```

---

### Quick Setup (Server + Users in One Command)

```bash
ansible-playbook -i inventory_test.ini setup_db_server.yml -e add_users=true
```

This performs complete setup including user creation.

---

## Common Workflows

### Workflow 1: Add More Users (Server Already Set Up)

```bash
# Edit users_to_create.json to add new users
nano users_to_create.json

# Create the new users
ansible-playbook -i inventory_test.ini create_users.yml
```

**Or use web interface**:
1. Open http://<server-ip>:5000
2. Navigate to "Create Users"
3. Add users manually or upload JSON file

---

### Workflow 2: Reset All Users (Clean Slate)

```bash
# Remove all existing users
ansible-playbook -i inventory_test.ini wipe_users.yml

# Create new users
ansible-playbook -i inventory_test.ini create_users.yml -e users_json_path="./new_users.json"
```

---

### Workflow 3: Manage Users via Web Interface

```bash
# SSH into server
ssh <user>@<server-ip>

# Start web app
sudo python3 app.py

# Open browser
# Navigate to: http://<server-ip>:5000
```

**Available actions**:
- Create users (manual or file upload)
- Delete users
- Reset passwords
- Lock/unlock accounts
- Manage shared databases
- Grant/revoke database access
- Execute SQL queries
- View action logs
- Export user list to CSV

---

### Workflow 4: Set Up Shared Database

**Option A: Via Web Interface**
1. Open http://<server-ip>:5000
2. Go to "Shared Database Management"
3. Enter database name (e.g., "project_db")
4. Click "Create Database"
5. Select database from dropdown
6. Grant access to users as needed

**Option B: Via SSH**
```bash
ssh <user>@<server-ip>
sudo mysql -e "CREATE DATABASE project_db;"
sudo mysql -e "GRANT ALL PRIVILEGES ON project_db.* TO 'student1'@'localhost';"
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         Control Machine (Your Laptop)           │
│                                                  │
│  • Ansible playbooks                            │
│  • inventory_test.ini                           │
│  • users_to_create.json                         │
└─────────────────┬───────────────────────────────┘
                  │ SSH
                  ▼
┌─────────────────────────────────────────────────┐
│         Target Server (Rocky Linux)              │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │         System Users (Linux)             │   │
│  │  • student1, student2, etc.              │   │
│  │  • Home directories: /home/student1/     │   │
│  │  • SSH access                            │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │         MariaDB Server                   │   │
│  │  • Databases: student1, student2, etc.   │   │
│  │  • Users: student1@localhost, etc.       │   │
│  │  • Shared databases: project_db, etc.    │   │
│  │  • Bind address: 127.0.0.1 (localhost)   │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      Web Management Interface (Flask)    │   │
│  │  • Port: 5000                            │   │
│  │  • app.py                                │   │
│  │  • Web UI for user management            │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                  ▲
                  │ HTTP
                  │
          Your Web Browser
```

---

## File Structure

```
user_creation_tool/
├── app.py                          # Web application
├── templates/
│   └── index.html                  # Web UI
├── setup_db_server.yml             # Server setup playbook
├── create_users.yml                # User creation playbook
├── wipe_users.yml                  # User removal playbook
├── inventory_test.ini              # Target server list
├── users_to_create.json            # User credentials
├── roles/
│   └── create_users/               # User creation role
│       ├── tasks/
│       │   └── main.yml
│       └── defaults/
│           └── main.yml
└── readme/
    ├── MASTER_README.md            # This file
    ├── APP_README.md               # Web app manual
    ├── SETUP_DB_SERVER_README.md   # Server setup manual
    ├── CREATE_USERS_README.md      # User creation manual
    └── WIPE_USERS_README.md        # User removal manual
```

---

## Decision Tree: Which Tool to Use?

```
┌───────────────────────────────────────┐
│  What do you need to do?              │
└───────────────┬───────────────────────┘
                │
    ┌───────────┴────────────┐
    │                        │
    ▼                        ▼
┌─────────┐            ┌──────────┐
│ New     │            │ Existing │
│ Server? │            │ Server?  │
└────┬────┘            └─────┬────┘
     │                       │
     ▼                       ▼
┌────────────────────┐  ┌────────────────────┐
│ Use:               │  │ What operation?    │
│ setup_db_server.yml│  └─────┬──────────────┘
└────────────────────┘        │
                        ┌─────┴──────┬──────────┬──────────┐
                        ▼            ▼          ▼          ▼
                   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
                   │ Add     │ │ Remove  │ │ Manage  │ │ Complex  │
                   │ Users?  │ │ Users?  │ │ Users?  │ │ Tasks?   │
                   └────┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘
                        │           │           │           │
                        ▼           ▼           ▼           ▼
                   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
                   │ Use:    │ │ Use:    │ │ Use:    │ │ Use:     │
                   │ create_ │ │ wipe_   │ │ app.py  │ │ app.py   │
                   │ users   │ │ users   │ │ (web)   │ │ (web)    │
                   │ .yml    │ │ .yml    │ └─────────┘ └──────────┘
                   └─────────┘ └─────────┘
```

---

## Security Features

### Network Security
- MariaDB bound to 127.0.0.1 (localhost only)
- Port 3306 not exposed externally
- SSH key-based authentication
- Firewall configured to block external DB access

### Database Security
- Root user: unix_socket authentication (no password needed when logged in as root)
- No remote root access
- Each user restricted to their own database
- Shared database access explicitly granted
- SQL injection protection in web interface

### User Security
- Password-only authentication (no plaintext storage in logs)
- Input validation (alphanumeric + underscore only)
- SSH user locking capability
- Action logging for audit trail

---

## Requirements

### Control Machine
- **OS**: Linux, macOS, or WSL on Windows
- **Ansible**: Version 2.9+
- **Python**: Version 3.6+
- **Expect**: For SSH key setup
- **SSH Client**: OpenSSH

Install on Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ansible expect python3 openssh-client
```

Install on RHEL/CentOS:
```bash
sudo yum install epel-release
sudo yum install ansible expect python3 openssh-clients
```

Install on macOS:
```bash
brew install ansible expect python3
```

---

### Target Server
- **OS**: Rocky Linux 8/9, RHEL 8/9, or CentOS 8/9
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 20GB+ available
- **Network**: SSH access (port 22)
- **Initial Access**: Password-based SSH (converted to key-based)

---

## Troubleshooting Guide

### Issue: Cannot connect to server

**Check 1**: Verify network connectivity
```bash
ping <server-ip>
```

**Check 2**: Verify SSH access
```bash
ssh <user>@<server-ip>
```

**Check 3**: Verify inventory file
```bash
cat inventory_test.ini
# Should contain correct IP/hostname
```

**Solution**: Update inventory file with correct server address.

---

### Issue: "expect not found"

**Solution**: Install expect on control machine
```bash
# Ubuntu/Debian
sudo apt-get install expect

# RHEL/CentOS
sudo yum install expect

# macOS
brew install expect
```

---

### Issue: MariaDB operations fail

**Check**: Is MariaDB running?
```bash
ssh <user>@<server-ip>
sudo systemctl status mariadb
```

**Solution**: Start MariaDB
```bash
sudo systemctl start mariadb
```

---

### Issue: Web interface not accessible

**Check 1**: Is app.py running?
```bash
ssh <user>@<server-ip>
ps aux | grep app.py
```

**Check 2**: Is port 5000 blocked?
```bash
sudo firewall-cmd --list-ports
```

**Solution**: Open port 5000
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

---

### Issue: Permission denied errors

**Check**: Are you running as root/sudo?
```bash
# For Ansible playbooks: Ansible handles sudo automatically
# For app.py:
sudo python3 app.py
```

---

### Issue: User already exists

**Solution Option 1**: Skip (playbook will warn but continue)

**Solution Option 2**: Remove existing user first
```bash
ansible-playbook -i inventory_test.ini wipe_users.yml
```

---

## Backup and Recovery

### Backup MariaDB Databases

**All databases**:
```bash
ssh <user>@<server-ip>
sudo mysqldump --all-databases > all_databases_backup.sql
```

**Single database**:
```bash
sudo mysqldump student1 > student1_backup.sql
```

**Download backup**:
```bash
scp <user>@<server-ip>:~/all_databases_backup.sql ./
```

---

### Restore MariaDB Databases

**All databases**:
```bash
scp ./all_databases_backup.sql <user>@<server-ip>:~/
ssh <user>@<server-ip>
sudo mysql < all_databases_backup.sql
```

**Single database**:
```bash
sudo mysql student1 < student1_backup.sql
```

---

### Backup Users JSON

```bash
cp users_to_create.json users_to_create.json.backup
```

Always keep a backup of user credentials for recovery.

---

## Performance Optimization

### For Large User Counts (100+ users)

**Option 1**: Use Ansible parallel execution
```bash
ansible-playbook -i inventory_test.ini create_users.yml -f 10
# -f 10 = 10 parallel tasks
```

**Option 2**: Use web interface file upload
- More efficient for bulk operations
- Built-in validation
- Progress tracking

---

## Monitoring and Logs

### Ansible Playbook Logs

Ansible outputs to terminal. Save logs:
```bash
ansible-playbook -i inventory_test.ini create_users.yml | tee ansible.log
```

---

### Web Application Logs

**Action logs**: Built into web interface
- Access via "Action Log" section
- Last 50 actions stored
- Location: `/var/lib/user_manager_actions.log`

**Server logs**:
```bash
ssh <user>@<server-ip>
sudo tail -f /var/log/messages
```

---

### MariaDB Logs

```bash
ssh <user>@<server-ip>
sudo tail -f /var/log/mariadb/mariadb.log
```

---

## Best Practices

1. **Always use version control** for configuration files
   ```bash
   git init
   git add inventory_test.ini users_to_create.json
   git commit -m "Initial configuration"
   ```

2. **Test with small user sets** before bulk operations
   ```json
   {
     "testuser1": "testpass1"
   }
   ```

3. **Use check mode** before destructive operations
   ```bash
   ansible-playbook -i inventory_test.ini wipe_users.yml --check
   ```

4. **Keep backups** of databases and configuration
   ```bash
   sudo mysqldump --all-databases > backup_$(date +%Y%m%d).sql
   ```

5. **Document changes** in action logs or external documentation

6. **Use strong passwords** for production environments

7. **Regularly update** the server and packages
   ```bash
   sudo dnf update -y
   ```

---

## Support and Documentation

- **Web App Manual**: [APP_README.md](./APP_README.md)
- **Server Setup Manual**: [SETUP_DB_SERVER_README.md](./SETUP_DB_SERVER_README.md)
- **User Creation Manual**: [CREATE_USERS_README.md](./CREATE_USERS_README.md)
- **User Removal Manual**: [WIPE_USERS_README.md](./WIPE_USERS_README.md)

---

## Summary of Commands

| Task | Command |
|------|---------|
| **Setup new server** | `ansible-playbook -i inventory_test.ini setup_db_server.yml` |
| **Setup + create users** | `ansible-playbook -i inventory_test.ini setup_db_server.yml -e add_users=true` |
| **Create users only** | `ansible-playbook -i inventory_test.ini create_users.yml` |
| **Remove all users** | `ansible-playbook -i inventory_test.ini wipe_users.yml` |
| **Start web interface** | `sudo python3 app.py` |
| **Check mode (dry run)** | `ansible-playbook <playbook> --check` |
| **Verbose output** | `ansible-playbook <playbook> -v` |
| **Backup database** | `sudo mysqldump --all-databases > backup.sql` |

---

## Version Information

- **Ansible**: 2.9+ required
- **Python**: 3.6+ required
- **Flask**: Latest version
- **MariaDB**: 10.3+ (installed by playbook)
- **Rocky Linux**: 8.x or 9.x

---

## License

This system is provided as-is for educational and administrative purposes.
