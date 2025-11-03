from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('', methods=['GET'])
@jwt_required()
def get_inventory():
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status', 'active')
        category = request.args.get('category')
        sort_by = request.args.get('sort_by', 'expiry_date')
        sort_order = 1 if request.args.get('sort_order', 'asc') == 'asc' else -1
        
        # Build query filter
        query_filter = {'user_id': ObjectId(current_user_id)}
        
        if status:
            query_filter['status'] = status
        
        if category:
            query_filter['category'] = category
        
        # Get inventory items with product details
        inventory_items = list(request.app.mongo.db.inventory.aggregate([
            {'$match': query_filter},
            {'$lookup': {
                'from': 'products',
                'localField': 'product_id',
                'foreignField': '_id',
                'as': 'product'
            }},
            {'$unwind': '$product'},
            {'$sort': {sort_by: sort_order}},
            {'$project': {
                '_id': 1,
                'quantity': 1,
                'expiry_date': 1,
                'added_date': 1,
                'location': 1,
                'notes': 1,
                'status': 1,
                'product': {
                    'id': '$product._id',
                    'name': '$product.name',
                    'brand': '$product.brand',
                    'category': '$product.category',
                    'image_url': '$product.image_url',
                    'barcode': '$product.barcode'
                }
            }}
        ]))
        
        # Calculate expiry alerts
        today = datetime.utcnow().date()
        for item in inventory_items:
            if item.get('expiry_date'):
                expiry_date = item['expiry_date'].date()
                days_remaining = (expiry_date - today).days
                item['days_remaining'] = days_remaining
                
                # Update status based on expiry
                if days_remaining < 0:
                    item['status'] = 'expired'
                elif days_remaining <= 3:
                    item['status'] = 'expiring_soon'
        
        return jsonify({
            'inventory': inventory_items,
            'count': len(inventory_items),
            'summary': get_inventory_summary(inventory_items)
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch inventory', 'details': str(e)}), 500

@inventory_bp.route('', methods=['POST'])
@jwt_required()
def add_to_inventory():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('product_id') or not data.get('quantity'):
            return jsonify({'error': 'Product ID and quantity are required'}), 400
        
        # Validate product exists
        product = request.app.mongo.db.products.find_one({'_id': ObjectId(data['product_id'])})
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Parse expiry date if provided
        expiry_date = None
        if data.get('expiry_date'):
            try:
                expiry_date = datetime.fromisoformat(data['expiry_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid expiry date format. Use ISO format.'}), 400
        
        inventory_item = {
            'user_id': ObjectId(current_user_id),
            'product_id': ObjectId(data['product_id']),
            'quantity': float(data['quantity']),
            'expiry_date': expiry_date,
            'added_date': datetime.utcnow(),
            'location': data.get('location', 'pantry'),
            'notes': data.get('notes', ''),
            'status': 'active'
        }
        
        # Check if item already exists in inventory
        existing_item = request.app.mongo.db.inventory.find_one({
            'user_id': ObjectId(current_user_id),
            'product_id': ObjectId(data['product_id']),
            'status': 'active'
        })
        
        if existing_item:
            # Update quantity if item exists
            new_quantity = existing_item['quantity'] + inventory_item['quantity']
            request.app.mongo.db.inventory.update_one(
                {'_id': existing_item['_id']},
                {'$set': {
                    'quantity': new_quantity,
                    'expiry_date': expiry_date or existing_item.get('expiry_date'),
                    'location': data.get('location', existing_item.get('location', 'pantry')),
                    'notes': data.get('notes', existing_item.get('notes', ''))
                }}
            )
            item_id = existing_item['_id']
        else:
            # Insert new item
            result = request.app.mongo.db.inventory.insert_one(inventory_item)
            item_id = result.inserted_id
        
        # Get the updated/inserted item with product details
        updated_item = request.app.mongo.db.inventory.aggregate([
            {'$match': {'_id': item_id}},
            {'$lookup': {
                'from': 'products',
                'localField': 'product_id',
                'foreignField': '_id',
                'as': 'product'
            }},
            {'$unwind': '$product'},
            {'$project': {
                '_id': 1,
                'quantity': 1,
                'expiry_date': 1,
                'added_date': 1,
                'location': 1,
                'notes': 1,
                'status': 1,
                'product': {
                    'id': '$product._id',
                    'name': '$product.name',
                    'brand': '$product.brand',
                    'category': '$product.category',
                    'image_url': '$product.image_url',
                    'barcode': '$product.barcode'
                }
            }}
        ]).next()
        
        return jsonify({
            'message': 'Item added to inventory successfully',
            'inventory_item': updated_item
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to add item to inventory', 'details': str(e)}), 500

@inventory_bp.route('/<item_id>', methods=['PUT'])
@jwt_required()
def update_inventory_item(item_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        update_data = {}
        allowed_fields = ['quantity', 'expiry_date', 'location', 'notes', 'status']
        
        for field in allowed_fields:
            if field in data:
                if field == 'expiry_date' and data[field]:
                    try:
                        update_data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({'error': 'Invalid expiry date format. Use ISO format.'}), 400
                else:
                    update_data[field] = data[field]
        
        if update_data:
            result = request.app.mongo.db.inventory.update_one(
                {'_id': ObjectId(item_id), 'user_id': ObjectId(current_user_id)},
                {'$set': update_data}
            )
            
            if result.matched_count == 0:
                return jsonify({'error': 'Inventory item not found'}), 404
        
        # Return updated item
        updated_item = request.app.mongo.db.inventory.aggregate([
            {'$match': {'_id': ObjectId(item_id)}},
            {'$lookup': {
                'from': 'products',
                'localField': 'product_id',
                'foreignField': '_id',
                'as': 'product'
            }},
            {'$unwind': '$product'},
            {'$project': {
                '_id': 1,
                'quantity': 1,
                'expiry_date': 1,
                'added_date': 1,
                'location': 1,
                'notes': 1,
                'status': 1,
                'product': {
                    'id': '$product._id',
                    'name': '$product.name',
                    'brand': '$product.brand',
                    'category': '$product.category',
                    'image_url': '$product.image_url',
                    'barcode': '$product.barcode'
                }
            }}
        ]).next()
        
        return jsonify({
            'message': 'Inventory item updated successfully',
            'inventory_item': updated_item
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to update inventory item', 'details': str(e)}), 500

@inventory_bp.route('/<item_id>', methods=['DELETE'])
@jwt_required()
def delete_inventory_item(item_id):
    try:
        current_user_id = get_jwt_identity()
        
        result = request.app.mongo.db.inventory.delete_one({
            '_id': ObjectId(item_id),
            'user_id': ObjectId(current_user_id)
        })
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Inventory item not found'}), 404
        
        return jsonify({'message': 'Inventory item deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete inventory item', 'details': str(e)}), 500

@inventory_bp.route('/expiring', methods=['GET'])
@jwt_required()
def get_expiring_items():
    try:
        current_user_id = get_jwt_identity()
        days = int(request.args.get('days', 7))
        
        threshold_date = datetime.utcnow() + timedelta(days=days)
        
        expiring_items = list(request.app.mongo.db.inventory.aggregate([
            {'$match': {
                'user_id': ObjectId(current_user_id),
                'status': 'active',
                'expiry_date': {'$lte': threshold_date, '$gte': datetime.utcnow()}
            }},
            {'$lookup': {
                'from': 'products',
                'localField': 'product_id',
                'foreignField': '_id',
                'as': 'product'
            }},
            {'$unwind': '$product'},
            {'$sort': {'expiry_date': 1}},
            {'$project': {
                '_id': 1,
                'quantity': 1,
                'expiry_date': 1,
                'location': 1,
                'product': {
                    'id': '$product._id',
                    'name': '$product.name',
                    'brand': '$product.brand',
                    'category': '$product.category',
                    'image_url': '$product.image_url'
                }
            }}
        ]))
        
        return jsonify({
            'expiring_items': expiring_items,
            'count': len(expiring_items),
            'threshold_days': days
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch expiring items', 'details': str(e)}), 500

def get_inventory_summary(inventory_items):
    """Generate inventory summary statistics"""
    total_items = len(inventory_items)
    total_quantity = sum(item.get('quantity', 0) for item in inventory_items)
    
    # Count by category
    categories = {}
    for item in inventory_items:
        category = item.get('product', {}).get('category', 'Uncategorized')
        categories[category] = categories.get(category, 0) + 1
    
    # Count by status
    status_counts = {}
    for item in inventory_items:
        status = item.get('status', 'active')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Expiring soon count (within 3 days)
    today = datetime.utcnow().date()
    expiring_soon = 0
    for item in inventory_items:
        if item.get('expiry_date'):
            expiry_date = item['expiry_date'].date()
            days_remaining = (expiry_date - today).days
            if 0 <= days_remaining <= 3:
                expiring_soon += 1
    
    return {
        'total_items': total_items,
        'total_quantity': total_quantity,
        'categories': categories,
        'status_counts': status_counts,
        'expiring_soon': expiring_soon
    }