from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import requests
from datetime import datetime

products_bp = Blueprint('products', __name__)

@products_bp.route('/search', methods=['GET'])
@jwt_required()
def search_products():
    try:
        barcode = request.args.get('barcode')
        query = request.args.get('query')
        
        if not barcode and not query:
            return jsonify({'error': 'Either barcode or query parameter is required'}), 400
        
        if barcode:
            # Search by barcode
            return search_by_barcode(barcode)
        else:
            # Search by text query
            return search_by_query(query)
            
    except Exception as e:
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

def search_by_barcode(barcode):
    """Search for product by barcode"""
    # First check local database
    product = request.app.mongo.db.products.find_one({'barcode': barcode})
    
    if product:
        return jsonify({
            'found': True,
            'source': 'local',
            'product': format_product(product)
        })
    
    # If not found locally, query Open Food Facts
    try:
        response = requests.get(
            f'{request.app.config["OPEN_FOOD_FACTS_API_URL"]}/product/{barcode}.json',
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 1 and data.get('product'):
                product_data = normalize_open_food_facts_product(data['product'])
                
                # Save to local database for future use
                request.app.mongo.db.products.insert_one(product_data)
                
                return jsonify({
                    'found': True,
                    'source': 'open_food_facts',
                    'product': format_product(product_data)
                })
        
        return jsonify({
            'found': False,
            'message': 'Product not found in database'
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to query Open Food Facts API', 'details': str(e)}), 500

def search_by_query(query):
    """Search for products by text query"""
    # Search in local database
    products = list(request.app.mongo.db.products.find({
        '$or': [
            {'name': {'$regex': query, '$options': 'i'}},
            {'brand': {'$regex': query, '$options': 'i'}},
            {'category': {'$regex': query, '$options': 'i'}}
        ]
    }).limit(20))
    
    return jsonify({
        'found': len(products) > 0,
        'products': [format_product(product) for product in products],
        'count': len(products)
    })

@products_bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Product name is required'}), 400
        
        # Generate a unique ID for custom products
        if not data.get('barcode'):
            import hashlib
            import time
            data['barcode'] = hashlib.md5(
                f"{data['name']}{data.get('brand', '')}{time.time()}".encode()
            ).hexdigest()[:12]
        
        product_data = {
            'barcode': data.get('barcode'),
            'name': data['name'].strip(),
            'brand': data.get('brand', '').strip(),
            'category': data.get('category', 'Uncategorized').strip(),
            'image_url': data.get('image_url'),
            'quantity': data.get('quantity', ''),
            'nutritional_info': data.get('nutritional_info', {}),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'created_by': get_jwt_identity()
        }
        
        # Check if product with same barcode already exists
        existing_product = request.app.mongo.db.products.find_one({'barcode': product_data['barcode']})
        if existing_product:
            return jsonify({
                'error': 'Product with this barcode already exists',
                'product': format_product(existing_product)
            }), 409
        
        result = request.app.mongo.db.products.insert_one(product_data)
        
        return jsonify({
            'message': 'Product created successfully',
            'product': format_product(product_data)
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create product', 'details': str(e)}), 500

@products_bp.route('/<product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    try:
        product = request.app.mongo.db.products.find_one({'_id': ObjectId(product_id)})
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({'product': format_product(product)})
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch product', 'details': str(e)}), 500

@products_bp.route('/<product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        update_data = {}
        
        # Only allow updating certain fields
        allowed_fields = ['name', 'brand', 'category', 'quantity', 'nutritional_info', 'image_url']
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            
            result = request.app.mongo.db.products.update_one(
                {'_id': ObjectId(product_id)},
                {'$set': update_data}
            )
            
            if result.matched_count == 0:
                return jsonify({'error': 'Product not found'}), 404
        
        # Return updated product
        product = request.app.mongo.db.products.find_one({'_id': ObjectId(product_id)})
        return jsonify({
            'message': 'Product updated successfully',
            'product': format_product(product)
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to update product', 'details': str(e)}), 500

@products_bp.route('/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    try:
        result = request.app.mongo.db.products.delete_one({'_id': ObjectId(product_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({'message': 'Product deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete product', 'details': str(e)}), 500

@products_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    try:
        categories = list(request.app.mongo.db.categories.find({}, {'_id': 0}))
        return jsonify({'categories': categories})
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch categories', 'details': str(e)}), 500

def normalize_open_food_facts_product(product_data):
    """Normalize Open Food Facts product data"""
    return {
        'barcode': product_data.get('code', ''),
        'name': product_data.get('product_name', 'Unknown Product').strip(),
        'brand': product_data.get('brands', 'Unknown Brand').strip(),
        'category': product_data.get('categories', 'Uncategorized').strip(),
        'image_url': product_data.get('image_url'),
        'quantity': product_data.get('quantity', ''),
        'nutritional_info': product_data.get('nutriments', {}),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'source': 'open_food_facts'
    }

def format_product(product):
    """Format product data for response"""
    return {
        'id': str(product['_id']),
        'barcode': product.get('barcode', ''),
        'name': product.get('name', ''),
        'brand': product.get('brand', ''),
        'category': product.get('category', ''),
        'image_url': product.get('image_url'),
        'quantity': product.get('quantity', ''),
        'nutritional_info': product.get('nutritional_info', {}),
        'created_at': product.get('created_at', '').isoformat() if product.get('created_at') else None,
        'updated_at': product.get('updated_at', '').isoformat() if product.get('updated_at') else None,
        'source': product.get('source', 'local')
    }