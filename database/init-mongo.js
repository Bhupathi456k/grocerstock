db = db.getSiblingDB('grocerstock');

// Create collections
db.createCollection('users');
db.createCollection('products');
db.createCollection('inventory');
db.createCollection('generated_barcodes');

// Create indexes for users collection
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "created_at": -1 });

// Create indexes for products collection
db.products.createIndex({ "barcode": 1 }, { unique: true });
db.products.createIndex({ "category": 1 });
db.products.createIndex({ "name": "text", "brand": "text" });
db.products.createIndex({ "created_at": -1 });

// Create indexes for inventory collection
db.inventory.createIndex({ "user_id": 1, "product_id": 1 });
db.inventory.createIndex({ "expiry_date": 1 });
db.inventory.createIndex({ "status": 1 });
db.inventory.createIndex({ "user_id": 1, "expiry_date": 1 });
db.inventory.createIndex({ "created_at": -1 });

// Create indexes for generated_barcodes collection
db.generated_barcodes.createIndex({ "custom_barcode": 1 }, { unique: true });
db.generated_barcodes.createIndex({ "user_id": 1 });
db.generated_barcodes.createIndex({ "created_at": -1 });

// Insert sample categories for reference
db.categories.insertMany([
  { name: "Fruits & Vegetables", description: "Fresh fruits and vegetables" },
  { name: "Dairy & Eggs", description: "Milk, cheese, eggs, and dairy products" },
  { name: "Meat & Seafood", description: "Fresh meat, poultry, and seafood" },
  { name: "Bakery & Bread", description: "Bread, pastries, and baked goods" },
  { name: "Pantry & Dry Goods", description: "Canned goods, pasta, rice, etc." },
  { name: "Beverages", description: "Drinks, juices, water, etc." },
  { name: "Frozen Foods", description: "Frozen vegetables, meals, ice cream" },
  { name: "Snacks & Sweets", description: "Chips, cookies, candy, etc." },
  { name: "Household & Cleaning", description: "Cleaning supplies, paper products" },
  { name: "Personal Care", description: "Toiletries, hygiene products" }
]);

print('GrocerStock database initialized successfully');
print('Collections created: users, products, inventory, generated_barcodes, categories');
print('Indexes created for optimal performance');