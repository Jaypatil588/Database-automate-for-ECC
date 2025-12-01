#!/usr/bin/env python3
import subprocess
import os
import json
import pwd
import shutil
import re
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_file
from io import StringIO

app = Flask(__name__)

# Data storage
DATA_FILE = '/var/lib/user_manager_data.json'
LOG_FILE = '/var/lib/user_manager_actions.log'

# Security: Input validation
def is_safe_input(value):
    """Only allow alphanumeric and underscore characters"""
    if not value:
        return False
    return re.match(r'^[a-zA-Z0-9_]+$', value) is not None

def is_safe_ip(value):
    """Validate IP address or range"""
    if not value:
        return True  # Empty is allowed (means 0.0.0.0)
    # Basic IP validation: xxx.xxx.xxx.xxx or 0.0.0.0
    return re.match(r'^(\d{1,3}\.){3}\d{1,3}$', value) is not None

def is_safe_sql_query(query):
    """Basic SQL query validation - only allow SELECT, INSERT, UPDATE, DELETE, SHOW, DESCRIBE"""
    if not query:
        return False
    query_upper = query.strip().upper()
    allowed_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'SHOW', 'DESCRIBE', 'DESC']
    dangerous_keywords = ['DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
    
    # Check if query starts with allowed keyword
    starts_with_allowed = any(query_upper.startswith(kw) for kw in allowed_keywords)
    # Check if query contains dangerous keywords
    contains_dangerous = any(kw in query_upper for kw in dangerous_keywords)
    
    return starts_with_allowed and not contains_dangerous

# Security: Root required decorator
def root_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if os.geteuid() != 0:
            return jsonify({"status": "error", "message": "Root privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'shared_dbs': []}

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def log_action(action, username, result):
    """Persistent file-based logging"""
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        'username': username,
        'result': result
    }
    
    try:
        # Load existing logs
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        
        # Append new log
        logs.append(log_entry)
        
        # Keep only last 50 entries
        if len(logs) > 50:
            logs = logs[-50:]
        
        # Save back to file
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"[!] Logging error: {e}")

def get_logs():
    """Retrieve logs from file"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                return json.load(f)
        return []
    except:
        return []

def get_system_users():
    users = []
    min_uid = 1000
    for p in pwd.getpwall():
        if p.pw_name == 'root' or (p.pw_uid >= min_uid and p.pw_shell not in ['/sbin/nologin', '/bin/false']):
            users.append(p.pw_name)
    return sorted(users)

def update_ssh_config():
    print("[*] Updating SSH configuration...")
    sshd_config_path = '/etc/ssh/sshd_config'
    
    allowed_users = get_system_users()
    allow_users_line = "AllowUsers " + " ".join(allowed_users)

    try:
        with open(sshd_config_path, 'r') as f:
            lines = f.readlines()

        new_lines = []
        found = False
        for line in lines:
            if line.strip().startswith("AllowUsers"):
                new_lines.append(allow_users_line + '\n')
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append('\n' + allow_users_line + '\n')
            
        temp_path = sshd_config_path + ".tmp"
        with open(temp_path, 'w') as f:
            f.writelines(new_lines)
        
        shutil.move(temp_path, sshd_config_path)
        
        subprocess.run(['systemctl', 'restart', 'sshd'], check=True)
        print(f"[+] SSH config updated. Allowed users: {', '.join(allowed_users)}")
        return {"status": "success", "message": "SSH permissions updated."}

    except Exception as e:
        print(f"[!] Error updating SSH config: {e}")
        return {"status": "error", "message": f"Failed to update SSH config: {e}"}

def get_database_users():
    print("[*] Fetching database users...")
    try:
        sql_command = "SELECT user FROM mysql.user WHERE host = 'localhost' AND user NOT IN ('root', 'mysql', 'mariadb.sys');"
        result = subprocess.run(
            ['mysql', '-N', '-e', sql_command], check=True, capture_output=True, text=True
        )
        users = result.stdout.strip().split('\n')
        return sorted([user for user in users if user])
    except subprocess.CalledProcessError as e:
        print(f"[!] Error fetching database users: {e.stderr}")
        return []

def get_db_size(db_name):
    try:
        sql = f"SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) FROM information_schema.TABLES WHERE table_schema = '{db_name}';"
        result = subprocess.run(['mysql', '-N', '-e', sql], capture_output=True, text=True, check=True)
        size = result.stdout.strip()
        return f"{size} MB" if size and size != 'NULL' else "0 MB"
    except:
        return "0 MB"

def is_user_locked(username):
    try:
        result = subprocess.run(['passwd', '-S', username], capture_output=True, text=True)
        return 'L' in result.stdout.split()[1] if result.stdout else False
    except:
        return False

def get_user_details():
    sys_users = get_system_users()
    users_info = []
    for user in sys_users:
        if user != 'root':
            users_info.append({
                'username': user,
                'password': '****',  # Never expose passwords
                'db_size': get_db_size(user),
                'locked': is_user_locked(user)
            })
    return users_info

def create_system_user(username, password):
    # Security: Validate input
    if not is_safe_input(username):
        return {"status": "error", "message": "Invalid username format. Only alphanumeric and underscore allowed."}
    
    try:
        subprocess.run(['useradd', '-m', '-s', '/bin/bash', username], check=True, capture_output=True)
        command = f"echo '{username}:{password}' | chpasswd"
        subprocess.run(command, shell=True, check=True, capture_output=True)
        # Security: Never store passwords in plain text
        return {"status": "success", "message": f"SSH user '{username}' created."}
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode().strip() if e.stderr else str(e)
        if "already exists" in error_message:
            return {"status": "warning", "message": f"SSH user '{username}' already exists."}
        return {"status": "error", "message": "Failed to create SSH user"}

def create_database_user(username, password):
    # Security: Validate input
    if not is_safe_input(username):
        return {"status": "error", "message": "Invalid username format"}
    
    db_name = username
    sql_commands = f"""
    CREATE DATABASE IF NOT EXISTS `{db_name}`;
    CREATE USER IF NOT EXISTS '{username}'@'localhost' IDENTIFIED BY '{password}';
    GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{username}'@'localhost';
    FLUSH PRIVILEGES;
    """
    try:
        subprocess.run(['mysql', '-e', sql_commands], check=True, capture_output=True, text=True)
        return {"status": "success", "message": f"DB user '{username}' created and restricted to database '{db_name}'."}
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode().strip()
        log_action('create_db_user', username, f'failed: {error_message}')
        return {"status": "error", "message": f"Failed to create DB user: {error_message}"}

@app.route('/')
def index():
    user_details = get_user_details()
    return render_template('index.html', user_details=user_details)

@app.route('/add_users', methods=['POST'])
@root_required
def add_users():
    users_to_add = request.get_json()
    results = []
    for user in users_to_add:
        username = user.get('username')
        password = user.get('password')
        if username and password:
            results.append(create_system_user(username, password))
            results.append(create_database_user(username, password))
            log_action('create_user', username, 'success')
    
    ssh_update_result = update_ssh_config()
    results.append(ssh_update_result)
    
    return jsonify({"results": results, "user_details": get_user_details()})

@app.route('/upload_users_file', methods=['POST'])
@root_required
def upload_users_file():
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400
    
    # Security: Validate file size (max 1MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 1048576:  # 1MB
        return jsonify({"status": "error", "message": "File too large. Maximum size is 1MB"}), 400
    
    try:
        # Read file content
        content = file.read().decode('utf-8')
        
        # Parse JSON
        try:
            user_data = json.loads(content)
        except json.JSONDecodeError:
            return jsonify({"status": "error", "message": "Invalid JSON format. Expected: {\"username\": \"password\", ...}"}), 400
        
        # Validate that it's a dictionary
        if not isinstance(user_data, dict):
            return jsonify({"status": "error", "message": "Invalid JSON structure. Expected key-value pairs: {\"username\": \"password\", ...}"}), 400
        
        results = []
        valid_count = 0
        invalid_count = 0
        
        for username, password in user_data.items():
            # Security: Validate username
            if not is_safe_input(username):
                results.append({"status": "error", "message": f"Invalid username format: {username}"})
                invalid_count += 1
                continue
            
            if not password or not isinstance(password, str):
                results.append({"status": "error", "message": f"Invalid password for: {username}"})
                invalid_count += 1
                continue
            
            # Create user
            result_sys = create_system_user(username, password)
            results.append(result_sys)
            
            if result_sys.get('status') == 'success' or result_sys.get('status') == 'warning':
                result_db = create_database_user(username, password)
                results.append(result_db)
                log_action('create_user', username, 'success')
                valid_count += 1
            else:
                invalid_count += 1
        
        # Update SSH config
        ssh_update_result = update_ssh_config()
        results.append(ssh_update_result)
        
        summary = f"Created {valid_count} users successfully."
        if invalid_count > 0:
            summary += f" Skipped {invalid_count} invalid entries."
        
        return jsonify({
            "status": "success",
            "message": summary,
            "results": results,
            "user_details": get_user_details()
        })
        
    except UnicodeDecodeError:
        return jsonify({"status": "error", "message": "Invalid file encoding. Please use UTF-8"}), 400
    except Exception as e:
        log_action('upload_file', 'bulk', 'failed')
        return jsonify({"status": "error", "message": "File processing failed"}), 500

@app.route('/delete_user', methods=['POST'])
@root_required
def delete_user():
    username = request.json.get('username')
    
    # Security: Validate input
    if not is_safe_input(username):
        return jsonify({"status": "error", "message": "Invalid username format"}), 400
    
    try:
        subprocess.run(['userdel', '-r', username], check=True, capture_output=True)
        sql = f"DROP DATABASE IF EXISTS `{username}`; DROP USER IF EXISTS '{username}'@'localhost'; FLUSH PRIVILEGES;"
        subprocess.run(['mysql', '-e', sql], check=True, capture_output=True)
        update_ssh_config()
        log_action('delete_user', username, 'success')
        return jsonify({"status": "success", "message": f"User {username} deleted", "user_details": get_user_details()})
    except Exception as e:
        log_action('delete_user', username, 'failed')
        return jsonify({"status": "error", "message": "Operation failed"}), 500

@app.route('/delete_multiple', methods=['POST'])
@root_required
def delete_multiple():
    usernames = request.json.get('usernames', [])
    results = []
    
    for username in usernames:
        # Security: Validate input
        if not is_safe_input(username):
            results.append({"username": username, "status": "error", "message": "Invalid format"})
            continue
            
        try:
            subprocess.run(['userdel', '-r', username], check=True, capture_output=True)
            sql = f"DROP DATABASE IF EXISTS `{username}`; DROP USER IF EXISTS '{username}'@'localhost'; FLUSH PRIVILEGES;"
            subprocess.run(['mysql', '-e', sql], check=True, capture_output=True)
            log_action('delete_user', username, 'success')
            results.append({"username": username, "status": "success"})
        except Exception as e:
            log_action('delete_user', username, 'failed')
            results.append({"username": username, "status": "error", "message": "Operation failed"})
    
    update_ssh_config()
    return jsonify({"results": results, "user_details": get_user_details()})

@app.route('/reset_password', methods=['POST'])
@root_required
def reset_password():
    username = request.json.get('username')
    new_password = request.json.get('password')
    
    # Security: Validate input
    if not is_safe_input(username):
        return jsonify({"status": "error", "message": "Invalid username format"}), 400
    
    try:
        command = f"echo '{username}:{new_password}' | chpasswd"
        subprocess.run(command, shell=True, check=True, capture_output=True)
        sql = f"SET PASSWORD FOR '{username}'@'localhost' = PASSWORD('{new_password}');"
        subprocess.run(['mysql', '-e', sql], check=True, capture_output=True)
        # Security: Never store passwords in plain text
        log_action('reset_password', username, 'success')
        return jsonify({"status": "success", "message": "Password updated"})
    except Exception as e:
        log_action('reset_password', username, 'failed')
        return jsonify({"status": "error", "message": "Operation failed"}), 500

@app.route('/toggle_lock', methods=['POST'])
@root_required
def toggle_lock():
    username = request.json.get('username')
    action = request.json.get('action')
    
    # Security: Validate input
    if not is_safe_input(username):
        return jsonify({"status": "error", "message": "Invalid username format"}), 400
    
    if action not in ['lock', 'unlock']:
        return jsonify({"status": "error", "message": "Invalid action"}), 400
    
    try:
        if action == 'lock':
            subprocess.run(['usermod', '-L', username], check=True, capture_output=True)
        else:
            subprocess.run(['usermod', '-U', username], check=True, capture_output=True)
        log_action(f'{action}_user', username, 'success')
        return jsonify({"status": "success", "user_details": get_user_details()})
    except Exception as e:
        return jsonify({"status": "error", "message": "Operation failed"}), 500

@app.route('/create_shared_db', methods=['POST'])
@root_required
def create_shared_db():
    db_name = request.json.get('db_name')
    
    # Security: Validate input
    if not is_safe_input(db_name):
        return jsonify({"status": "error", "message": "Invalid database name format"}), 400
    
    try:
        sql = f"CREATE DATABASE IF NOT EXISTS `{db_name}`;"
        subprocess.run(['mysql', '-e', sql], check=True, capture_output=True)
        data = load_data()
        if db_name not in data['shared_dbs']:
            data['shared_dbs'].append(db_name)
            save_data(data)
        log_action('create_shared_db', db_name, 'success')
        return jsonify({"status": "success", "message": f"Database {db_name} created", "shared_dbs": data['shared_dbs']})
    except Exception as e:
        return jsonify({"status": "error", "message": "Operation failed"}), 500

@app.route('/grant_access', methods=['POST'])
@root_required
def grant_access():
    db_name = request.json.get('db_name')
    username = request.json.get('username')
    
    # Security: Validate input
    if not is_safe_input(db_name) or not is_safe_input(username):
        return jsonify({"status": "error", "message": "Invalid input format"}), 400
    
    try:
        # Grant specific privileges for working *inside* the database
        sql = f"GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES, CREATE TEMPORARY TABLES, LOCK TABLES, EXECUTE, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, TRIGGER ON `{db_name}`.* TO '{username}'@'localhost'; FLUSH PRIVILEGES;"
        subprocess.run(['mysql', '-e', sql], check=True, capture_output=True)
        log_action('grant_access', f'{username} to {db_name}', 'success')
        return jsonify({"status": "success", "message": f"Table/object management access granted to {username} on {db_name}"})
    except Exception as e:
        log_action('grant_access', f'{username} to {db_name}', f'failed: {e}')
        return jsonify({"status": "error", "message": "Operation failed"}), 500

@app.route('/revoke_access', methods=['POST'])
@root_required
def revoke_access():
    db_name = request.json.get('db_name')
    username = request.json.get('username')
    
    # Security: Validate input
    if not is_safe_input(db_name) or not is_safe_input(username):
        return jsonify({"status": "error", "message": "Invalid input format"}), 400
    
    try:
        sql = f"REVOKE ALL PRIVILEGES ON `{db_name}`.* FROM '{username}'@'localhost'; FLUSH PRIVILEGES;"
        subprocess.run(['mysql', '-e', sql], check=True, capture_output=True)
        log_action('revoke_access', f'{username} from {db_name}', 'success')
        return jsonify({"status": "success", "message": f"Access revoked from {username}"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Operation failed"}), 500

@app.route('/query_shared_db', methods=['POST'])
@root_required
def query_shared_db():
    db_name = request.json.get('db_name')
    query = request.json.get('query')
    
    # Security: Validate database name
    if not is_safe_input(db_name):
        return jsonify({"status": "error", "message": "Invalid database name"}), 400
    
    # Security: Validate SQL query - only allow safe operations
    if not is_safe_sql_query(query):
        return jsonify({"status": "error", "message": "Query not allowed. Only SELECT, INSERT, UPDATE, DELETE, SHOW, DESCRIBE are permitted"}), 400
    
    try:
        result = subprocess.run(['mysql', '-t', db_name, '-e', query], capture_output=True, text=True, check=True)
        return jsonify({"status": "success", "result": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": "Query execution failed"}), 500

@app.route('/get_shared_dbs', methods=['GET'])
def get_shared_dbs():
    data = load_data()
    return jsonify({"shared_dbs": data.get('shared_dbs', [])})

@app.route('/get_logs', methods=['GET'])
def get_logs_route():
    return jsonify({"logs": get_logs()})

@app.route('/export_csv', methods=['GET'])
def export_csv():
    user_details = get_user_details()
    output = StringIO()
    # Security: Never export passwords
    output.write("Username,Database Size,Locked\n")
    for user in user_details:
        output.write(f"{user['username']},{user['db_size']},{user['locked']}\n")
    
    from io import BytesIO
    mem = BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    output.close()
    
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='users.csv')

def detect_mariadb_config():
    """Detect MariaDB configuration file location"""
    possible_paths = [
        '/etc/my.cnf.d/server.cnf',                    # Rocky Linux/RHEL/CentOS
        '/etc/my.cnf.d/mariadb-server.cnf',            # Alternative RHEL-based
        '/etc/mysql/mariadb.conf.d/50-server.cnf',     # Debian/Ubuntu
        '/etc/my.cnf'                                   # Generic fallback
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

@app.route('/set_ip_range', methods=['POST'])
@root_required
def set_ip_range():
    ip_range = request.json.get('ip_range', '')
    
    # Security: Validate IP address
    if ip_range and not is_safe_ip(ip_range):
        return jsonify({"status": "error", "message": "Invalid IP address format"}), 400
    
    # Detect MariaDB config file location
    mariadb_conf = detect_mariadb_config()
    if not mariadb_conf:
        log_action('set_ip_range', ip_range or 'all', 'failed: config not found')
        return jsonify({"status": "error", "message": "MariaDB configuration file not found"}), 500
    
    try:
        bind_addr = '0.0.0.0' if not ip_range else ip_range
        
        with open(mariadb_conf, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        found = False
        for line in lines:
            if line.strip().startswith('bind-address'):
                new_lines.append(f'bind-address = {bind_addr}\n')
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            for i, line in enumerate(new_lines):
                if '[mysqld]' in line or '[mariadb]' in line or '[server]' in line:
                    new_lines.insert(i + 1, f'bind-address = {bind_addr}\n')
                    break
        
        with open(mariadb_conf, 'w') as f:
            f.writelines(new_lines)
        
        subprocess.run(['systemctl', 'restart', 'mariadb'], check=True)
        log_action('set_ip_range', ip_range or 'all', 'success')
        return jsonify({"status": "success", "message": f"IP range set to {bind_addr}"})
    except Exception as e:
        log_action('set_ip_range', ip_range or 'all', 'failed')
        return jsonify({"status": "error", "message": "Operation failed"}), 500

if __name__ == '__main__':
    print("--- User Creation Web Tool ---")
    print(f"Access at: http://<your-server-ip>:5000")
    app.run(host='0.0.0.0', port=5000)

