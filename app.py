from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
import uuid
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_jwt_secret'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Khởi tạo extensions
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Tạo thư mục uploads nếu chưa có
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Kết nối MongoDB
try:
    client = MongoClient("mongodb+srv://admin:971012@admin.7oi2tx6.mongodb.net/?retryWrites=true&w=majority&appName=admin")
    db = client.web243  # Database name
    print("✅ Kết nối MongoDB Atlas thành công!")
except Exception as e:
    print(f"❌ Lỗi kết nối MongoDB Atlas: {e}")
    db = None

# Collections
users_collection = db.users if db is not None else None
categories_collection = db.categories if db is not None else None
products_collection = db.products if db is not None else None
transactions_collection = db.transactions if db is not None else None
orders_collection = db.orders if db is not None else None
topup_cards_collection = db.topup_cards if db is not None else None
wallet_topups_collection = db.wallet_topups if db is not None else None
bank_settings_collection = db.bank_settings if db is not None else None
articles_collection = db.articles if db is not None else None

# Momo payment configuration
PARTNER_CODE = 'MOMO...'
ACCESS_KEY = '...'
SECRET_KEY = '...'
MOMO_ENDPOINT = 'https://test-payment.momo.vn/v2/gateway/api/create'

# Helper functions
def generate_id():
    return str(ObjectId())

