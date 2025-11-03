# GrocerStock Setup Guide

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js (for development)
- Python 3.8+ (for development)

## 📁 Project Structure Setup

Create the following directory structure:

```
grocerstock/
├── frontend/
│   ├── index.html
│   ├── css/
│   ├── js/
│   ├── assets/
│   └── pages/
├── backend/
│   ├── flask_app/
│   └── node_service/
├── database/
└── docker/
```

## 🐳 Docker Configuration

### docker-compose.yml
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:latest
    container_name: grocerstock-mongo
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./database/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
      - MONGO_INITDB_DATABASE=grocerstock

  flask-app:
    build:
      context: ./backend/flask_app
      dockerfile: Dockerfile.flask
    container_name: grocerstock-flask
    ports:
      - "5000:5000"
    depends_on:
      - mongodb
    environment:
      - MONGO_URI=mongodb://admin:password@mongodb:27017/grocerstock?authSource=admin
      - OPEN_FOOD_FACTS_API_URL=https://world.openfoodfacts.org/api/v0
      - JWT_SECRET_KEY=your-secret-key-here
      - FLASK_ENV=development
    volumes:
      - ./backend/flask_app:/app
      - ./frontend:/app/static

  node-service:
    build:
      context: ./backend/node_service
      dockerfile: Dockerfile.node
    container_name: grocerstock-node
    ports:
      - "3000:3000"
    depends_on:
      - mongodb
    environment:
      - MONGO_URI=mongodb://admin:password@mongodb:27017/grocerstock?authSource=admin
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - JWT_SECRET=your-secret-key-here
      - NODE_ENV=development
    volumes:
      - ./backend/node_service:/app

volumes:
  mongodb_data:
```

### Dockerfile.flask
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

### Dockerfile.node
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

## 🗄️ Database Configuration

### database/init-mongo.js
```javascript
db = db.getSiblingDB('grocerstock');

// Create collections
db.createCollection('users');
db.createCollection('products');
db.createCollection('inventory');
db.createCollection('generated_barcodes');

// Create indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });

db.products.createIndex({ "barcode": 1 }, { unique: true });
db.products.createIndex({ "category": 1 });
db.products.createIndex({ "name": "text", "brand": "text" });

db.inventory.createIndex({ "user_id": 1, "product_id": 1 });
db.inventory.createIndex({ "expiry_date": 1 });
db.inventory.createIndex({ "status": 1 });

db.generated_barcodes.createIndex({ "custom_barcode": 1 }, { unique: true });
db.generated_barcodes.createIndex({ "user_id": 1 });

print('Database initialized successfully');
```

## 🔧 Backend Setup

### Flask Backend Dependencies (backend/flask_app/requirements.txt)
```txt
Flask==2.3.3
Flask-PyMongo==2.3.0
Flask-JWT-Extended==4.5.3
Flask-CORS==4.0.0
bcrypt==4.0.1
requests==2.31.0
python-barcode==0.14.0
Pillow==10.0.0
python-dotenv==1.0.0
Werkzeug==2.3.7
```

### Flask Application Structure (backend/flask_app/app.py)
```python
from flask import Flask, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import timedelta
import os

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/grocerstock')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Initialize extensions
    mongo = PyMongo(app)
    jwt = JWTManager(app)
    CORS(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.inventory import inventory_bp
    from routes.barcode import barcode_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(barcode_bp, url_prefix='/api/barcode')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### Node.js Service Dependencies (backend/node_service/package.json)
```json
{
  "name": "grocerstock-node-service",
  "version": "1.0.0",
  "description": "Real-time service for GrocerStock",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "socket.io": "^4.7.2",
    "mongoose": "^7.5.0",
    "axios": "^1.5.0",
    "cors": "^2.8.5",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
```

### Node.js Server (backend/node_service/server.js)
```javascript
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB connection
mongoose.connect(process.env.MONGO_URI || 'mongodb://localhost:27017/grocerstock', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Routes
app.use('/api/realtime', require('./routes/realtime'));
app.use('/api/ai', require('./routes/ai'));

// Socket.io for real-time updates
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);
  
  socket.on('join-inventory', (userId) => {
    socket.join(`inventory-${userId}`);
  });
  
  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Node.js service running on port ${PORT}`);
});
```

## 🎨 Frontend Setup

### Main HTML Structure (frontend/index.html)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GrocerStock - Smart Inventory Manager</title>
    <link rel="stylesheet" href="css/variables.css">
    <link rel="stylesheet" href="css/main.css">
    <link rel="stylesheet" href="css/animations.css">
    <link rel="stylesheet" href="css/responsive.css">
</head>
<body>
    <div id="app">
        <!-- App content will be loaded here -->
    </div>
    
    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/quagga@0.12.1/dist/quagga.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/filesaver.js@2.0.5/dist/FileSaver.min.js"></script>
    <script src="js/utils.js"></script>
    <script src="js/auth.js"></script>
    <script src="js/scanner.js"></script>
    <script src="js/inventory.js"></script>
    <script src="js/barcode-generator.js"></script>
    <script src="js/realtime.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
```

