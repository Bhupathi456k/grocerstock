#!/usr/bin/env python3
"""
Test script to diagnose Flask app startup issues
"""
import os
import sys
import traceback

def test_flask_startup():
    print("Testing Flask app startup...")
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(__file__))
    
    try:
        # Test basic imports
        print("1. Testing basic imports...")
        from flask import Flask
        from flask_pymongo import PyMongo
        from flask_jwt_extended import JWTManager
        from flask_cors import CORS
        from datetime import datetime, timedelta
        from dotenv import load_dotenv
        print("OK - Basic imports successful")
        
        # Test route imports
        print("2. Testing route imports...")
        from routes.auth import auth_bp
        from routes.products import products_bp
        from routes.inventory import inventory_bp
        from routes.barcode import barcode_bp
        print("OK - Route imports successful")
        
        # Test app creation
        print("3. Testing app creation...")
        app = Flask(__name__)
        
        # Test configuration
        print("4. Testing configuration...")
        load_dotenv()
        app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/grocerstock')
        app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
        app.config['OPEN_FOOD_FACTS_API_URL'] = os.getenv('OPEN_FOOD_FACTS_API_URL', 'https://world.openfoodfacts.org/api/v0')
        print("OK - Configuration successful")
        
        # Test extensions
        print("5. Testing extensions...")
        mongo = PyMongo(app)
        jwt = JWTManager(app)
        CORS(app)
        print("OK - Extensions initialized")
        
        # Test blueprint registration
        print("6. Testing blueprint registration...")
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(products_bp, url_prefix='/api/products')
        app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
        app.register_blueprint(barcode_bp, url_prefix='/api/barcode')
        print("OK - Blueprint registration successful")
        
        # Test route definitions
        print("7. Testing route definitions...")
        with app.app_context():
            # Check if routes are properly registered
            rules = []
            for rule in app.url_map.iter_rules():
                rules.append(str(rule))
            
            print(f"OK - Found {len(rules)} routes registered")
            print("Sample routes:")
            for rule in rules[:5]:  # Show first 5 routes
                print(f"  - {rule}")
        
        print("\nSUCCESS - Flask app startup test PASSED!")
        return True
        
    except Exception as e:
        print(f"\nFAILED - Flask app startup test FAILED!")
        print(f"Error: {e}")
        print("\nTraceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_flask_startup()
    sys.exit(0 if success else 1)