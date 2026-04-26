# 🎓 QLSV - Quản Lý Sinh Viên (Student Management System)

**PHP-based student management system with MySQL database**

## ✨ Features

- 👤 **Multi-role system** - Admin, Lecturer, Student
- 📚 **Class management** - Create and manage classes
- 📝 **Enrollment** - Student course registration
- 📊 **Grading** - Lecturer grade management
- 🔐 **Secure authentication** - SHA256 password hashing
- 📱 **Responsive UI** - Bootstrap-based interface

## 🏗️ Architecture

### Technology Stack
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Backend**: PHP 7.4+
- **Database**: MySQL 8.0
- **Web Server**: Apache 2.4
- **Container**: Docker

### Database Schema

**Tables:**
- `roles` - User roles (Admin, Lecturer, Student)
- `users` - User accounts and authentication
- `classes` - Course/class information
- `students` - Student profiles
- `enrollments` - Student course registrations
- `grades` - Student grades

## 🚀 Quick Start

### 1. Local Development

```bash
cd Web-Project-1/

# Start with Docker Compose
docker-compose up -d

# Access
http://localhost:8080/qlsv
```

### 2. Manual Setup

```bash
# Install dependencies
sudo yum install -y httpd php php-mysqlnd mysql

# Copy files
sudo cp -r * /var/www/html/

# Configure database
mysql -h <db-host> -u admin -p < database/complete_setup.sql

# Configure .env
cp .env.example .env
nano .env

# Start Apache
sudo systemctl start httpd
```

### 3. Production Deployment

See `../DEPLOYMENT_COMPLETE_GUIDE.md` for full deployment with Terraform + Ansible.

## 🔐 Default Accounts

**Admin:**
- Username: `admin`
- Password: `123@`

**Lecturers:**
- Username: `gv01`, `gv02`, `gv03`
- Password: `123@`

**Students:**
- Username: `sv01` to `sv10`
- Password: `123@`

## 📊 Database Configuration

### Environment Variables

```bash
# Database Connection
DB_HOST=localhost
DB_NAME=qlsv_system
DB_USER=admin
DB_PASS=your_password

# Application
APP_ENV=production
DEBUG=false
```

### Database Schema Deployment

```bash
# Deploy schema
mysql -h <db-host> -u admin -p < database/complete_setup.sql

# Verify
mysql -h <db-host> -u admin -p -e "USE qlsv_system; SHOW TABLES;"
```

## 🎯 User Roles & Permissions

### Admin
- ✅ Manage all users
- ✅ Manage classes
- ✅ View all enrollments
- ✅ View all grades
- ✅ System configuration

### Lecturer
- ✅ View assigned classes
- ✅ View enrolled students
- ✅ Grade students
- ✅ View teaching schedule

### Student
- ✅ View enrolled classes
- ✅ View grades
- ✅ View schedule
- ❌ Cannot modify data

## 📁 Project Structure

```
Web-Project-1/
├── admin/                    # Admin panel
│   ├── dashboard.php
│   ├── students.php
│   ├── lecturers.php
│   ├── classes.php
│   └── enrollments.php
├── lecturer/                 # Lecturer panel
│   ├── dashboard.php
│   ├── teaching.php
│   ├── grading.php
│   └── students_by_subject.php
├── student/                  # Student panel
│   ├── dashboard.php
│   ├── grades.php
│   └── schedule.php
├── api/                      # API endpoints
│   ├── auth.php
│   ├── db.php
│   ├── login.php
│   └── logout.php
├── assets/                   # Static files
│   └── css/
├── database/                 # Database schema
│   └── complete_setup.sql
├── inc/                      # Includes
│   ├── layout.php
│   └── ids.php
├── index.php                 # Login page
├── qlsv.php                  # Main application
├── Dockerfile                # Container image
└── .env.example              # Environment template
```

## 🔧 Configuration

### Apache Configuration

```apache
<VirtualHost *:8080>
    DocumentRoot /var/www/html
    
    <Directory /var/www/html>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog /var/log/httpd/error_log
    CustomLog /var/log/httpd/access_log combined
</VirtualHost>
```

### PHP Configuration

```ini
; php.ini
display_errors = Off
log_errors = On
error_log = /var/log/app/php-error.log
upload_max_filesize = 10M
post_max_size = 10M
```

## 🐛 Troubleshooting

### Cannot connect to database

```bash
# Check database connection
mysql -h <db-host> -u admin -p

# Verify .env file
cat .env

# Check PHP MySQL extension
php -m | grep mysql
```

### Permission denied errors

```bash
# Fix file permissions
sudo chown -R apache:apache /var/www/html
sudo chmod -R 755 /var/www/html

# Fix log directory
sudo mkdir -p /var/log/app
sudo chown apache:apache /var/log/app
```

### Session errors

```bash
# Check session directory
sudo ls -la /var/lib/php/session/

# Fix permissions
sudo chown -R apache:apache /var/lib/php/session/
```

## 📊 Monitoring

### Application Logs

```bash
# PHP errors
tail -f /var/log/app/php-error.log

# Apache access
tail -f /var/log/httpd/access_log

# Apache errors
tail -f /var/log/httpd/error_log
```

### CloudWatch Integration

Logs are automatically sent to CloudWatch when deployed with Terraform:
- `/aws/ec2/web-tier/system` - System logs
- `/aws/ec2/web-tier/httpd` - Apache logs
- `/aws/ec2/web-tier/application` - PHP application logs

## 🔐 Security

### Password Hashing

```php
// Password is hashed with SHA256 + salt
$password = SHA2(CONCAT('123@', 'username', '_salt'), 256);
```

### SQL Injection Prevention

```php
// Use prepared statements
$stmt = $conn->prepare("SELECT * FROM users WHERE username = ?");
$stmt->bind_param("s", $username);
$stmt->execute();
```

### Session Security

```php
// Regenerate session ID on login
session_regenerate_id(true);

// Set secure session parameters
ini_set('session.cookie_httponly', 1);
ini_set('session.use_only_cookies', 1);
```

## 📈 Performance

### Optimization Tips

1. **Enable OPcache**
```ini
opcache.enable=1
opcache.memory_consumption=128
opcache.max_accelerated_files=10000
```

2. **Database Indexing**
```sql
CREATE INDEX idx_username ON users(username);
CREATE INDEX idx_student_class ON enrollments(student_id, class_id);
```

3. **Caching**
```php
// Cache database queries
$cache_key = "user_" . $user_id;
if (!$user = cache_get($cache_key)) {
    $user = get_user_from_db($user_id);
    cache_set($cache_key, $user, 3600);
}
```

## 🧪 Testing

### Manual Testing

```bash
# Test login
curl -X POST http://localhost:8080/api/login.php \
    -d "username=admin&password=123@"

# Test API
curl http://localhost:8080/api/me.php \
    -H "Cookie: PHPSESSID=<session-id>"
```

### Load Testing

```bash
# Install Apache Bench
sudo yum install httpd-tools

# Run load test
ab -n 1000 -c 10 http://localhost:8080/qlsv
```

## 📝 Development

### Adding New Features

1. Create new PHP file in appropriate directory
2. Include authentication check
3. Use layout template
4. Add database queries with prepared statements
5. Test thoroughly

### Code Style

```php
<?php
// Use strict types
declare(strict_types=1);

// Include authentication
require_once '../api/auth.php';

// Check permissions
if ($_SESSION['role_code'] !== 'ADMIN') {
    header('Location: /qlsv');
    exit;
}

// Your code here
?>
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details

---

**Built with ❤️ for educational institutions**
