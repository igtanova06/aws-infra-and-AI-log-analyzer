-- =============================================
-- COMPLETE DATABASE SETUP FOR H&M CLOTHING STORE
-- =============================================
-- DROP existing database and create fresh
DROP DATABASE IF EXISTS qlsv_system;
CREATE DATABASE qlsv_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE qlsv_system;

-- =============================================
-- TABLE: roles
-- =============================================
CREATE TABLE roles (
  role_id INT(11) NOT NULL AUTO_INCREMENT,
  role_code VARCHAR(50) NOT NULL UNIQUE,
  role_name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO roles (role_id, role_code, role_name) VALUES
(1, 'ADMIN', 'Administrator'),
(2, 'CUSTOMER', 'Customer');

-- =============================================
-- TABLE: users
-- =============================================
CREATE TABLE users (
  user_id INT(11) NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  full_name VARCHAR(200) DEFAULT NULL,
  email VARCHAR(100) DEFAULT NULL,
  phone VARCHAR(20) DEFAULT NULL,
  role_id INT(11) DEFAULT 2,
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  KEY idx_username (username),
  KEY idx_role (role_id),
  CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Default password for all accounts: 123@
-- Hash: SHA2(CONCAT('123@', username, '_salt'), 256)
INSERT INTO users (user_id, username, password, full_name, email, role_id, is_active) VALUES
-- Admin account (admin / 123@)
(1, 'admin', SHA2(CONCAT('123@', 'admin', '_salt'), 256), 'H&M Shop Manager', 'admin@hm-store.com', 1, 1),
-- Customer accounts (customer01-03 / 123@)
(2, 'customer01', SHA2(CONCAT('123@', 'customer01', '_salt'), 256), 'Nguyen Thi Minh', 'minh.nguyen@gmail.com', 2, 1),
(3, 'customer02', SHA2(CONCAT('123@', 'customer02', '_salt'), 256), 'Tran Van Binh', 'binh.tran@gmail.com', 2, 1),
(4, 'customer03', SHA2(CONCAT('123@', 'customer03', '_salt'), 256), 'Le Thi Dung', 'dung.le@gmail.com', 2, 1);

-- =============================================
-- TABLE: categories
-- =============================================
CREATE TABLE categories (
  category_id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO categories (category_id, name, description) VALUES
(1, 'Men', 'Trendy and classic menswear collections'),
(2, 'Women', 'Fashion-forward womenswear and dresses'),
(3, 'Divided', 'Young, casual, and street-style wear'),
(4, 'Kids', 'Comfortable and playful kids clothing'),
(5, 'Accessories', 'Bags, hats, jewelry, and belts');

-- =============================================
-- TABLE: products
-- =============================================
CREATE TABLE products (
  product_id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  price DECIMAL(10,2) NOT NULL,
  stock INT(11) NOT NULL DEFAULT 0,
  category_id INT(11) DEFAULT NULL,
  image_url VARCHAR(500) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (product_id),
  KEY idx_category (category_id),
  CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO products (product_id, name, description, price, stock, category_id, image_url) VALUES
-- Men's category (ID: 1)
(1, 'Relaxed Fit Hooded Jacket', 'Soft sweat jacket with a double-layered drawstring hood, zip at front, and side pockets. Ribbing at cuffs and hem. Soft brushed inside.', 799000.00, 45, 1, 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=500&q=80'),
(2, 'Regular Fit Linen-blend Shirt', 'Shirt in a woven linen and cotton blend. Turn-down collar, classic front, and a yoke at the back. Open chest pocket and long sleeves with adjustable buttoning at the cuffs.', 599000.00, 60, 1, 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=500&q=80'),
(3, 'Slim Fit Chino Pants', 'Chinos in stretch cotton twill. Zip fly with button, side pockets, and welt back pockets with button. Slim Fit for a close fit at thighs and knees.', 899000.00, 35, 1, 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=500&q=80'),

-- Women''s category (ID: 2)
(4, 'A-line Cotton Dress', 'Short dress in airy, woven cotton fabric. V-neck, buttons down the front, and short puff sleeves with narrow, elasticated cuffs. Flared A-line skirt.', 999000.00, 30, 2, 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=500&q=80'),
(5, 'Oversized Denim Jacket', 'Oversized jacket in sturdy cotton denim with a collar, buttons down the front, and welt side pockets. Chest pockets with flap and button.', 1199000.00, 25, 2, 'https://images.unsplash.com/photo-1551537482-f2075a1d41f2?w=500&q=80'),
(6, 'Rib-knit Mock-neck Top', 'Fitted top in soft rib-knit fabric. Mock neck, long sleeves, and a straight hem.', 499000.00, 50, 2, 'https://images.unsplash.com/photo-1564257631407-4deb1f99d992?w=500&q=80'),

-- Divided category (ID: 3)
(7, 'Printed Graphic Hoodie', 'Hoodie in sweatshirt fabric made from a cotton blend. Double-layered hood with drawstring, a kangaroo pocket, and graphic print at front.', 699000.00, 80, 3, 'https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=500&q=80'),
(8, 'Loose Fit Cargo Pants', 'Cargo pants in woven cotton fabric. Loose fit. High waist with elasticated drawstring, zip fly with button, side pockets, and cargo pockets.', 799000.00, 40, 3, 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=500&q=80'),

-- Kids'' category (ID: 4)
(9, '2-pack Cotton T-shirts', 'T-shirts in soft cotton jersey with a narrow ribbing around the neckline. One printed and one solid color.', 349000.00, 100, 4, 'https://images.unsplash.com/photo-1519457431-44ccd64a579b?w=500&q=80'),
(10, 'Denim Dungarees', 'Dungarees in washed, stretch denim. Adjustable straps with metal fasteners, chest pocket, and mock fly.', 599000.00, 30, 4, 'https://images.unsplash.com/photo-1622290291468-a28f7a7dc6a8?w=500&q=80'),

-- Accessories category (ID: 5)
(11, 'Cotton Canvas Shopper', 'Canvas bag with two handles at top and a spacious main compartment. Unlined.', 299000.00, 120, 5, 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&q=80'),
(12, 'Polarized Sunglasses', 'Sunglasses with lightweight plastic frames and polarized lenses that block glare and protect against UV rays.', 399000.00, 75, 5, 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=500&q=80');

-- =============================================
-- TABLE: orders
-- =============================================
CREATE TABLE orders (
  order_id INT(11) NOT NULL AUTO_INCREMENT,
  user_id INT(11) NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(50) DEFAULT 'Pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (order_id),
  KEY idx_user (user_id),
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample orders
INSERT INTO orders (order_id, user_id, total_amount, status, created_at) VALUES
(1, 2, 1398000.00, 'Completed', '2026-06-05 14:32:00'),
(2, 3, 1199000.00, 'Processing', '2026-06-07 09:15:00'),
(3, 4, 399000.00, 'Pending', '2026-06-08 00:05:00');

-- =============================================
-- TABLE: order_items
-- =============================================
CREATE TABLE order_items (
  order_item_id INT(11) NOT NULL AUTO_INCREMENT,
  order_id INT(11) NOT NULL,
  product_id INT(11) NOT NULL,
  quantity INT(11) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (order_item_id),
  KEY idx_order (order_id),
  KEY idx_product (product_id),
  CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
-- Order 1: 1 Hoodie + 1 Canvas Shopper
(1, 7, 1, 699000.00),
(1, 11, 2, 299000.00),
(1, 12, 1, 399000.00),
-- Order 2: 1 Denim Jacket
(2, 5, 1, 1199000.00),
-- Order 3: 1 Sunglasses
(3, 12, 1, 399000.00);

-- =============================================
-- SUMMARY
-- =============================================
-- Tables created: roles, users, categories, products, orders, order_items
-- Default accounts:
--   Admin: admin / 123@
--   Customers: customer01, customer02, customer03 / 123@
-- =============================================
