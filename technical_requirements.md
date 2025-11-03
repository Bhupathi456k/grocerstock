# GrocerStock Technical Requirements

## 📋 File Structure & Dependencies

### Project Root
```
grocerstock/
├── .gitignore
├── README.md
├── docker-compose.yml
└── .env.example
```

### Frontend Structure
```
frontend/
├── index.html
├── splash.html
├── css/
│   ├── main.css
│   ├── animations.css
│   ├── responsive.css
│   └── variables.css
├── js/
│   ├── app.js              # Main application logic
│   ├── auth.js             # Authentication handling
│   ├── scanner.js          # Barcode scanning functionality
│   ├── inventory.js        # Inventory management
│   ├── barcode-generator.js # Custom barcode generation
│   ├── realtime.js         # Real-time updates
│   └── utils.js            # Utility functions
├── assets/
│   ├── images/
│   │   ├── logo.svg
│   │   ├── splash-logo.svg
│   │   └── icons/
│   └── fonts/
└── pages/
    ├── login.html
    ├── dashboard.html
    ├── scanner.html
    ├── inventory.html
    └── barcode-generator.html
```

### Backend Structure
```
backend/
├── flask_app/
│   ├── app.py              # Main Flask application
│   ├── models.py           # Database models
│   ├── config.py           # Configuration
│   ├── requirements.txt
│   ├── Dockerfile.flask
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py         # Authentication routes
│   │   ├── products.py      # Product management
│   │   ├── inventory.py     # Inventory operations
│   │   └── barcode.py      # Barcode generation
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── barcode_utils.py # Barcode processing
│   │   ├── image_processing.py # Image handling
│   │   ├── auth_utils.py    # Authentication helpers
│   │   └── api_utils.py     # External API calls
│   └── static/
│       └── barcodes/        # Generated barcode images
└── node_service/
    ├── package.json
    ├── server.js           # Main Node.js server
    ├── Dockerfile.node
    ├── routes/
    │   ├── realtime.js     # WebSocket routes
    │   └── ai.js           # AI integration routes
    ├── utils/
    │   ├── websocket.js    # WebSocket management
    │   └── ai-utils.js     # DeepSeek API integration
    └── middleware/
        └── auth.js         # Authentication middleware
```

### Database Initialization
```
database/
└── init-mongo.js           # MongoDB setup script
```

## 🔧 Dependencies Specification

### Flask Backend Dependencies (requirements.txt)
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

### Node.js Service Dependencies (package.json)
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

### Frontend Dependencies (CDN links in HTML)
```html
<!-- In index.html -->
<script src="https://cdn.jsdelivr.net/npm/quagga@0.12.1/dist/quagga.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/filesaver.js@2.0.5/dist/FileSaver.min.js"></script>
```

## 🎨 UI Component Specifications

### Color System
```css
/* variables.css */
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
}
```

### Typography Scale
```css
:root {
  --font-family-primary: 'Inter', 'Segoe UI', system-ui, sans-serif;
  
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
}
```

### Component Specifications

#### 1. Splash Screen
- **Duration**: 2-3 seconds
- **Animation**: Logo scale + fade-in with loading spinner
- **Background**: Solid white with orange accent
- **Transition**: Smooth fade to main app

#### 2. Login/Signup Forms
- **Fields**: Email/Username, Password, Confirm Password (signup)
- **Validation**: Real-time field validation
- **Error States**: Clear error messages with icons
- **Success States**: Smooth transitions to dashboard

#### 3. Scanner Interface
- **Camera Access**: Request permissions with fallback
- **Overlay**: Orange scanning frame with instructions
- **Feedback**: Visual and audio feedback on scan
- **Processing**: Loading state during API calls

#### 4. Product Cards
- **Layout**: Grid-based responsive cards
- **Information**: Image, name, brand, expiry date, quantity
- **Actions**: Edit, delete, quick actions
- **States**: Normal, expired (red accent), low stock (yellow)

#### 5. Barcode Generator
- **Input Fields**: Product name, category, optional weight
- **Preview**: Real-time barcode preview
- **Download Options**: PNG, SVG formats
- **Print**: Print-friendly layout

## 🔌 API Integration Specifications

### Open Food Facts API
```javascript
// Base URL: https://world.openfoodfacts.org/api/v0
// Endpoint: /product/{barcode}.json

// Expected Response Structure:
{
  "product": {
    "product_name": "Product Name",
    "brands": "Brand Name",
    "categories": "Category, Subcategory",
    "image_url": "https://...",
    "nutriments": { ... },
    "quantity": "500g"
  }
}
```

### DeepSeek AI API Integration
```javascript
// For product categorization
{
  "prompt": "Categorize this product: [product details]",
  "max_tokens": 100
}

// For expiry prediction
{
  "prompt": "Predict expiry date for [product type] stored in [location]",
  "max_tokens": 50
}
```

## 🗄️ Database Indexes

### Required Indexes
```javascript
// Users collection
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });

// Products collection
db.products.createIndex({ "barcode": 1 }, { unique: true });
db.products.createIndex({ "category": 1 });
db.products.createIndex({ "name": "text", "brand": "text" });

// Inventory collection
db.inventory.createIndex({ "user_id": 1, "product_id": 1 });
db.inventory.createIndex({ "expiry_date": 1 });
db.inventory.createIndex({ "status": 1 });

// Generated Barcodes collection
db.generated_barcodes.createIndex({ "custom_barcode": 1 }, { unique: true });
db.generated_barcodes.createIndex({ "user_id": 1 });
```

## 🔒 Security Requirements

### Authentication
- JWT tokens with 24-hour expiration
- Password hashing with bcrypt (12 rounds)
- Secure token storage in HTTP-only cookies
- CSRF protection for state-changing operations

### Input Validation
- Sanitize all user inputs
- Validate barcode formats (UPC/EAN)
- Validate date formats and ranges
- File type validation for image uploads

### CORS Configuration
```python
# Flask CORS configuration
CORS(app, origins=['http://localhost:3000', 'https://yourdomain.com'])
```

## 📱 Responsive Breakpoints
```css
/* Mobile First Approach */
/* Base styles for mobile */

/* Tablet */
@media (min-width: 768px) {
  /* Tablet-specific styles */
}

/* Desktop */
@media (min-width: 1024px) {
  /* Desktop-specific styles */
}

/* Large Desktop */
@media (min-width: 1440px) {
  /* Large screen optimizations */
}
```

## 🚀 Performance Targets
- **First Contentful Paint**: < 2 seconds
- **Time to Interactive**: < 3 seconds
- **Barcode Scan Processing**: < 2 seconds
- **API Response Time**: < 500ms
- **Image Loading**: Optimized with lazy loading

This technical requirements document provides the complete specification for implementing the GrocerStock application with all necessary dependencies, file structures, and implementation details.