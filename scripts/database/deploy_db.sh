#!/bin/bash
set -e

echo "🗄️ Database Deployment Script"
echo "================================"

# Load DB credentials from Terraform outputs
DB_HOST=$(cd ../../environments/dev && terraform output -raw db_endpoint)
DB_USER="admin"
DB_PASS=$(cd ../../environments/dev && terraform output -raw db_password)
DB_NAME="qlsv_system"

echo "📍 DB Host: $DB_HOST"
echo "👤 DB User: $DB_USER"
echo "🗄️ DB Name: $DB_NAME"

# Kiểm tra kết nối
echo ""
echo "🔍 Testing database connection..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" -e "SELECT VERSION();" || {
    echo "❌ Cannot connect to database"
    exit 1
}

echo "✅ Connection successful!"

# Deploy schema
echo ""
echo "📦 Deploying database schema..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" < ../../Web-Project-1/database/complete_setup.sql

echo ""
echo "✅ Database deployment complete!"
echo ""
echo "📊 Database Summary:"
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" -e "
USE qlsv_system;
SELECT 'Users' as Table_Name, COUNT(*) as Count FROM users
UNION ALL
SELECT 'Students', COUNT(*) FROM students
UNION ALL
SELECT 'Classes', COUNT(*) FROM classes
UNION ALL
SELECT 'Enrollments', COUNT(*) FROM enrollments
UNION ALL
SELECT 'Grades', COUNT(*) FROM grades;
"

echo ""
echo "🔐 Default Accounts:"
echo "  Admin: admin / 123@"
echo "  Lecturers: gv01, gv02, gv03 / 123@"
echo "  Students: sv01-sv10 / 123@"
