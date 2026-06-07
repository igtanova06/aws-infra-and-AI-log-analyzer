# 🛍️ H&M Clothing Store Full-Stack Web Application

This folder contains the source code for a modern, high-fidelity H&M clothing store application built to replace the old PHP student management system. It is designed to work seamlessly with the existing 2-tier AWS deployment architecture and provides comprehensive logging compatible with the **AI Agent RCA** project.

---

## 🛠️ Technology Stack
1. **Frontend**: React (18) + Tailwind CSS + Vite
2. **Backend**: Node.js + Express
3. **Database**: MySQL 8.0 (AWS RDS)
4. **Containerization**: Docker (Multi-stage build)

---

## 🏗️ Architecture & Logging Integration

To integrate with the **AI Agent RCA** log parser and correlator, this application writes logs to two distinct targets matching the CloudWatch configuration:

1. **HTTP Web Access Logs (stdout)**:
   - Written to the container standard output in the **Apache Access Log format**:
     `192.168.1.1 - - [22/Apr/2026:10:23:45 +0000] "GET /api/products HTTP/1.1" 200 450`
   - Monitored by the CloudWatch agent on the host machine and shipped to the `/aws/ec2/web-tier/httpd` log group.
   - Used by the AI Agent to detect web attacks such as **SQL Injection** (via URL query parameters matching strings like `union` or `select`).

2. **Application Event Logs (`/var/log/app/application.log`)**:
   - Written as structured **JSON objects** containing `level`, `message`, `component`, and `timestamp` keys.
   - Monitored by the CloudWatch agent and shipped to the `/aws/ec2/web-tier/application` log group.
   - Triggers security and performance alerts based on specific keyword matches:
     - Contains `"unauthorized"` or `"forbidden"` → classified as `unauthorized_access` (e.g. brute force detection).
     - Contains `"timeout"` → classified as `connection_timeout` (e.g. database pool exhaustion).

---

## 🛡️ RCA Security Simulation Panel

A dedicated **RCA Developer Simulator Console** is embedded directly within the frontend. It allows security engineers to execute synthetic attacks and trigger matching backend alerts:

*   **Trigger SQL Injection**: Simulates a malicious query attempting to leak credential hashes from the `users` table via the unescaped `/api/products/search` endpoint.
*   **Trigger Brute Force**: Fires 3 failed authentication events for the `admin` user within 1 second.
*   **Trigger DB Timeout**: Simulates database connection pool exhaustion.

---

## 📂 Project Structure

```
hm-store/
├── backend/
│   ├── src/
│   │   ├── db.js          # MySQL connection pool & RCA log writer
│   │   └── index.js        # Express API endpoints & HTTP logger
│   └── package.json        # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # E-commerce store UI & Simulation dashboard
│   │   ├── index.css       # Core Tailwind and custom styling
│   │   └── main.jsx        # React entrypoint
│   ├── index.html          # Web entrypoint (Google Fonts integration)
│   ├── tailwind.config.js  # Theme and color config
│   ├── postcss.config.js
│   └── package.json        # Frontend dependencies
├── database/
│   └── complete_setup.sql  # H&M database schema & mock dataset
└── Dockerfile              # Multi-stage image builder
```

---

## 💾 Database Schema

The store database (`qlsv_system`) contains 6 core tables:
*   `roles`: User roles (`ADMIN`, `CUSTOMER`).
*   `users`: User accounts with SHA-256 hashed credentials.
*   `categories`: E-commerce catalog sections (`Men`, `Women`, `Divided`, `Kids`, `Accessories`).
*   `products`: Clothing items with price, inventory stock, and description.
*   `orders`: Checkout transaction details.
*   `order_items`: Line items of each order.

### Default Accounts
*   **Admin**: `admin` / password: `123@`
*   **Customer 1**: `customer01` / password: `123@`
*   **Customer 2**: `customer02` / password: `123@`
*   **Customer 3**: `customer03` / password: `123@`

Password hashes are computed via SHA-256 using:
`crypto.createHash('sha256').update(password + username + '_salt').digest('hex')`
This aligns with the MySQL seed encryption:
`SHA2(CONCAT(password, username, '_salt'), 256)`

---

## 🚀 Local Development

1. **Prerequisites**: Ensure you have Node.js (v18+) and a running MySQL instance.
2. **Database Import**:
   ```bash
   mysql -h localhost -u root -p < database/complete_setup.sql
   ```
3. **Environment Setup**:
   Define variables on your host machine or pass them when launching:
   - `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`
4. **Backend Start**:
   ```bash
   cd backend
   npm install
   npm run dev
   ```
5. **Frontend Start**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173/` in your browser. (Note: For absolute routing, configure a proxy in `vite.config.js` or point the frontend API call to target the local backend port).
