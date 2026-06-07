const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { pool, logAppEvent } = require('./db');

const app = express();
const PORT = process.env.PORT || 80;

app.use(cors());
app.use(express.json());

// Apache-compatible HTTP access logger
function getApacheDateFormat() {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const d = new Date();
  const day = String(d.getUTCDate()).padStart(2, '0');
  const month = months[d.getUTCMonth()];
  const year = d.getUTCFullYear();
  const hours = String(d.getUTCHours()).padStart(2, '0');
  const minutes = String(d.getUTCMinutes()).padStart(2, '0');
  const seconds = String(d.getUTCSeconds()).padStart(2, '0');
  return `${day}/${month}/${year}:${hours}:${minutes}:${seconds} +0000`;
}

app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress || '127.0.0.1';
    const cleanIp = ip.includes('::ffff:') ? ip.split('::ffff:')[1] : ip;
    const apacheDate = getApacheDateFormat();
    
    // Apache log format: 192.168.1.1 - - [22/Apr/2026:10:23:45 +0000] "GET /api/products HTTP/1.1" 200 1234
    const contentLength = res.get('Content-Length') || 0;
    const apacheLog = `${cleanIp} - - [${apacheDate}] "${req.method} ${req.originalUrl} HTTP/1.1" ${res.statusCode} ${contentLength}`;
    
    // Standard stdout logging is parsed by CloudWatch agent as container log (/aws/ec2/web-tier/httpd)
    console.log(apacheLog);
  });
  next();
});

// Helper for SHA-256 password hashing matching SQL database
function hashPassword(password, username) {
  return crypto.createHash('sha256').update(password + username + '_salt').digest('hex');
}

// ------------------------------------------------------------
// API ROUTES
// ------------------------------------------------------------

// 1. Health check
app.get('/api/health', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT 1');
    res.json({ status: 'healthy', database: 'connected', timestamp: new Date().toISOString() });
  } catch (error) {
    logAppEvent('ERROR', `Health check failed - Database timeout: ${error.message}`);
    res.status(500).json({ status: 'unhealthy', database: 'disconnected', error: error.message });
  }
});

