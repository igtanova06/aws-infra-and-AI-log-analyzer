const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Helper to log errors matching the RCA agent expectations
const logAppEvent = (level, message, component = 'DatabaseService') => {
  const timestamp = new Date().toISOString();
  const logEntry = JSON.stringify({
    level: level.toUpperCase(),
    message,
    component,
    timestamp
  }) + '\n';

  // Standard output
  console.log(`[${timestamp}] [${level.toUpperCase()}] [${component}] ${message}`);

  // Write to log file
  const logDir = '/var/log/app';
  const logFile = path.join(logDir, 'application.log');
  try {
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    fs.appendFileSync(logFile, logEntry);
  } catch (err) {
    // Fallback to local file in development
    try {
      fs.appendFileSync('./application.log', logEntry);
    } catch (e) {
      // Ignore write errors
    }
  }
};

const poolConfig = {
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'admin',
  password: process.env.DB_PASS || '123@',
  database: process.env.DB_NAME || 'qlsv_system',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
};

logAppEvent('INFO', `Initializing DB Pool connected to ${poolConfig.host} (DB: ${poolConfig.database})`);

const realPool = mysql.createPool(poolConfig);
let useMock = false;

// ------------------------------------------------------------
// IN-MEMORY DATABASE MOCK STORE
// ------------------------------------------------------------
function hashPassword(password, username) {
  return crypto.createHash('sha256').update(password + username + '_salt').digest('hex');
}

const mockRoles = [
  { role_id: 1, role_code: 'ADMIN', role_name: 'Administrator' },
  { role_id: 2, role_code: 'CUSTOMER', role_name: 'Customer' }
];

const mockUsers = [
  { user_id: 1, username: 'admin', password: hashPassword('123@', 'admin'), full_name: 'H&M Shop Manager', email: 'admin@hm-store.com', role_id: 1, is_active: 1 },
  { user_id: 2, username: 'customer01', password: hashPassword('123@', 'customer01'), full_name: 'Nguyen Thi Minh', email: 'minh.nguyen@gmail.com', role_id: 2, is_active: 1 },
  { user_id: 3, username: 'customer02', password: hashPassword('123@', 'customer02'), full_name: 'Tran Van Binh', email: 'binh.tran@gmail.com', role_id: 2, is_active: 1 },
  { user_id: 4, username: 'customer03', password: hashPassword('123@', 'customer03'), full_name: 'Le Thi Dung', email: 'dung.le@gmail.com', role_id: 2, is_active: 1 }
];

const mockCategories = [
  { category_id: 1, name: 'Men', description: 'Trendy and classic menswear collections' },
  { category_id: 2, name: 'Women', description: 'Fashion-forward womenswear and dresses' },
  { category_id: 3, name: 'Divided', description: 'Young, casual, and street-style wear' },
  { category_id: 4, name: 'Kids', description: 'Comfortable and playful kids clothing' },
  { category_id: 5, name: 'Accessories', description: 'Bags, hats, jewelry, and belts' }
];

