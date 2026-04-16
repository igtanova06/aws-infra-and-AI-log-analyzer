# Sử dụng Image PHP 8.1 với Apache tích hợp sẵn
FROM php:8.1-apache

# Cài đặt các extension PHP cần thiết cho database (nếu dùng MySQL)
RUN docker-php-ext-install mysqli pdo pdo_mysql

# Enable module rewrite của Apache
RUN a2enmod rewrite

# Copy mã nguồn Web App vào thư mục mặc định của Apache
COPY . /var/www/html/

# Phân quyền cho thư mục uploads hoặc temp nếu cần
RUN chown -R www-data:www-data /var/www/html

# Mở cổng 80 bên trong Container
EXPOSE 80
