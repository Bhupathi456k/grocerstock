from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import re
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('email') or not data.get('password') or not data.get('username'):
            return jsonify({'error': 'Email, username, and password are required'}), 400
        
        email = data.get('email').strip().lower()
        username = data.get('username').strip()
        password = data.get('password')
        
        # Validate email format
        if not EMAIL_REGEX.match(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Check if user already exists
        if current_app.mongo.db.users.find_one({'email': email}):
            return jsonify({'error': 'Email already registered'}), 409
        
        if current_app.mongo.db.users.find_one({'username': username}):
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        user_data = {
            'email': email,
            'username': username,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.utcnow(),
            'last_login': None,
            'preferences': {
                'theme': 'light',
                'notifications': True
            }
        }
        
        # Insert user into database
        result = current_app.mongo.db.users.insert_one(user_data)
        
        # Create access token
        access_token = create_access_token(identity=str(result.inserted_id))
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': {
                'id': str(result.inserted_id),
                'email': email,
                'username': username,
                'preferences': user_data['preferences']
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        # Find user by email
        user = current_app.mongo.db.users.find_one({'email': email})
        
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update last login
        current_app.mongo.db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Create access token
        access_token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'username': user['username'],
                'preferences': user.get('preferences', {})
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        
        user = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'username': user['username'],
                'preferences': user.get('preferences', {}),
                'created_at': user['created_at'].isoformat(),
                'last_login': user.get('last_login', '').isoformat() if user.get('last_login') else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch profile', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        update_data = {}
        
        # Update username if provided
        if 'username' in data:
            new_username = data['username'].strip()
            if new_username:
                # Check if username is already taken by another user
                existing_user = current_app.mongo.db.users.find_one({
                    'username': new_username,
                    '_id': {'$ne': ObjectId(current_user_id)}
                })
                if existing_user:
                    return jsonify({'error': 'Username already taken'}), 409
                update_data['username'] = new_username
        
        # Update preferences if provided
        if 'preferences' in data:
            update_data['preferences'] = data['preferences']
        
        if update_data:
            current_app.mongo.db.users.update_one(
                {'_id': ObjectId(current_user_id)},
                {'$set': update_data}
            )
        
        # Fetch updated user
        user = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'username': user['username'],
                'preferences': user.get('preferences', {})
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        # Validate new password strength
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
        
        # Get user and verify current password
        user = current_app.mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
        
        if not user or not check_password_hash(user['password_hash'], current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        current_app.mongo.db.users.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$set': {'password_hash': generate_password_hash(new_password)}}
        )
        
        return jsonify({'message': 'Password updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to change password', 'details': str(e)}), 500