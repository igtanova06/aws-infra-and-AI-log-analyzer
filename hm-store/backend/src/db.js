const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');

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

const pool = mysql.createPool(poolConfig);

// Test database connection immediately
(async () => {
  try {
    const connection = await pool.getConnection();
    logAppEvent('INFO', 'Database connection successfully established.');
    connection.release();
  } catch (error) {
    logAppEvent('ERROR', `Database connection timeout - Failed to connect to ${poolConfig.host}. Error: ${error.message}`);
  }
})();

module.exports = {
  pool,
  logAppEvent
};
