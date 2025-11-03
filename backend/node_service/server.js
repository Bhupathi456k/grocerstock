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
    origin: ["http://localhost:3000", "http://localhost:5000"],
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

mongoose.connection.on('connected', () => {
  console.log('Connected to MongoDB');
});

mongoose.connection.on('error', (err) => {
  console.error('MongoDB connection error:', err);
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'node-realtime-service',
    timestamp: new Date().toISOString()
  });
});

// Real-time inventory updates via WebSocket
const connectedUsers = new Map();

io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  // Join user-specific room for inventory updates
  socket.on('join-inventory', (userId) => {
    socket.join(`inventory-${userId}`);
    connectedUsers.set(socket.id, userId);
    console.log(`User ${userId} joined inventory room`);
  });

  // Handle inventory updates
  socket.on('inventory-update', (data) => {
    const userId = connectedUsers.get(socket.id);
    if (userId) {
      // Broadcast to all connected clients in the same user room
      io.to(`inventory-${userId}`).emit('inventory-changed', data);
      console.log(`Inventory update broadcasted for user ${userId}`);
    }
  });

  // Handle expiry notifications subscription
  socket.on('subscribe-expiry', (userId) => {
    socket.join(`expiry-${userId}`);
    console.log(`User ${userId} subscribed to expiry notifications`);
  });

  socket.on('disconnect', () => {
    const userId = connectedUsers.get(socket.id);
    if (userId) {
      console.log(`User ${userId} disconnected`);
      connectedUsers.delete(socket.id);
    }
  });
});

// AI Integration Routes
app.post('/api/ai/categorize', async (req, res) => {
  try {
    const { productData } = req.body;

    if (!productData || !productData.name) {
      return res.status(400).json({ error: 'Product data with name is required' });
    }

    // Simulate AI categorization (replace with actual DeepSeek API call)
    const category = await categorizeProduct(productData);

    res.json({
      success: true,
      category: category,
      confidence: 'high'
    });
  } catch (error) {
    console.error('AI categorization error:', error);
    res.status(500).json({
      success: false,
      error: 'Categorization failed',
      details: error.message
    });
  }
});

app.post('/api/ai/suggestions', async (req, res) => {
  try {
    const { inventory, preferences } = req.body;

    if (!inventory) {
      return res.status(400).json({ error: 'Inventory data is required' });
    }

    // Simulate AI suggestions (replace with actual DeepSeek API call)
    const suggestions = await generateSuggestions(inventory, preferences);

    res.json({
      success: true,
      suggestions: suggestions
    });
  } catch (error) {
    console.error('AI suggestions error:', error);
    res.status(500).json({
      success: false,
      error: 'Suggestions generation failed',
      details: error.message
    });
  }
});

// Mock AI functions (replace with actual DeepSeek API integration)
async function categorizeProduct(productData) {
  // This would be replaced with actual DeepSeek API call
  const categories = [
    'Fruits & Vegetables',
    'Dairy & Eggs', 
    'Meat & Seafood',
    'Bakery & Bread',
    'Pantry & Dry Goods',
    'Beverages',
    'Frozen Foods',
    'Snacks & Sweets',
    'Household & Cleaning',
    'Personal Care'
  ];

  // Simple keyword-based categorization for demo
  const name = productData.name.toLowerCase();
  
  if (name.includes('apple') || name.includes('banana') || name.includes('vegetable')) {
    return 'Fruits & Vegetables';
  } else if (name.includes('milk') || name.includes('cheese') || name.includes('egg')) {
    return 'Dairy & Eggs';
  } else if (name.includes('meat') || name.includes('chicken') || name.includes('fish')) {
    return 'Meat & Seafood';
  } else if (name.includes('bread') || name.includes('cake') || name.includes('pastry')) {
    return 'Bakery & Bread';
  } else {
    return 'Pantry & Dry Goods';
  }
}

async function generateSuggestions(inventory, preferences = {}) {
  // This would be replaced with actual DeepSeek API call
  const expiringSoon = inventory.filter(item => {
    if (!item.expiry_date) return false;
    const expiry = new Date(item.expiry_date);
    const today = new Date();
    const daysDiff = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
    return daysDiff <= 3 && daysDiff >= 0;
  });

  const lowStock = inventory.filter(item => item.quantity <= 2);

  return {
    expiring_soon: expiringSoon.map(item => ({
      product: item.product.name,
      expiry_date: item.expiry_date,
      days_remaining: Math.ceil((new Date(item.expiry_date) - new Date()) / (1000 * 60 * 60 * 24))
    })),
    low_stock: lowStock.map(item => ({
      product: item.product.name,
      current_quantity: item.quantity,
      suggestion: 'Consider restocking soon'
    })),
    recipe_suggestions: [
      {
        name: 'Quick Pantry Meal',
        description: 'Use items that are expiring soon',
        ingredients: expiringSoon.slice(0, 3).map(item => item.product.name)
      }
    ]
  };
}

// Expiry notification service
setInterval(async () => {
  try {
    const now = new Date();
    const sevenDaysFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

    const expiringItems = await mongoose.connection.db.collection('inventory')
      .aggregate([
        {
          $match: {
            expiry_date: { $lte: sevenDaysFromNow, $gte: now },
            status: 'active'
          }
        },
        {
          $lookup: {
            from: 'products',
            localField: 'product_id',
            foreignField: '_id',
            as: 'product'
          }
        },
        {
          $unwind: '$product'
        },
        {
          $lookup: {
            from: 'users',
            localField: 'user_id',
            foreignField: '_id',
            as: 'user'
          }
        },
        {
          $unwind: '$user'
        }
      ]).toArray();

    expiringItems.forEach(item => {
      const daysRemaining = Math.ceil((item.expiry_date - now) / (1000 * 60 * 60 * 24));
      
      io.to(`expiry-${item.user_id}`).emit('expiry-alert', {
        product: item.product.name,
        expiry_date: item.expiry_date,
        days_remaining: daysRemaining,
        alert_level: daysRemaining <= 1 ? 'critical' : daysRemaining <= 3 ? 'warning' : 'info'
      });
    });

  } catch (error) {
    console.error('Expiry notification error:', error);
  }
}, 60 * 60 * 1000); // Run every hour

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Node.js real-time service running on port ${PORT}`);
});