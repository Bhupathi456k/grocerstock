from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import hashlib
import time
from datetime import datetime

barcode_bp = Blueprint('barcode', __name__)

@barcode_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_barcode():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        product_name = data.get('product_name')
        category = data.get('category', '')
        weight = data.get('weight', '')
        
        if not product_name:
            return jsonify({'error': 'Product name is required'}), 400
        
        # Generate unique identifier for custom barcode
        unique_id = hashlib.md5(
            f"{product_name}{category}{weight}{time.time()}".encode()
        ).hexdigest()[:12]
        
        # Generate barcode image
        try:
            barcode_class = barcode.get_barcode_class('code128')
            barcode_instance = barcode_class(unique_id, writer=ImageWriter())
            
            # Save to bytes buffer
            buffer = BytesIO()
            barcode_instance.write(buffer)
            buffer.seek(0)
        except Exception as e:
            return jsonify({'error': 'Failed to generate barcode image', 'details': str(e)}), 500
        
        # Save barcode data to database
        barcode_data = {
            'custom_barcode': unique_id,
            'product_name': product_name.strip(),
            'category': category.strip(),
            'weight': weight.strip(),
            'created_at': datetime.utcnow(),
            'user_id': ObjectId(current_user_id)
        }
        
        # Check if barcode already exists (unlikely but possible)
        existing_barcode = request.app.mongo.db.generated_barcodes.find_one({'custom_barcode': unique_id})
        if existing_barcode:
            # Regenerate with different timestamp
            unique_id = hashlib.md5(
                f"{product_name}{category}{weight}{time.time()}".encode()
            ).hexdigest()[:12]
            barcode_data['custom_barcode'] = unique_id
        
        result = request.app.mongo.db.generated_barcodes.insert_one(barcode_data)
        
        return jsonify({
            'success': True,
            'barcode_data': {
                'id': str(result.inserted_id),
                'custom_barcode': unique_id,
                'product_name': product_name,
                'category': category,
                'weight': weight,
                'created_at': barcode_data['created_at'].isoformat()
            },
            'image_url': f'/api/barcode/{unique_id}/image'
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate barcode', 'details': str(e)}), 500

@barcode_bp.route('/<barcode_id>/image', methods=['GET'])
def get_barcode_image(barcode_id):
    try:
        # Generate barcode image on the fly
        barcode_class = barcode.get_barcode_class('code128')
        barcode_instance = barcode_class(barcode_id, writer=ImageWriter())
        
        buffer = BytesIO()
        barcode_instance.write(buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='image/png',
            as_attachment=False,
            download_name=f'barcode_{barcode_id}.png'
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate barcode image', 'details': str(e)}), 500

@barcode_bp.route('/<barcode_id>/download', methods=['GET'])
def download_barcode_image(barcode_id):
    try:
        # Generate barcode image on the fly
        barcode_class = barcode.get_barcode_class('code128')
        barcode_instance = barcode_class(barcode_id, writer=ImageWriter())
        
        buffer = BytesIO()
        barcode_instance.write(buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'barcode_{barcode_id}.png'
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate barcode image', 'details': str(e)}), 500

@barcode_bp.route('/my-barcodes', methods=['GET'])
@jwt_required()
def get_my_barcodes():
    try:
        current_user_id = get_jwt_identity()
        
        barcodes = list(request.app.mongo.db.generated_barcodes.find(
            {'user_id': ObjectId(current_user_id)},
            {'user_id': 0}  # Exclude user_id from response
        ).sort('created_at', -1))
        
        formatted_barcodes = []
        for barcode in barcodes:
            formatted_barcodes.append({
                'id': str(barcode['_id']),
                'custom_barcode': barcode['custom_barcode'],
                'product_name': barcode['product_name'],
                'category': barcode.get('category', ''),
                'weight': barcode.get('weight', ''),
                'created_at': barcode['created_at'].isoformat(),
                'image_url': f'/api/barcode/{barcode["custom_barcode"]}/image',
                'download_url': f'/api/barcode/{barcode["custom_barcode"]}/download'
            })
        
        return jsonify({
            'barcodes': formatted_barcodes,
            'count': len(formatted_barcodes)
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch barcodes', 'details': str(e)}), 500

@barcode_bp.route('/<barcode_id>', methods=['GET'])
@jwt_required()
def get_barcode_details(barcode_id):
    try:
        current_user_id = get_jwt_identity()
        
        barcode_data = request.app.mongo.db.generated_barcodes.find_one({
            'custom_barcode': barcode_id,
            'user_id': ObjectId(current_user_id)
        })
        
        if not barcode_data:
            return jsonify({'error': 'Barcode not found'}), 404
        
        return jsonify({
            'barcode': {
                'id': str(barcode_data['_id']),
                'custom_barcode': barcode_data['custom_barcode'],
                'product_name': barcode_data['product_name'],
                'category': barcode_data.get('category', ''),
                'weight': barcode_data.get('weight', ''),
                'created_at': barcode_data['created_at'].isoformat(),
                'image_url': f'/api/barcode/{barcode_data["custom_barcode"]}/image',
                'download_url': f'/api/barcode/{barcode_data["custom_barcode"]}/download'
            }
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch barcode details', 'details': str(e)}), 500

@barcode_bp.route('/<barcode_id>', methods=['DELETE'])
@jwt_required()
def delete_barcode(barcode_id):
    try:
        current_user_id = get_jwt_identity()
        
        result = request.app.mongo.db.generated_barcodes.delete_one({
            'custom_barcode': barcode_id,
            'user_id': ObjectId(current_user_id)
        })
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Barcode not found'}), 404
        
        return jsonify({'message': 'Barcode deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete barcode', 'details': str(e)}), 500

@barcode_bp.route('/validate/<barcode>', methods=['GET'])
def validate_barcode(barcode):
    """Validate barcode format"""
    try:
        # Check if it's a standard barcode format
        if len(barcode) in [12, 13] and barcode.isdigit():
            # UPC (12 digits) or EAN-13 (13 digits)
            return jsonify({
                'valid': True,
                'format': 'UPC' if len(barcode) == 12 else 'EAN-13',
                'message': 'Valid UPC/EAN barcode'
            })
        elif len(barcode) <= 20 and all(c.isalnum() or c == '-' for c in barcode):
            # Code 128 (alphanumeric, max 20 characters)
            return jsonify({
                'valid': True,
                'format': 'Code 128',
                'message': 'Valid Code 128 barcode'
            })
        else:
            return jsonify({
                'valid': False,
                'message': 'Invalid barcode format'
            })
            
    except Exception as e:
        return jsonify({'error': 'Validation failed', 'details': str(e)}), 500