def convert_objectid(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not all([email, username, password]):
        return jsonify({'message': 'Thiếu thông tin đăng ký'}), 400

    # Kiểm tra user đã tồn tại
    existing_user = users_collection.find_one({'username': username})
    if existing_user:
        return jsonify({'message': 'Tài khoản đã tồn tại!'}), 400

    # Tạo user mới
    hashed_password = generate_password_hash(password)
    new_user = {
        '_id': generate_id(),
        'email': email,
        'username': username,
        'password': hashed_password,
        'role': 'User',
        'balance': 0,
        'total_topup': 0,
        'created_at': datetime.utcnow()
    }

    try:
        users_collection.insert_one(new_user)
        return jsonify({'message': 'Đăng ký thành công!'}), 201
    except Exception as e:
        return jsonify({'message': 'Lỗi hệ thống, vui lòng thử lại sau.'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not all([username, password]):
        return jsonify({'message': 'Thiếu thông tin đăng nhập'}), 400

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'message': 'Tài khoản không tồn tại'}), 401

    if user['password'] != password:
        return jsonify({'message': 'Sai tài khoản hoặc mật khẩu'}), 401

    # Tạo JWT token
    access_token = create_access_token(
        identity=str(user['_id'])
    )

    return jsonify({
        'message': 'Đăng nhập thành công',
        'token': access_token,
        'role': user['role'],
        'username': user['username'],
        'balance': user['balance'],
        'totalTopup': user.get('totalTopup', 0)
    }), 200

# Category routes
@app.route('/api/categories', methods=['GET'])
def get_categories():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        # Kiểm tra xem có phải admin request không
        show_all = request.args.get('admin', 'false').lower() == 'true'
        
        if show_all:
            # Admin có thể xem tất cả categories
            categories = list(categories_collection.find())
        else:
            # User chỉ thấy categories active
            categories = list(categories_collection.find({'status': 'active'}))
        
        result = []
        for category in categories:
            result.append({
                'id': str(category['_id']),
                'name': category['name'],
                'order': category.get('order', 0),
                'status': category.get('status', 'active')
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy categories: {str(e)}'}), 500

@app.route('/api/categories', methods=['POST'])
def create_category():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Tên danh mục là bắt buộc'}), 400

    try:
        new_category = {
            '_id': generate_id(),
            'name': name,
            'order': 0,
            'status': 'active'
        }
        categories_collection.insert_one(new_category)
        return jsonify({
            'id': str(new_category['_id']),
            'name': new_category['name'],
            'order': new_category['order'],
            'status': new_category['status']
        }), 201
    except Exception as e:
        return jsonify({'error': f'Lỗi khi tạo category: {str(e)}'}), 400

@app.route('/api/categories/<category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    # Chỉ admin mới có quyền cập nhật category
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền cập nhật danh mục'}), 403
        
    try:
        data = request.get_json()
        name = data.get('name')
        status = data.get('status')
        
        if not name:
            return jsonify({'error': 'Tên danh mục là bắt buộc'}), 400
        
        # Tìm category bằng ID (có thể là string hoặc ObjectId)
        category = categories_collection.find_one({'_id': category_id})
        if not category:
            # Thử tìm bằng ObjectId nếu category_id là string
            try:
                from bson import ObjectId
                category_object_id = ObjectId(category_id)
                category = categories_collection.find_one({'_id': category_object_id})
            except:
                pass
        
        if not category:
            return jsonify({'message': 'Không tìm thấy danh mục'}), 404
        
        # Cập nhật thông tin
        update_data = {}
        if name:
            update_data['name'] = name
        if status:
            update_data['status'] = status
        
        # Cập nhật category
        result = categories_collection.update_one(
            {'_id': category_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({'message': f'Cập nhật danh mục thành công'}), 200
        else:
            return jsonify({'message': 'Không có thay đổi nào'}), 200
            
    except Exception as e:
        return jsonify({'error': f'Lỗi khi cập nhật category: {str(e)}'}), 500

@app.route('/api/categories/<category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    # Chỉ admin mới có quyền xóa category
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền xóa danh mục'}), 403
        
    try:
        # Tìm category bằng ID (có thể là string hoặc ObjectId)
        category = categories_collection.find_one({'_id': category_id})
        if not category:
            # Thử tìm bằng ObjectId nếu category_id là string
            try:
                from bson import ObjectId
                category_object_id = ObjectId(category_id)
                category = categories_collection.find_one({'_id': category_object_id})
            except:
                pass
        
        if not category:
            return jsonify({'message': 'Không tìm thấy danh mục'}), 404
        
        # Tìm tất cả sản phẩm trong category này (sử dụng category_id string)
        products_in_category = list(products_collection.find({'category_id': category_id}))
        products_count = len(products_in_category)
        
        # Xóa tất cả ảnh của sản phẩm trong category
        deleted_images = 0
        for product in products_in_category:
            if product.get('image'):
                image_path = product['image']
                # Loại bỏ /uploads/ prefix để lấy tên file
                if image_path.startswith('/uploads/'):
                    filename = image_path[9:]  # Bỏ '/uploads/'
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    try:
                        if os.path.exists(full_path):
                            os.remove(full_path)
                            deleted_images += 1
                            print(f"✅ Đã xóa ảnh: {filename}")
                    except Exception as e:
                        print(f"❌ Lỗi khi xóa ảnh {filename}: {str(e)}")
        
        # Xóa tất cả sản phẩm trong category
        if products_count > 0:
            delete_result = products_collection.delete_many({'category_id': category_id})
            print(f"✅ Đã xóa {delete_result.deleted_count} sản phẩm")
        
        # Xóa category
        category_result = categories_collection.delete_one({'_id': category_id})
        
        if category_result.deleted_count > 0:
            message = f'Xóa danh mục thành công!'
            if products_count > 0:
                message += f' Đã xóa {products_count} sản phẩm'
            if deleted_images > 0:
                message += f' và {deleted_images} ảnh'
            message += '.'
            
            return jsonify({'message': message}), 200
        else:
            return jsonify({'message': 'Không thể xóa danh mục'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Lỗi khi xóa category: {str(e)}'}), 500

# Product routes
@app.route('/api/products', methods=['GET'])
def get_products():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        # Kiểm tra nếu có filter theo category_id
        category_id = request.args.get('category_id')
        
        if category_id:
            # Lấy sản phẩm theo category_id cụ thể
            products = list(products_collection.find({'category_id': category_id}))
        else:
            # Lấy tất cả sản phẩm từ danh mục active
            active_categories = list(categories_collection.find({'status': 'active'}))
            active_category_ids = [str(cat['_id']) for cat in active_categories]
            products = list(products_collection.find({'category_id': {'$in': active_category_ids}}))
        
        result = []
        for product in products:
            category = categories_collection.find_one({'_id': product['category_id']})
            result.append({
                '_id': str(product['_id']),
                'name': product['name'],
                'price': product['price'],
                'category_id': str(product['category_id']),
                'category_name': category['name'] if category else '',
                'image': product.get('image'),
                'sale': product.get('sale'),
                'link_demo': product.get('link_demo'),
                'link_tai': product.get('link_tai'),
                'name_key': product.get('name_key'),
                'content': product.get('content'),
                'created_at': product['created_at'].isoformat()
            })
            # Debug: log image path
            print(f"Product {product['name']}: image = {product.get('image')}")
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy products: {str(e)}'}), 500

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    print(f"🔍 Looking for product with ID: {product_id}")
    
    try:
        # Try to find product by string first (since IDs are stored as strings)
        product = products_collection.find_one({'_id': product_id})
        print(f"✅ Found product with string ID: {product is not None}")
        
        # If not found, try ObjectId
        if not product:
            try:
                product = products_collection.find_one({'_id': ObjectId(product_id)})
                print(f"✅ Found product with ObjectId: {product is not None}")
            except Exception as e:
                print(f"❌ ObjectId conversion failed: {e}")
        
        if not product:
            # Debug: show all products
            all_products = list(products_collection.find())
            print(f"📦 Total products in DB: {len(all_products)}")
            for p in all_products:
                print(f"   - ID: {p['_id']} (type: {type(p['_id'])}) - Name: {p['name']}")
                # Check if this is the product we're looking for
                if str(p['_id']) == product_id:
                    print(f"   ✅ FOUND MATCHING PRODUCT!")
                else:
                    print(f"   ❌ No match: {str(p['_id'])} != {product_id}")
            return jsonify({'message': 'Sản phẩm không tồn tại'}), 404
        
        # Get category info
        category = None
        if 'category_id' in product:
            try:
                category = categories_collection.find_one({'_id': product['category_id']})
            except:
                # If category_id is string, try to find by string
                category = categories_collection.find_one({'_id': product['category_id']})
        
        result = {
            '_id': str(product['_id']),
            'name': product['name'],
            'price': product['price'],
            'category_id': str(product['category_id']) if 'category_id' in product else None,
            'category_name': category['name'] if category else '',
            'image': product.get('image'),
            'sale': product.get('sale'),
            'demo_link': product.get('link_demo'),
            'download_link': product.get('link_tai'),
            'key': product.get('name_key'),
            'description': product.get('content'),
            'created_at': product['created_at'].isoformat() if 'created_at' in product else None
        }
        
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Lỗi khi lấy chi tiết sản phẩm: {e}")
        return jsonify({'message': 'Lỗi khi lấy chi tiết sản phẩm'}), 500

@app.route('/api/products', methods=['POST'])
def create_product():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        name = request.form.get('name')
        price = float(request.form.get('price'))
        category_id = request.form.get('categoryId')
        
        if not all([name, price, category_id]):
            return jsonify({'error': 'Thiếu thông tin sản phẩm'}), 400

        # Xử lý upload file
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Tạo tên file unique
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                image_path = f"/uploads/{unique_filename}"

        new_product = {
            '_id': generate_id(),
            'name': name,
            'price': price,
            'category_id': category_id,
            'image': image_path,
            'sale': request.form.get('sale'),
            'link_demo': request.form.get('linkDemo'),
            'link_tai': request.form.get('linkTai'),
            'name_key': request.form.get('nameKey'),
            'content': request.form.get('content'),
            'created_at': datetime.utcnow()
        }

        products_collection.insert_one(new_product)
        
        return jsonify({
            'id': str(new_product['_id']),
            'name': new_product['name'],
            'price': new_product['price'],
            'category_id': new_product['category_id'],
            'image': new_product['image']
        }), 201
    except Exception as e:
        return jsonify({'error': f'Lỗi khi thêm sản phẩm: {str(e)}'}), 400

@app.route('/api/products/<product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        # Kiểm tra quyền admin
        current_user_id = get_jwt_identity()
        
        # Thử tìm user bằng ObjectId
        try:
            from bson import ObjectId
            user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        except:
            # Nếu không phải ObjectId, tìm bằng string
            user = users_collection.find_one({'_id': current_user_id})
        
        if not user or user.get('role') != 'Admin':
            return jsonify({'message': 'Không có quyền truy cập'}), 403
            
        # Lấy dữ liệu từ request (FormData)
        name = request.form.get('name')
        price = request.form.get('price')
        link = request.form.get('link')
        category_id = request.form.get('category_id')
        
        if not all([name, price, category_id]):
            return jsonify({'message': 'Thiếu thông tin sản phẩm'}), 400
            
        # Tìm sản phẩm
        product = products_collection.find_one({'_id': product_id})
        if not product:
            return jsonify({'message': 'Không tìm thấy sản phẩm'}), 404
            
        # Cập nhật sản phẩm
        update_data = {
            'name': name,
            'price': float(price),
            'category_id': category_id
        }
        
        # Chỉ cập nhật link nếu có
        if link:
            update_data['link_demo'] = link
            
        # Xử lý upload ảnh mới nếu có
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Xóa ảnh cũ nếu có
                if product.get('image'):
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image'].replace('/uploads/', ''))
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                        print(f"✅ Đã xóa ảnh cũ: {old_image_path}")
                
                # Upload ảnh mới
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                update_data['image'] = f"/uploads/{unique_filename}"
                print(f"✅ Đã upload ảnh mới: {unique_filename}")
        
        products_collection.update_one(
            {'_id': product_id},
            {'$set': update_data}
        )
        
        return jsonify({'message': 'Cập nhật sản phẩm thành công!'}), 200
        
    except Exception as e:
        print(f"Lỗi khi cập nhật sản phẩm: {e}")
        return jsonify({'message': 'Lỗi hệ thống, vui lòng thử lại sau.'}), 500

@app.route('/api/products/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        # Kiểm tra quyền admin
        current_user_id = get_jwt_identity()
        
        # Thử tìm user bằng ObjectId
        try:
            from bson import ObjectId
            user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        except:
            # Nếu không phải ObjectId, tìm bằng string
            user = users_collection.find_one({'_id': current_user_id})
        
        if not user or user.get('role') != 'Admin':
            return jsonify({'message': 'Không có quyền truy cập'}), 403
            
        # Tìm sản phẩm
        product = products_collection.find_one({'_id': product_id})
        if not product:
            return jsonify({'message': 'Không tìm thấy sản phẩm'}), 404
            
        # Xóa ảnh sản phẩm nếu có
        if product.get('image'):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image'].replace('/uploads/', ''))
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"✅ Đã xóa ảnh sản phẩm: {image_path}")
            
        # Xóa sản phẩm
        products_collection.delete_one({'_id': product_id})
        
        return jsonify({'message': 'Xóa sản phẩm thành công!'}), 200
        
    except Exception as e:
        print(f"Lỗi khi xóa sản phẩm: {e}")
        return jsonify({'message': 'Lỗi hệ thống, vui lòng thử lại sau.'}), 500

# User Management routes
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền xem danh sách users'}), 403
        
    try:
        users = list(users_collection.find())
        result = []
        for user in users:
            result.append({
                'username': user['username'],
                'email': user.get('email', ''),
                'role': user['role'],
                'balance': user['balance'],
                'totalTopup': user.get('totalTopup', 0)
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy danh sách users: {str(e)}'}), 500

@app.route('/api/user/<username>/update-balance', methods=['POST'])
@jwt_required()
def update_balance(username):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    current_user = users_collection.find_one({'_id': current_user_id})
    data = request.get_json()
    amount = data.get('amount')
    transaction_type = data.get('type')
    description = data.get('description', 'Cập nhật số dư')

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'message': 'Không tìm thấy người dùng'}), 404

    # Kiểm tra quyền
    if current_user['username'] != user['username'] and current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền cập nhật số dư của người khác.'}), 403

    try:
        # Cập nhật số dư
        if transaction_type == 'add':
            new_balance = user['balance'] + amount
            new_total_topup = user['total_topup'] + amount
        elif transaction_type == 'subtract':
            new_balance = max(0, user['balance'] - amount)
            new_total_topup = user['total_topup']

        users_collection.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'balance': new_balance,
                    'total_topup': new_total_topup
                }
            }
        )

        # Lưu lịch sử giao dịch
        transaction = {
            '_id': generate_id(),
            'user_id': user['_id'],
            'amount': amount,
            'transaction_type': transaction_type,
            'admin_id': current_user['_id'],
            'description': description,
            'created_at': datetime.utcnow()
        }
        transactions_collection.insert_one(transaction)

        return jsonify({
            'message': 'Cập nhật số dư thành công',
            'balance': new_balance,
            'totalTopup': new_total_topup
        }), 200

    except Exception as e:
        return jsonify({'message': 'Lỗi khi cập nhật số dư', 'error': str(e)}), 500

@app.route('/api/user/<username>', methods=['DELETE'])
@jwt_required()
def delete_user(username):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    print(f"Debug - current_user_id: {current_user_id}")
    print(f"Debug - current_user: {current_user}")
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    # Chỉ admin mới có quyền xóa user
    if current_user['role'] != 'Admin':
        return jsonify({'message': f'Bạn không có quyền xóa user. Role: {current_user["role"]}'}), 403
        
    try:
        user = users_collection.find_one({'username': username})
        if not user:
            return jsonify({'message': 'Không tìm thấy user'}), 404
            
        # Không cho phép xóa chính mình
        if current_user['username'] == username:
            return jsonify({'message': 'Không thể xóa chính mình'}), 400
            
        users_collection.delete_one({'username': username})
        return jsonify({'message': f'Đã xóa user {username} thành công'}), 200
    except Exception as e:
        return jsonify({'error': f'Lỗi khi xóa user: {str(e)}'}), 500

@app.route('/api/user/<username>', methods=['PUT'])
@jwt_required()
def update_user(username):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    # Chỉ admin mới có quyền update user
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền cập nhật user'}), 403
        
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        balance = data.get('balance')
        
        # Tìm user cần update
        user = users_collection.find_one({'username': username})
        if not user:
            return jsonify({'message': 'Không tìm thấy user'}), 404
        
        # Không cho phép thay đổi role của chính mình
        if current_user['username'] == username and role != current_user['role']:
            return jsonify({'message': 'Không thể thay đổi role của chính mình'}), 400
        
        # Cập nhật thông tin
        update_data = {}
        if email:
            update_data['email'] = email
        if password:
            update_data['password'] = password  # Không hash vì đang dùng plain text
        if role:
            update_data['role'] = role
        if balance is not None:
            update_data['balance'] = int(balance)
        
        users_collection.update_one(
            {'username': username},
            {'$set': update_data}
        )
        
        return jsonify({'message': f'Cập nhật user {username} thành công'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Lỗi khi cập nhật user: {str(e)}'}), 500

@app.route('/api/user/<username>/balance', methods=['GET'])
@jwt_required()
def get_user_balance(username):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'message': 'Không tìm thấy người dùng'}), 404

    return jsonify({'balance': user['balance']}), 200

@app.route('/api/user/<username>/transactions', methods=['GET'])
@jwt_required()
def get_user_transactions(username):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    user = users_collection.find_one({'username': username})
    
    if not user:
        return jsonify({'message': 'Không tìm thấy người dùng'}), 404

    if not current_user:
        return jsonify({'message': 'Không tìm thấy user hiện tại'}), 404

    if current_user['username'] != user['username'] and current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền xem lịch sử giao dịch của người khác.'}), 403

    try:
        transactions = list(transactions_collection.find({'user_id': user['_id']}))
        result = []
        for trans in transactions:
            admin = users_collection.find_one({'_id': trans['admin_id']})
            result.append({
                'id': str(trans['_id']),
                'amount': trans['amount'],
                'transaction_type': trans['transaction_type'],
                'admin_username': admin['username'] if admin else 'Unknown',
                'description': trans['description'],
                'created_at': trans['created_at'].isoformat()
            })

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy transactions: {str(e)}'}), 500

# Buy product
@app.route('/api/buy', methods=['POST'])
@jwt_required()
def buy_product():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    data = request.get_json()
    product_id = data.get('productId')

    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        user = users_collection.find_one({'_id': current_user_id})
    
    # Tìm sản phẩm
    product = products_collection.find_one({'_id': product_id})

    if not user or not product:
        return jsonify({'message': 'Không tìm thấy user hoặc sản phẩm'}), 404

    if user['balance'] < product['price']:
        return jsonify({'message': 'Số dư không đủ'}), 400

    try:
        # Trừ tiền
        new_balance = user['balance'] - product['price']
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'balance': new_balance}}
        )
        
        # Lưu đơn hàng
        order = {
            '_id': generate_id(),
            'user_id': user['_id'],
            'product_id': product['_id'],
            'price': product['price'],
            'created_at': datetime.utcnow()
        }
        orders_collection.insert_one(order)
        
        return jsonify({'message': 'Mua sản phẩm thành công!'}), 200
    except Exception as e:
        return jsonify({'message': f'Lỗi khi mua sản phẩm: {str(e)}'}), 500

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/upload-image', methods=['POST'])
@jwt_required()
def upload_image():
    """Upload ảnh cho bài viết"""
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        # Kiểm tra quyền admin
        current_user_id = get_jwt_identity()
        try:
            current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        except:
            current_user = users_collection.find_one({'_id': current_user_id})
        
        if not current_user or current_user['role'] != 'Admin':
            return jsonify({'message': 'Bạn không có quyền upload ảnh'}), 403
        
        # Kiểm tra file
        if 'image' not in request.files:
            return jsonify({'message': 'Không có file ảnh'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'message': 'Không có file được chọn'}), 400
        
        # Kiểm tra loại file
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
            return jsonify({'message': 'Loại file không được hỗ trợ'}), 400
        
        # Kiểm tra kích thước file (max 5MB)
        if len(file.read()) > 5 * 1024 * 1024:
            file.seek(0)  # Reset file pointer
            return jsonify({'message': 'File quá lớn (max 5MB)'}), 400
        
        file.seek(0)  # Reset file pointer
        
        # Tạo tên file unique
        import uuid
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        
        # Lưu file vào thư mục img_post
        img_post_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'img_post')
        os.makedirs(img_post_folder, exist_ok=True)
        
        file_path = os.path.join(img_post_folder, filename)
        file.save(file_path)
        
        # Trả về URL ảnh
        image_url = f"/uploads/img_post/{filename}"
        
        print(f"✅ Upload ảnh thành công: {image_url}")
        
        return jsonify({
            'message': 'Upload ảnh thành công!',
            'image_url': image_url,
            'filename': filename
        }), 200
        
    except Exception as e:
        print(f"❌ Lỗi upload ảnh: {str(e)}")
        return jsonify({'message': f'Lỗi upload ảnh: {str(e)}'}), 500

# Test route
@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({
        'message': 'Flask backend đang hoạt động!',
        'database': 'Connected' if db is not None else 'Disconnected',
        'timestamp': datetime.now().isoformat()
    }), 200

# Stats route
@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền xem thống kê'}), 403
        
    try:
        # Tổng users
        users_count = users_collection.count_documents({})
        
        # Tổng sản phẩm
        products_count = products_collection.count_documents({})
        
        # Tổng doanh thu (tổng tiền nạp + tiền admin cộng)
        total_revenue = 0
        
        # Tính từ totalTopup của users
        users = users_collection.find()
        for user in users:
            total_revenue += user.get('totalTopup', 0)
        
        # Tính từ transactions (tiền admin cộng cho user)
        transactions = transactions_collection.find({"transaction_type": "add"})
        for trans in transactions:
            total_revenue += trans.get('amount', 0)
        
        # Tổng đơn hàng đã thanh toán (tất cả orders)
        total_orders_count = orders_collection.count_documents({})
        
        return jsonify({
            'users_count': users_count,
            'products_count': products_count,
            'total_revenue': total_revenue,
            'completed_orders_count': total_orders_count
        }), 200
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy thống kê: {str(e)}'}), 500

# Bank Settings API
@app.route('/api/bank/settings', methods=['GET'])
def get_bank_settings():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        # Lấy cấu hình ngân hàng hiện tại
        settings = bank_settings_collection.find_one({})
        
        if settings:
            return jsonify({
                'settings': {
                    'bankName': settings.get('bankName', ''),
                    'accountNumber': settings.get('accountNumber', ''),
                    'accountName': settings.get('accountName', ''),
                    'transferContent': settings.get('transferContent', ''),
                    'transferNote': settings.get('transferNote', ''),
                    'qrImage': settings.get('qrImage', '')
                }
            }), 200
        else:
            return jsonify({'settings': None}), 200
            
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy cấu hình ngân hàng: {str(e)}'}), 500

@app.route('/api/bank/settings', methods=['POST'])
@jwt_required()
def save_bank_settings():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    # Chỉ admin mới có quyền cập nhật cấu hình ngân hàng
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền cập nhật cấu hình ngân hàng'}), 403
        
    try:
        # Lấy dữ liệu từ form
        bank_name = request.form.get('bankName')
        account_number = request.form.get('accountNumber')
        account_name = request.form.get('accountName')
        transfer_content = request.form.get('transferContent')
        transfer_note = request.form.get('transferNote')
        
        # Xử lý upload ảnh QR
        qr_image_path = ''
        if 'qrImage' in request.files:
            qr_file = request.files['qrImage']
            if qr_file and qr_file.filename:
                # Tạo tên file an toàn
                filename = secure_filename(qr_file.filename)
                # Thêm timestamp để tránh trùng tên
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
                
                # Lưu file
                qr_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                qr_image_path = f'/uploads/{filename}'
        
        # Tạo hoặc cập nhật cấu hình
        settings_data = {
            'bankName': bank_name,
            'accountNumber': account_number,
            'accountName': account_name,
            'transferContent': transfer_content,
            'transferNote': transfer_note,
            'updated_at': datetime.utcnow()
        }
        
        # Nếu có upload ảnh QR mới
        if qr_image_path:
            settings_data['qrImage'] = qr_image_path
        
        # Kiểm tra xem đã có cấu hình chưa
        existing_settings = bank_settings_collection.find_one({})
        
        if existing_settings:
            # Cập nhật cấu hình hiện tại
            bank_settings_collection.update_one(
                {'_id': existing_settings['_id']},
                {'$set': settings_data}
            )
        else:
            # Tạo cấu hình mới
            settings_data['_id'] = generate_id()
            bank_settings_collection.insert_one(settings_data)
        
        return jsonify({'message': 'Lưu cấu hình ngân hàng thành công!'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lưu cấu hình ngân hàng: {str(e)}'}), 500

# User Orders API
@app.route('/api/orders', methods=['POST'])
@jwt_required()
def create_order():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        current_user_id = get_jwt_identity()
        print(f"🔍 Creating order for user: {current_user_id}")
        
        data = request.get_json()
        print(f"📦 Request data: {data}")
        
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        print(f"🛍️ Product ID: {product_id}, Quantity: {quantity}")
        
        if not product_id:
            return jsonify({'message': 'Thiếu thông tin sản phẩm'}), 400
            
        # Get product details
        print(f"🔍 Looking for product: {product_id}")
        product = products_collection.find_one({'_id': product_id})
        if not product:
            print(f"❌ Product not found with string ID")
            # Try ObjectId
            try:
                product = products_collection.find_one({'_id': ObjectId(product_id)})
                print(f"✅ Found product with ObjectId: {product is not None}")
            except:
                print(f"❌ Product not found with ObjectId either")
                return jsonify({'message': 'Sản phẩm không tồn tại'}), 404
        else:
            print(f"✅ Found product: {product['name']}")
        
        if not product:
            return jsonify({'message': 'Sản phẩm không tồn tại'}), 404
            
        # Get user details - try by ID first, then by username
        print(f"🔍 Looking for user: {current_user_id}")
        user = users_collection.find_one({'_id': current_user_id})
        if not user:
            print(f"❌ User not found with string ID")
            # Try ObjectId conversion
            try:
                user = users_collection.find_one({'_id': ObjectId(current_user_id)})
                print(f"✅ Found user with ObjectId: {user is not None}")
            except:
                print(f"❌ User not found with ObjectId")
        
        if not user:
            # Try to find by username (JWT might contain username instead of ID)
            print(f"🔍 Trying to find by username: {current_user_id}")
            user = users_collection.find_one({'username': current_user_id})
            print(f"✅ Found user by username: {user is not None}")
        
        if not user:
            print(f"❌ User not found by any method")
            return jsonify({'message': 'Người dùng không tồn tại'}), 404
        else:
            print(f"✅ Found user: {user['username']} - Balance: {user.get('balance', 0)}")
            
        # Calculate total price
        price = float(product['price'])  # Convert to float
        if product.get('sale'):
            price = price * (1 - float(product['sale']) / 100)
        total_price = price * quantity
        
        # Check user balance
        if user['balance'] < total_price:
            return jsonify({'message': 'Số dư không đủ'}), 400
            
        # Create order
        order = {
            '_id': generate_id(),
            'user_id': user['_id'],  # Use user's _id, not current_user_id
            'product_id': product_id,
            'quantity': quantity,
            'total_price': total_price,
            'status': 'completed',
            'created_at': datetime.utcnow()
        }
        
        # Insert order
        orders_collection.insert_one(order)
        
        # Update user balance
        new_balance = user['balance'] - total_price
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'balance': new_balance}}
        )
        
        return jsonify({
            'message': 'Mua hàng thành công!',
            'order_id': str(order['_id']),
            'total_price': total_price,
            'new_balance': new_balance
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating order: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Lỗi khi tạo đơn hàng: {str(e)}'}), 500

@app.route('/api/user/<username>/orders', methods=['GET'])
@jwt_required()
def get_user_orders(username):
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    # Kiểm tra quyền (chỉ xem orders của chính mình)
    if current_user['username'] != username:
        return jsonify({'message': 'Bạn không có quyền xem orders của user khác'}), 403
        
    try:
        # Lấy tất cả orders của user
        orders = list(orders_collection.find({'user_id': current_user['_id']}))
        
        # Lấy thông tin sản phẩm cho mỗi order
        result = []
        for order in orders:
            # Xử lý cấu trúc orders mới với products array
            if 'products' in order and isinstance(order['products'], list):
                # Cấu trúc mới: order có products array
                for product_item in order['products']:
                    product_id = product_item.get('product_id')
                    if product_id:
                        # Tìm thông tin sản phẩm
                        product = products_collection.find_one({'_id': ObjectId(product_id)})
                        
                        order_info = {
                            'id': str(order['_id']),
                            'price': product_item.get('price', 0),
                            'created_at': order['created_at'].isoformat(),
                            'status': order.get('status', 'completed'),
                            'product_name': product['name'] if product else product_item.get('name', 'Sản phẩm không tồn tại'),
                            'product_link_tai': product.get('link_tai') if product else None,
                            'product_link_demo': product.get('link_demo') if product else None,
                            'product_name_key': product.get('name_key') if product else None,
                            'product_content': product.get('content') if product else None
                        }
                        result.append(order_info)
            else:
                # Cấu trúc cũ: order có product_id đơn lẻ
                product_id = order.get('product_id')
                if product_id:
                    # Thử tìm sản phẩm với nhiều cách khác nhau
                    product = None
                    
                    # Thử với ObjectId
                    try:
                        product = products_collection.find_one({'_id': ObjectId(product_id)})
                    except:
                        pass
                    
                    # Nếu không tìm thấy, thử với string
                    if not product:
                        product = products_collection.find_one({'_id': product_id})
                    
                    # Nếu vẫn không tìm thấy, thử với tên sản phẩm
                    if not product and order.get('product_name'):
                        product = products_collection.find_one({'name': order.get('product_name')})
                    
                    # Tạo thông tin order với fallback
                    order_info = {
                        'id': str(order['_id']),
                        'price': order.get('total_price', order.get('price', 0)),  # Use total_price for new orders
                        'created_at': order['created_at'].isoformat(),
                        'status': order.get('status', 'completed'),
                        'product_name': product['name'] if product else (order.get('product_name') or 'Sản phẩm không tồn tại'),
                        'product_link_tai': product.get('link_tai') if product else order.get('product_link_tai'),
                        'product_link_demo': product.get('link_demo') if product else order.get('product_link_demo'),
                        'product_name_key': product.get('name_key') if product else order.get('product_name_key'),
                        'product_content': product.get('content') if product else order.get('product_content')
                    }
                    result.append(order_info)
        
        return jsonify({'orders': result}), 200
        
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy orders: {str(e)}'}), 500

# Top-up History API
@app.route('/api/topup-history', methods=['GET'])
@jwt_required()
def get_topup_history():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    # Chỉ admin mới có quyền xem lịch sử nạp tiền
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền xem lịch sử nạp tiền'}), 403
        
    try:
        # Lấy tất cả lịch sử nạp tiền từ wallet_topups_collection
        topups = list(wallet_topups_collection.find({}).sort('created_at', -1))
        
        # Chuyển đổi ObjectId thành string
        result = []
        for topup in topups:
            # Tìm thông tin user
            user = users_collection.find_one({'_id': topup['user_id']})
            
            topup_info = {
                'id': str(topup['_id']),
                'username': user['username'] if user else 'User không tồn tại',
                'amount': topup['amount'],
                'method': topup.get('method', 'Nạp tiền'),
                'status': topup.get('status', 'completed'),
                'created_at': topup['created_at'].isoformat()
            }
            result.append(topup_info)
        
        return jsonify({'topups': result}), 200
        
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy lịch sử nạp tiền: {str(e)}'}), 500

# Admin Transactions API
@app.route('/api/admin-transactions', methods=['GET'])
@jwt_required()
def get_admin_transactions():
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    current_user_id = get_jwt_identity()
    
    # Thử tìm user bằng ObjectId
    try:
        from bson import ObjectId
        current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
    except:
        # Nếu không phải ObjectId, tìm bằng string
        current_user = users_collection.find_one({'_id': current_user_id})
    
    if not current_user:
        return jsonify({'message': 'Không tìm thấy user'}), 404
    
    # Chỉ admin mới có quyền xem giao dịch admin
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Bạn không có quyền xem giao dịch admin'}), 403
        
    try:
        # Lấy tất cả giao dịch từ transactions_collection
        transactions = list(transactions_collection.find({}).sort('created_at', -1))
        
        # Chuyển đổi ObjectId thành string
        result = []
        for transaction in transactions:
            # Tìm thông tin user
            user = users_collection.find_one({'_id': transaction['user_id']})
            
            transaction_info = {
                'id': str(transaction['_id']),
                'username': user['username'] if user else 'User không tồn tại',
                'amount': transaction['amount'],
                'type': transaction['transaction_type'],
                'description': transaction.get('description', ''),
                'created_at': transaction['created_at'].isoformat()
            }
            result.append(transaction_info)
        
        return jsonify({'transactions': result}), 200
        
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy giao dịch admin: {str(e)}'}), 500

# Nạp thẻ cào
@app.route('/api/topup-card', methods=['POST'])
@jwt_required()
def topup_card():
    data = request.get_json()
    card_type = data.get('cardType')
    amount = float(data.get('amount', 0))
    serial = data.get('serial')
    code = data.get('code')
    user_id = get_jwt_identity()
    if not all([card_type, amount, serial, code, user_id]):
        return jsonify({'success': False, 'message': 'Thiếu thông tin!'}), 400
    topup = {
        'user_id': user_id,
        'card_type': card_type,
        'amount': amount,
        'serial': serial,
        'code': code,
        'status': 'Đang nạp',
        'created_at': datetime.utcnow()
    }
    result = topup_cards_collection.insert_one(topup)
    return jsonify({
        'success': True,
        'message': 'Nạp thẻ thành công! Đang nạp...',
        'topupId': str(result.inserted_id)
    })

# Cập nhật trạng thái nạp thẻ
@app.route('/api/topup-card/<topup_id>/status', methods=['POST'])
@jwt_required()
def update_topup_status(topup_id):
    data = request.get_json()
    status = data.get('status')
    if not status:
        return jsonify({'success': False, 'message': 'Thiếu trạng thái!'}), 400
    topup = topup_cards_collection.find_one({'_id': ObjectId(topup_id)})
    if not topup:
        return jsonify({'success': False, 'message': 'Không tìm thấy giao dịch!'}), 404
    if status == 'Thành công' and topup['status'] != 'Thành công':
        # Cộng tiền vào tài khoản user (dù user_id là ObjectId hay string)
        user = users_collection.find_one({'_id': topup['user_id']})
        if not user:
            try:
                user = users_collection.find_one({'_id': ObjectId(topup['user_id'])})
            except:
                user = None
        if not user:
            return jsonify({'success': False, 'message': 'Không tìm thấy user!'}), 404
        new_balance = float(user.get('balance', 0)) + float(topup['amount'])
        users_collection.update_one({'_id': user['_id']}, {'$set': {'balance': new_balance}})
        # (Optional) Lưu lịch sử giao dịch nếu muốn
    topup_cards_collection.update_one({'_id': ObjectId(topup_id)}, {'$set': {'status': status}})
    return jsonify({'success': True, 'message': 'Cập nhật trạng thái thành công.'})

# API cho bài viết
@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Lấy danh sách tất cả bài viết"""
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        articles = list(articles_collection.find({}).sort('created_at', -1))
        
        # Chuyển đổi ObjectId thành string
        result = []
        for article in articles:
            # Tìm thông tin tác giả (author_id là ObjectId)
            try:
                author = users_collection.find_one({'_id': ObjectId(article['author_id'])})
            except:
                # Thử tìm bằng string nếu không phải ObjectId
                try:
                    author = users_collection.find_one({'_id': article['author_id']})
                except:
                    author = None
            
            article_info = {
                'id': str(article['_id']),
                'title': article['title'],
                'content': article['content'],
                'summary': article.get('summary', ''),
                'image': article.get('image', ''),
                'author': author['username'] if author else 'Admin',
                'views': article.get('views', 0),
                'status': article.get('status', 'published'),
                'created_at': article['created_at'].isoformat(),
                'updated_at': article.get('updated_at', article['created_at']).isoformat()
            }
            result.append(article_info)
        
        return jsonify({'articles': result}), 200
        
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy danh sách bài viết: {str(e)}'}), 500

@app.route('/api/articles/<article_id>', methods=['GET'])
def get_article(article_id):
    """Lấy chi tiết một bài viết"""
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        print(f"🔍 Tìm bài viết với ID: {article_id}")
        
        # Tìm bằng string trước (vì database lưu ID dưới dạng string)
        article = articles_collection.find_one({'_id': article_id})
        print(f"🔍 Tìm bằng string: {article is not None}")
        
        # Nếu không tìm thấy bằng string, thử bằng ObjectId
        if not article:
            try:
                article = articles_collection.find_one({'_id': ObjectId(article_id)})
                print(f"✅ Tìm thấy bài viết bằng ObjectId")
            except Exception as e:
                print(f"❌ Lỗi ObjectId: {e}")
                article = None
        
        if not article:
            print(f"❌ Không tìm thấy bài viết với ID: {article_id}")
            return jsonify({'message': 'Không tìm thấy bài viết'}), 404
        
        # Tìm thông tin tác giả (author_id là ObjectId)
        print(f"🔍 Tìm tác giả với ID: {article['author_id']}")
        try:
            author = users_collection.find_one({'_id': ObjectId(article['author_id'])})
            print(f"✅ Tìm thấy tác giả bằng ObjectId")
        except Exception as e:
            print(f"❌ Lỗi tìm tác giả bằng ObjectId: {e}")
            # Thử tìm bằng string nếu không phải ObjectId
            try:
                author = users_collection.find_one({'_id': article['author_id']})
                print(f"✅ Tìm thấy tác giả bằng string")
            except Exception as e2:
                print(f"❌ Lỗi tìm tác giả bằng string: {e2}")
                author = None
        
        # Tăng lượt xem
        try:
            articles_collection.update_one(
                {'_id': article['_id']}, 
                {'$inc': {'views': 1}}
            )
        except Exception as e:
            print(f"Lỗi khi tăng lượt xem: {e}")
        
        article_info = {
            'id': str(article['_id']),
            'title': article['title'],
            'content': article['content'],
            'summary': article.get('summary', ''),
            'image': article.get('image', ''),
            'author': author['username'] if author else 'Admin',
            'views': article.get('views', 0) + 1,
            'status': article.get('status', 'published'),
            'created_at': article['created_at'].isoformat(),
            'updated_at': article.get('updated_at', article['created_at']).isoformat()
        }
        
        return jsonify(article_info), 200
        
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy chi tiết bài viết: {str(e)}'}), 500

@app.route('/api/articles', methods=['POST'])
@jwt_required()
def create_article():
    """Tạo bài viết mới (chỉ admin)"""
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        print("🔍 Bắt đầu tạo bài viết...")
        print(f"📝 Request method: {request.method}")
        print(f"📝 Request headers: {dict(request.headers)}")
        
        current_user_id = get_jwt_identity()
        print(f"👤 User ID: {current_user_id}")
        
        # Tìm user hiện tại
        try:
            from bson import ObjectId
            current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
            print(f"✅ Tìm thấy user bằng ObjectId")
        except Exception as e:
            print(f"❌ Lỗi ObjectId: {e}")
            current_user = users_collection.find_one({'_id': current_user_id})
            print(f"🔍 Tìm user bằng string: {current_user is not None}")
        
        if not current_user:
            print(f"❌ Không tìm thấy user với ID: {current_user_id}")
            return jsonify({'message': 'Không tìm thấy user'}), 404
        
        print(f"👤 User role: {current_user.get('role', 'Unknown')}")
        
        # Chỉ admin mới có quyền tạo bài viết
        if current_user['role'] != 'Admin':
            print(f"❌ User không có quyền admin")
            return jsonify({'message': 'Bạn không có quyền tạo bài viết'}), 403
        
        data = request.get_json()
        print(f"📝 Data nhận được: {data}")
        
        title = data.get('title')
        content = data.get('content')
        summary = data.get('summary', '')
        image = data.get('image', '')
        status = data.get('status', 'published')
        
        print(f"📝 Parsed data: title='{title}', content='{content[:50]}...', image='{image}', status='{status}'")
        
        if not all([title, content]):
            print(f"❌ Thiếu thông tin: title={bool(title)}, content={bool(content)}")
            return jsonify({'error': 'Thiếu thông tin bài viết'}), 400
        
        new_article = {
            '_id': generate_id(),
            'title': title,
            'content': content,
            'summary': summary,
            'image': image,
            'author_id': current_user['_id'],
            'views': 0,
            'status': status,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        print(f"📝 New article data: {new_article}")
        
        result = articles_collection.insert_one(new_article)
        print(f"✅ Tạo bài viết thành công: inserted_id={result.inserted_id}")
        
        return jsonify({
            'id': new_article['_id'],
            'title': new_article['title'],
            'message': 'Tạo bài viết thành công!'
        }), 201
        
    except Exception as e:
        print(f"❌ Exception khi tạo bài viết: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Lỗi khi tạo bài viết: {str(e)}'}), 400

@app.route('/api/articles/<article_id>', methods=['PUT'])
@jwt_required()
def update_article(article_id):
    """Cập nhật bài viết (chỉ admin)"""
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        print(f"✏️ Bắt đầu cập nhật bài viết ID: {article_id}")
        current_user_id = get_jwt_identity()
        print(f"👤 User ID: {current_user_id}")
        
        # Tìm user hiện tại
        try:
            from bson import ObjectId
            current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
            print(f"✅ Tìm thấy user bằng ObjectId")
        except Exception as e:
            print(f"❌ Lỗi ObjectId: {e}")
            current_user = users_collection.find_one({'_id': current_user_id})
            print(f"🔍 Tìm user bằng string: {current_user is not None}")
        
        if not current_user:
            print(f"❌ Không tìm thấy user với ID: {current_user_id}")
            return jsonify({'message': 'Không tìm thấy user'}), 404
        
        print(f"👤 User role: {current_user.get('role', 'Unknown')}")
        
        # Chỉ admin mới có quyền cập nhật bài viết
        if current_user['role'] != 'Admin':
            print(f"❌ User không có quyền admin")
            return jsonify({'message': 'Bạn không có quyền cập nhật bài viết'}), 403
        
        # Tìm bài viết - thử bằng string trước
        article = articles_collection.find_one({'_id': article_id})
        print(f"🔍 Tìm bài viết bằng string: {article is not None}")
        
        # Nếu không tìm thấy bằng string, thử bằng ObjectId
        if not article:
            try:
                article = articles_collection.find_one({'_id': ObjectId(article_id)})
                print(f"✅ Tìm thấy bài viết bằng ObjectId")
            except Exception as e:
                print(f"❌ Lỗi ObjectId: {e}")
                article = None
        
        if not article:
            print(f"❌ Không tìm thấy bài viết với ID: {article_id}")
            return jsonify({'message': 'Không tìm thấy bài viết'}), 404
        
        print(f"📄 Tìm thấy bài viết: {article.get('title', 'N/A')}")
        
        data = request.get_json()
        print(f"📝 Data nhận được: {data}")
        
        title = data.get('title')
        content = data.get('content')
        summary = data.get('summary', '')
        image = data.get('image', '')
        status = data.get('status', 'published')
        
        if not all([title, content]):
            print(f"❌ Thiếu thông tin: title={bool(title)}, content={bool(content)}")
            return jsonify({'error': 'Thiếu thông tin bài viết'}), 400
        
        update_data = {
            'title': title,
            'content': content,
            'summary': summary,
            'image': image,
            'status': status,
            'updated_at': datetime.utcnow()
        }
        
        print(f"📝 Update data: {update_data}")
        
        result = articles_collection.update_one(
            {'_id': article['_id']}, 
            {'$set': update_data}
        )
        
        print(f"✅ Cập nhật thành công: modified_count={result.modified_count}")
        
        return jsonify({'message': 'Cập nhật bài viết thành công!'}), 200
        
    except Exception as e:
        print(f"❌ Exception khi cập nhật bài viết: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Lỗi khi cập nhật bài viết: {str(e)}'}), 400

@app.route('/api/articles/<article_id>', methods=['DELETE'])
@jwt_required()
def delete_article(article_id):
    """Xóa bài viết (chỉ admin)"""
    if db is None:
        return jsonify({'message': 'Database không khả dụng'}), 500
        
    try:
        print(f"🗑️ Bắt đầu xóa bài viết ID: {article_id}")
        current_user_id = get_jwt_identity()
        print(f"👤 User ID: {current_user_id}")
        
        # Tìm user hiện tại
        try:
            from bson import ObjectId
            current_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
            print(f"✅ Tìm thấy user bằng ObjectId")
        except Exception as e:
            print(f"❌ Lỗi ObjectId: {e}")
            current_user = users_collection.find_one({'_id': current_user_id})
            print(f"🔍 Tìm user bằng string: {current_user is not None}")
        
        if not current_user:
            print(f"❌ Không tìm thấy user với ID: {current_user_id}")
            return jsonify({'message': 'Không tìm thấy user'}), 404
        
        print(f"👤 User role: {current_user.get('role', 'Unknown')}")
        
        # Chỉ admin mới có quyền xóa bài viết
        if current_user['role'] != 'Admin':
            print(f"❌ User không có quyền admin")
            return jsonify({'message': 'Bạn không có quyền xóa bài viết'}), 403
        
        # Tìm bài viết trước khi xóa để lấy thông tin ảnh
        article = articles_collection.find_one({'_id': article_id})
        if not article:
            try:
                article = articles_collection.find_one({'_id': ObjectId(article_id)})
            except:
                article = None
        
        if not article:
            print(f"❌ Không tìm thấy bài viết để xóa")
            return jsonify({'message': 'Không tìm thấy bài viết'}), 404
        
        # Xóa ảnh nếu có
        image_path = article.get('image', '')
        if image_path and image_path.startswith('/uploads/img_post/'):
            try:
                # Lấy tên file từ path
                filename = image_path.replace('/uploads/img_post/', '')
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'img_post', filename)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️ Đã xóa ảnh: {file_path}")
                else:
                    print(f"⚠️ File ảnh không tồn tại: {file_path}")
            except Exception as e:
                print(f"❌ Lỗi khi xóa ảnh: {str(e)}")
        
        # Xóa bài viết - thử bằng string trước
        result = articles_collection.delete_one({'_id': article_id})
        print(f"🔍 Xóa bằng string, deleted_count: {result.deleted_count}")
        
        # Nếu không xóa được bằng string, thử bằng ObjectId
        if result.deleted_count == 0:
            try:
                result = articles_collection.delete_one({'_id': ObjectId(article_id)})
                print(f"✅ Xóa bằng ObjectId, deleted_count: {result.deleted_count}")
            except Exception as e:
                print(f"❌ Lỗi ObjectId delete: {e}")
                result = articles_collection.delete_one({'_id': article_id})
                print(f"🔍 Xóa bằng string lần 2, deleted_count: {result.deleted_count}")
        
        if result.deleted_count == 0:
            print(f"❌ Không tìm thấy bài viết để xóa")
            return jsonify({'message': 'Không tìm thấy bài viết'}), 404
        
        print(f"✅ Xóa bài viết thành công!")
        return jsonify({'message': 'Xóa bài viết thành công!'}), 200
        
    except Exception as e:
        print(f"❌ Exception khi xóa bài viết: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Lỗi khi xóa bài viết: {str(e)}'}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True) 