// 2. Authentication API (Login)
app.post('/api/auth/login', async (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password are required' });
  }

  try {
    const [users] = await pool.query(
      'SELECT u.*, r.role_code FROM users u JOIN roles r ON u.role_id = r.role_id WHERE u.username = ?',
      [username]
    );

    if (users.length === 0) {
      logAppEvent('WARN', `Unauthorized access attempt: User '${username}' not found.`, 'AuthService');
      return res.status(401).json({ error: 'Invalid username or password' });
    }

    const user = users[0];
    const computedHash = hashPassword(password, username);

    if (user.password !== computedHash) {
      logAppEvent('WARN', `Unauthorized access attempt: Password mismatch for user '${username}'.`, 'AuthService');
      return res.status(401).json({ error: 'Invalid username or password' });
    }

    if (!user.is_active) {
      logAppEvent('WARN', `Unauthorized access attempt: Blocked active user '${username}'.`, 'AuthService');
      return res.status(403).json({ error: 'Account is deactivated' });
    }

    logAppEvent('INFO', `User login successful: ${username} (${user.role_code})`, 'AuthService');
    res.json({
      user: {
        id: user.user_id,
        username: user.username,
        fullName: user.full_name,
        email: user.email,
        role: user.role_code
      }
    });
  } catch (error) {
    logAppEvent('ERROR', `Login server error: ${error.message}`, 'AuthService');
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// 3. Products API
app.get('/api/products', async (req, res) => {
  const { category } = req.query;
  try {
    let query = 'SELECT p.*, c.name as category_name FROM products p JOIN categories c ON p.category_id = c.category_id';
    const params = [];

    if (category) {
      query += ' WHERE c.name = ?';
      params.push(category);
    }

    const [products] = await pool.query(query, params);
    res.json(products);
  } catch (error) {
    logAppEvent('ERROR', `Failed to fetch products: ${error.message}`, 'ProductService');
    res.status(500).json({ error: 'Failed to retrieve products' });
  }
});

// 4. Products Search (SIMULATING SQL INJECTION VULNERABILITY)
// We use raw concatenation without prepared statements so users can run custom SQL injections
app.get('/api/products/search', async (req, res) => {
  const { q } = req.query;
  if (!q) {
    return res.status(400).json({ error: 'Search term is required' });
  }

  // Raw query concatenation vulnerability
  const rawQuery = `SELECT p.*, c.name as category_name FROM products p JOIN categories c ON p.category_id = c.category_id WHERE p.name LIKE '%${q}%'`;
  
  try {
    // Check if the query looks suspicious and log SQL injection warnings for correlation
    const loweredQ = q.toLowerCase();
    if (loweredQ.includes('union') || loweredQ.includes('select') || loweredQ.includes('--') || loweredQ.includes("'")) {
      logAppEvent('WARN', `SQL injection vulnerability pattern detected in search parameter: ${q}`, 'SecurityGuard');
    }

    const [products] = await pool.query(rawQuery);
    res.json(products);
  } catch (error) {
    logAppEvent('ERROR', `SQL Database execution exception: ${error.message} | Query: ${rawQuery}`, 'DatabaseService');
    res.status(500).json({ error: 'Database query execution error', query: rawQuery });
  }
});

// 5. Product Detail
app.get('/api/products/:id', async (req, res) => {
  const { id } = req.params;
  try {
    const [products] = await pool.query(
      'SELECT p.*, c.name as category_name FROM products p JOIN categories c ON p.category_id = c.category_id WHERE p.product_id = ?',
      [id]
    );

    if (products.length === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }

    res.json(products[0]);
  } catch (error) {
    logAppEvent('ERROR', `Failed to fetch product details for ID ${id}: ${error.message}`, 'ProductService');
    res.status(500).json({ error: 'Failed to retrieve product details' });
  }
});

// 6. Categories API
app.get('/api/categories', async (req, res) => {
  try {
    const [categories] = await pool.query('SELECT * FROM categories');
    res.json(categories);
  } catch (error) {
    logAppEvent('ERROR', `Failed to fetch categories: ${error.message}`, 'ProductService');
    res.status(500).json({ error: 'Failed to retrieve categories' });
  }
});

// 7. Orders API (Create Order)
app.post('/api/orders', async (req, res) => {
  const { userId, items, totalAmount } = req.body;

  if (!userId || !items || items.length === 0 || !totalAmount) {
    return res.status(400).json({ error: 'Invalid order request parameters' });
  }

  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();

    // Insert order record
    const [orderRes] = await conn.query(
      'INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, ?)',
      [userId, totalAmount, 'Processing']
    );
    const orderId = orderRes.insertId;

    // Process each item, update stock
    for (const item of items) {
      // Check stock
      const [prodRes] = await conn.query('SELECT stock, name FROM products WHERE product_id = ?', [item.productId]);
      if (prodRes.length === 0) {
        throw new Error(`Product not found: ID ${item.productId}`);
      }

      const currentStock = prodRes[0].stock;
      if (currentStock < item.quantity) {
        throw new Error(`Insufficient stock for ${prodRes[0].name}. Available: ${currentStock}, Requested: ${item.quantity}`);
      }

      // Deduct stock
      await conn.query('UPDATE products SET stock = stock - ? WHERE product_id = ?', [item.quantity, item.productId]);

      // Add order item details
      await conn.query(
        'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
        [orderId, item.productId, item.quantity, item.price]
      );
    }

    await conn.commit();
    logAppEvent('INFO', `Order #${orderId} created successfully for user #${userId}. Total: ${totalAmount} VND`, 'OrderService');
    res.status(201).json({ status: 'success', orderId });
  } catch (error) {
    await conn.rollback();
    logAppEvent('ERROR', `Failed to create order: ${error.message}`, 'OrderService');
    res.status(500).json({ error: error.message });
  } finally {
    conn.release();
  }
});

// 8. Admin statistics dashboard
app.get('/api/admin/stats', async (req, res) => {
  try {
    const [salesResult] = await pool.query('SELECT SUM(total_amount) as totalSales, COUNT(*) as totalOrders FROM orders');
    const [usersResult] = await pool.query('SELECT COUNT(*) as totalCustomers FROM users WHERE role_id = 2');
    const [productsResult] = await pool.query('SELECT COUNT(*) as totalProducts FROM products');
    
    // Fetch last 5 orders with username
    const [lastOrders] = await pool.query(
      'SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.user_id ORDER BY o.created_at DESC LIMIT 5'
    );

    res.json({
      totalSales: salesResult[0].totalSales || 0,
      totalOrders: salesResult[0].totalOrders || 0,
      totalCustomers: usersResult[0].totalCustomers || 0,
      totalProducts: productsResult[0].totalProducts || 0,
      recentOrders: lastOrders
    });
  } catch (error) {
    logAppEvent('ERROR', `Admin statistics retrieval failed: ${error.message}`, 'AdminService');
    res.status(500).json({ error: 'Failed to retrieve stats' });
  }
});

// ------------------------------------------------------------
// RCA SECURITY SIMULATION APIS (Developer controls)
// ------------------------------------------------------------
app.post('/api/simulate/sql-injection', (req, res) => {
  const ip = req.body.ip || '198.51.100.45'; // Simulated external attacker IP
  const payload = req.body.payload || "/api/products/search?q=jeans'%20UNION%20SELECT%20user_id,username,password%20FROM%20users--";
  const apacheDate = getApacheDateFormat();
  
  // 1. Simulate the Apache entry matching SQL Injection
  const apacheLog = `${ip} - - [${apacheDate}] "GET ${payload} HTTP/1.1" 500 248`;
  console.log(apacheLog);

  // 2. Log custom application warning that parser reads
  logAppEvent('WARN', `SQL injection vulnerability pattern detected in search parameter: UNION SELECT`, 'SecurityGuard');
  logAppEvent('ERROR', `SQL Database execution exception: Table 'users' contains sensitive hash passwords. Query: SELECT * FROM products WHERE name LIKE '%jeans' UNION SELECT user_id,username,password FROM users--'`, 'DatabaseService');

  res.json({ message: 'SQL Injection simulated successfully in application logs.' });
});

app.post('/api/simulate/brute-force', (req, res) => {
  const ip = req.body.ip || '203.0.113.110';
  const username = req.body.username || 'admin';
  const apacheDate = getApacheDateFormat();

  // Simulate multiple unauthorized logs
  for (let i = 0; i < 3; i++) {
    setTimeout(() => {
      const logStr = `${ip} - - [${getApacheDateFormat()}] "POST /api/auth/login HTTP/1.1" 401 64`;
      console.log(logStr);
      logAppEvent('WARN', `Unauthorized access attempt: Password mismatch for user '${username}'.`, 'AuthService');
    }, i * 200);
  }

  res.json({ message: 'Brute force attack logs simulated successfully.' });
});

app.post('/api/simulate/db-timeout', (req, res) => {
  logAppEvent('ERROR', 'Database connection timeout - mysql connection pool exhausted. System capacity exceeded.', 'DatabaseService');
  logAppEvent('ERROR', 'Database connection timeout - Failed to reconnect to RDS MySQL instance after 3 retries.', 'DatabaseService');
  res.json({ message: 'Database timeout logs simulated successfully.' });
});

// ------------------------------------------------------------
// FRONTEND SERVING
// ------------------------------------------------------------

// Serve built React files
app.use(express.static(path.join(__dirname, '../../frontend/dist')));

// Serve placeholder images for products
app.get('/images/:name', (req, res) => {
  // We can return a generic SVG or color swatch if files don't exist
  res.setHeader('Content-Type', 'image/svg+xml');
  const colorMap = {
    men_jacket: '#2c3e50',
    men_linen: '#34495e',
    men_chino: '#7f8c8d',
    women_dress: '#9b59b6',
    women_denim: '#2980b9',
    women_top: '#e74c3c',
    div_hoodie: '#d35400',
    div_cargo: '#27ae60',
    kids_tee: '#f1c40f',
    kids_denim: '#16a085',
    acc_canvas: '#bdc3c7',
    acc_glasses: '#34495e'
  };
  const name = req.params.name.replace('.jpg', '');
  const color = colorMap[name] || '#7f8c8d';
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="400" viewBox="0 0 300 400">
    <rect width="100%" height="100%" fill="${color}"/>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#ffffff" font-family="system-ui, sans-serif" font-size="24" font-weight="bold">${name.replace('_', ' ').toUpperCase()}</text>
    <text x="50%" y="58%" dominant-baseline="middle" text-anchor="middle" fill="#ffffff" font-family="system-ui, sans-serif" font-size="14" opacity="0.8">H&amp;M Premium Collection</text>
  </svg>`;
  res.send(svg);
});

// Catch-all route to serve Index.html for React SPA Router
app.get('*', (req, res) => {
  if (req.path.startsWith('/api/')) {
    return res.status(404).json({ error: 'API Route Not Found' });
  }
  res.sendFile(path.join(__dirname, '../../frontend/dist/index.html'));
});

app.listen(PORT, () => {
  logAppEvent('INFO', `H&M Store server is running on port ${PORT}`);
});