### CSS Variables (frontend/css/variables.css)
```css
:root {
  /* Primary Colors */
  --primary-orange: #FF9900;
  --primary-orange-light: #FFB84D;
  --primary-orange-dark: #E68A00;
  
  /* Neutral Colors */
  --white: #FFFFFF;
  --gray-50: #F8F9FA;
  --gray-100: #E9ECEF;
  --gray-200: #DEE2E6;
  --gray-500: #6C757D;
  --gray-800: #343A40;
  --black: #212529;
  
  /* Semantic Colors */
  --success: #28A745;
  --warning: #FFC107;
  --error: #DC3545;
  --info: #17A2B8;
  
  /* Typography */
  --font-family-primary: 'Inter', 'Segoe UI', system-ui, sans-serif;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  
  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
}
```

## 🔧 Environment Configuration

### .env.example
```env
# Flask Backend
MONGO_URI=mongodb://admin:password@mongodb:27017/grocerstock?authSource=admin
JWT_SECRET_KEY=your-super-secret-jwt-key-here
OPEN_FOOD_FACTS_API_URL=https://world.openfoodfacts.org/api/v0
FLASK_ENV=development

# Node.js Service
DEEPSEEK_API_KEY=your-deepseek-api-key-here
NODE_ENV=development
```

## 🚀 Development Commands

### Starting the Application
```bash
# Clone and setup
git clone <repository-url>
cd grocerstock

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start with Docker Compose
docker-compose up -d

# Or for development with logs
docker-compose up
```

### Development Setup (Optional)
```bash
# Flask backend development
cd backend/flask_app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

# Node.js service development
cd backend/node_service
npm install
npm run dev
```

## 📋 API Endpoints Summary

### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh token

### Product Endpoints
- `GET /api/products/search?barcode={code}` - Search by barcode
- `GET /api/products/search?query={name}` - Search by name
- `POST /api/products` - Create new product
- `GET /api/products/{id}` - Get product details
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

### Inventory Endpoints
- `GET /api/inventory` - Get user inventory
- `POST /api/inventory` - Add to inventory
- `PUT /api/inventory/{id}` - Update inventory item
- `DELETE /api/inventory/{id}` - Remove from inventory

### Barcode Endpoints
- `POST /api/barcode/generate` - Generate custom barcode
- `GET /api/barcode/{id}/image` - Get barcode image

### Real-time Endpoints (Node.js)
- `GET /api/realtime/inventory` - WebSocket connection
- `POST /api/ai/categorize` - AI categorization
- `POST /api/ai/suggestions` - Inventory suggestions

## 🧪 Testing the Setup

1. **Start the application:**
   ```bash
   docker-compose up -d
   ```

2. **Check services are running:**
   ```bash
   docker-compose ps
   ```

3. **Test MongoDB connection:**
   ```bash
   docker exec -it grocerstock-mongo mongosh -u admin -p password --authenticationDatabase admin
   ```

4. **Test Flask API:**
   ```bash
   curl http://localhost:5000/api/health
   ```

5. **Test Node.js service:**
   ```bash
   curl http://localhost:3000/api/health
   ```

This setup guide provides everything needed to get the GrocerStock application running with Docker Compose, including all configuration files and setup instructions.