const mockProducts = [
  { product_id: 1, name: 'Relaxed Fit Hooded Jacket', description: 'Soft sweat jacket with a double-layered drawstring hood, zip at front, and side pockets. Ribbing at cuffs and hem. Soft brushed inside.', price: 799000.00, stock: 45, category_id: 1, image_url: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=500&q=80' },
  { product_id: 2, name: 'Regular Fit Linen-blend Shirt', description: 'Shirt in a woven linen and cotton blend. Turn-down collar, classic front, and a yoke at the back. Open chest pocket and long sleeves with adjustable buttoning at the cuffs.', price: 599000.00, stock: 60, category_id: 1, image_url: 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=500&q=80' },
  { product_id: 3, name: 'Slim Fit Chino Pants', description: 'Chinos in stretch cotton twill. Zip fly with button, side pockets, and welt back pockets with button. Slim Fit for a close fit at thighs and knees.', price: 899000.00, stock: 35, category_id: 1, image_url: 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=500&q=80' },
  { product_id: 4, name: 'A-line Cotton Dress', description: 'Short dress in airy, woven cotton fabric. V-neck, buttons down the front, and short puff sleeves with narrow, elasticated cuffs. Flared A-line skirt.', price: 999000.00, stock: 30, category_id: 2, image_url: 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=500&q=80' },
  { product_id: 5, name: 'Oversized Denim Jacket', description: 'Oversized jacket in sturdy cotton denim with a collar, buttons down the front, and welt side pockets. Chest pockets with flap and button.', price: 1199000.00, stock: 25, category_id: 2, image_url: 'https://images.unsplash.com/photo-1551537482-f2075a1d41f2?w=500&q=80' },
  { product_id: 6, name: 'Rib-knit Mock-neck Top', description: 'Fitted top in soft rib-knit fabric. Mock neck, long sleeves, and a straight hem.', price: 499000.00, stock: 50, category_id: 2, image_url: 'https://images.unsplash.com/photo-1564257631407-4deb1f99d992?w=500&q=80' },
  { product_id: 8, name: 'Loose Fit Cargo Pants', description: 'Cargo pants in woven cotton fabric. Loose fit. High waist with elasticated drawstring, zip fly with button, side pockets, and cargo pockets.', price: 799000.00, stock: 40, category_id: 3, image_url: 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=500&q=80' },
  { product_id: 9, name: '2-pack Cotton T-shirts', description: 'T-shirts in soft cotton jersey with a narrow ribbing around the neckline. One printed and one solid color.', price: 349000.00, stock: 100, category_id: 4, image_url: 'https://images.unsplash.com/photo-1519457431-44ccd64a579b?w=500&q=80' },
  { product_id: 10, name: 'Denim Dungarees', description: 'Dungarees in washed, stretch denim. Adjustable straps with metal fasteners, chest pocket, and mock fly.', price: 599000.00, stock: 30, category_id: 4, image_url: 'https://images.unsplash.com/photo-1622290291468-a28f7a7dc6a8?w=500&q=80' },
  { product_id: 11, name: 'Cotton Canvas Shopper', description: 'Canvas bag with two handles at top and a spacious main compartment. Unlined.', price: 299000.00, stock: 120, category_id: 5, image_url: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&q=80' },
  { product_id: 12, name: 'Polarized Sunglasses', description: 'Sunglasses with lightweight plastic frames and polarized lenses that block glare and protect against UV rays.', price: 399000.00, stock: 75, category_id: 5, image_url: 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=500&q=80' }
];

const mockOrders = [
  { order_id: 1, user_id: 2, total_amount: 997000.00, status: 'Completed', created_at: '2026-06-05T14:32:00.000Z' },
  { order_id: 2, user_id: 3, total_amount: 1199000.00, status: 'Processing', created_at: '2026-06-07T09:15:00.000Z' },
  { order_id: 3, user_id: 4, total_amount: 399000.00, status: 'Pending', created_at: '2026-06-08T00:05:00.000Z' }
];

const mockOrderItems = [
  { order_item_id: 2, order_id: 1, product_id: 11, quantity: 2, price: 299000.00 },
  { order_item_id: 3, order_id: 1, product_id: 12, quantity: 1, price: 399000.00 },
  { order_item_id: 4, order_id: 2, product_id: 5, quantity: 1, price: 1199000.00 },
  { order_item_id: 5, order_id: 3, product_id: 12, quantity: 1, price: 399000.00 }
];

function executeMockQuery(sql, params = []) {
  const normalizedSql = sql.replace(/\s+/g, ' ').trim();

  // 1. SELECT 1 (Healthcheck)
  if (normalizedSql === 'SELECT 1') {
    return [[{ 1: 1 }]];
  }

  // 2. Auth Login query
  if (normalizedSql.includes('FROM users u JOIN roles r') && normalizedSql.includes('WHERE u.username = ?')) {
    const username = params[0];
    const user = mockUsers.find(u => u.username === username);
    if (!user) return [[]];
    const role = mockRoles.find(r => r.role_id === user.role_id);
    return [[{ ...user, role_code: role ? role.role_code : 'CUSTOMER' }]];
  }

  // 3. Product details
  if (normalizedSql.includes('FROM products p JOIN categories c') && normalizedSql.includes('WHERE p.product_id = ?')) {
    const id = parseInt(params[0], 10);
    const prod = mockProducts.find(p => p.product_id === id);
    if (!prod) return [[]];
    const cat = mockCategories.find(c => c.category_id === prod.category_id);
    return [[{ ...prod, category_name: cat ? cat.name : '' }]];
  }

  // 4. Products by category
  if (normalizedSql.includes('FROM products p JOIN categories c') && normalizedSql.includes('WHERE c.name = ?')) {
    const catName = params[0];
    const cat = mockCategories.find(c => c.name.toLowerCase() === catName.toLowerCase());
    if (!cat) return [[]];
    const prods = mockProducts.filter(p => p.category_id === cat.category_id).map(prod => ({
      ...prod,
      category_name: cat.name
    }));
    return [prods];
  }

  // 5. Products Search (with raw SQL injection check)
  if (normalizedSql.includes('FROM products p JOIN categories c') && normalizedSql.includes('WHERE p.name LIKE')) {
    // Extract query parameter search string
    // e.g. WHERE p.name LIKE '%jeans%'
    const match = normalizedSql.match(/LIKE\s+'%([^%]*)%'/i);
    const q = match ? match[1] : '';

    const loweredQ = q.toLowerCase();
    if (loweredQ.includes('union') || loweredQ.includes('select') || loweredQ.includes('--') || loweredQ.includes("'")) {
      throw new Error(`Table 'qlsv_system.users' does not exist (simulated SQL syntax error for injection test)`);
    }

    const prods = mockProducts.filter(p => p.name.toLowerCase().includes(q.toLowerCase())).map(prod => {
      const cat = mockCategories.find(c => c.category_id === prod.category_id);
      return { ...prod, category_name: cat ? cat.name : '' };
    });
    return [prods];
  }

  // 6. Products list (all)
  if (normalizedSql.startsWith('SELECT p.*, c.name as category_name FROM products p JOIN categories c')) {
    const prods = mockProducts.map(prod => {
      const cat = mockCategories.find(c => c.category_id === prod.category_id);
      return { ...prod, category_name: cat ? cat.name : '' };
    });
    return [prods];
  }

  // 7. Categories list
  if (normalizedSql === 'SELECT * FROM categories') {
    return [mockCategories];
  }

  // 8. Order checkout: stock and name check
  if (normalizedSql.includes('SELECT stock, name FROM products WHERE product_id = ?')) {
    const id = parseInt(params[0], 10);
    const prod = mockProducts.find(p => p.product_id === id);
    if (!prod) return [[]];
    return [[{ stock: prod.stock, name: prod.name }]];
  }

  // 9. Order checkout: deduct stock
  if (normalizedSql.includes('UPDATE products SET stock = stock - ? WHERE product_id = ?')) {
    const qty = parseInt(params[0], 10);
    const id = parseInt(params[1], 10);
    const prod = mockProducts.find(p => p.product_id === id);
    if (prod) {
      prod.stock = Math.max(0, prod.stock - qty);
    }
    return [{ affectedRows: 1 }];
  }

  // 10. Order checkout: insert order
  if (normalizedSql.includes('INSERT INTO orders (user_id, total_amount, status)')) {
    const user_id = parseInt(params[0], 10);
    const total_amount = parseFloat(params[1]);
    const status = params[2];
    const newId = mockOrders.length > 0 ? Math.max(...mockOrders.map(o => o.order_id)) + 1 : 1;
    mockOrders.push({
      order_id: newId,
      user_id,
      total_amount,
      status,
      created_at: new Date().toISOString()
    });
    return [{ insertId: newId }];
  }

  // 11. Order checkout: insert order items
  if (normalizedSql.includes('INSERT INTO order_items (order_id, product_id, quantity, price)')) {
    const order_id = parseInt(params[0], 10);
    const product_id = parseInt(params[1], 10);
    const quantity = parseInt(params[2], 10);
    const price = parseFloat(params[3]);
    const newId = mockOrderItems.length > 0 ? Math.max(...mockOrderItems.map(oi => oi.order_item_id)) + 1 : 1;
    mockOrderItems.push({
      order_item_id: newId,
      order_id,
      product_id,
      quantity,
      price
    });
    return [{ insertId: newId }];
  }

  // 12. Admin dashboard: total sales and orders
  if (normalizedSql.includes('SELECT SUM(total_amount) as totalSales, COUNT(*) as totalOrders FROM orders')) {
    const totalSales = mockOrders.reduce((sum, o) => sum + o.total_amount, 0);
    const totalOrders = mockOrders.length;
    return [[{ totalSales, totalOrders }]];
  }

  // 13. Admin dashboard: total customer count
  if (normalizedSql.includes('SELECT COUNT(*) as totalCustomers FROM users WHERE role_id = 2')) {
    const totalCustomers = mockUsers.filter(u => u.role_id === 2).length;
    return [[{ totalCustomers }]];
  }

  // 14. Admin dashboard: total product count
  if (normalizedSql.includes('SELECT COUNT(*) as totalProducts FROM products')) {
    const totalProducts = mockProducts.length;
    return [[{ totalProducts }]];
  }

  // 15. Admin dashboard: recent orders list
  if (normalizedSql.includes('SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.user_id')) {
    const sortedOrders = [...mockOrders].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5);
    const result = sortedOrders.map(o => {
      const user = mockUsers.find(u => u.user_id === o.user_id);
      return {
        ...o,
        username: user ? user.username : 'unknown'
      };
    });
    return [result];
  }

  console.log(`[MOCK] Unhandled SQL query: "${sql}" with params:`, params);
  return [[]];
}

const pool = {
  query: async (sql, params) => {
    if (useMock) {
      return executeMockQuery(sql, params);
    }
    try {
      return await realPool.query(sql, params);
    } catch (err) {
      logAppEvent('WARN', `Database connection failed during query. Falling back to IN-MEMORY database. Error: ${err.message}`);
      useMock = true;
      return executeMockQuery(sql, params);
    }
  },
  getConnection: async () => {
    if (useMock) {
      return {
        beginTransaction: async () => {},
        query: async (sql, params) => executeMockQuery(sql, params),
        commit: async () => {},
        rollback: async () => {},
        release: () => {}
      };
    }
    try {
      return await realPool.getConnection();
    } catch (err) {
      logAppEvent('WARN', `Failed to get connection. Falling back to mock. Error: ${err.message}`);
      useMock = true;
      return {
        beginTransaction: async () => {},
        query: async (sql, params) => executeMockQuery(sql, params),
        commit: async () => {},
        rollback: async () => {},
        release: () => {}
      };
    }
  }
};

// Test database connection immediately
(async () => {
  try {
    const connection = await realPool.getConnection();
    logAppEvent('INFO', 'Database connection successfully established.');
    connection.release();
  } catch (error) {
    logAppEvent('WARN', `Database connection failed/timeout - Falling back to IN-MEMORY MOCK database. Error: ${error.message}`);
    useMock = true;
  }
})();

module.exports = {
  pool,
  logAppEvent
};
