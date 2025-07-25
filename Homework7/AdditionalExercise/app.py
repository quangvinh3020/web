from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "supersecret"

client = MongoClient("mongodb://localhost:27017/")
db = client['onlinestore_db']
products_col = db['products']
orders_col = db['orders']
users_col = db['users']

# ------------- TRANG CHỦ & MENU -----------------
@app.route('/')
def index():
    return render_template('index.html')

# ------------- USER: XEM SẢN PHẨM -----------------
@app.route('/products')
def product_list():
    products = list(products_col.find())
    return render_template('product_list.html', products=products)

# ------------- ADMIN: XEM, THÊM, SỬA, XOÁ SẢN PHẨM -------------
@app.route('/admin/products')
def product_admin():
    products = list(products_col.find())
    return render_template('product_admin.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def product_add():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = int(request.form['price'])
        quantity = int(request.form['quantity'])
        description = request.form['description']
        image = request.form['image']
        products_col.insert_one({
            'name': name,
            'category': category,
            'price': price,
            'quantity': quantity,
            'description': description,
            'image': image
        })
        return redirect(url_for('product_admin'))
    return render_template('product_add.html')

@app.route('/admin/products/edit/<id>', methods=['GET', 'POST'])
def product_edit(id):
    prod = products_col.find_one({'_id': ObjectId(id)})
    if request.method == 'POST':
        products_col.update_one({'_id': ObjectId(id)}, {'$set': {
            'name': request.form['name'],
            'category': request.form['category'],
            'price': int(request.form['price']),
            'quantity': int(request.form['quantity']),
            'description': request.form['description'],
            'image': request.form['image']
        }})
        return redirect(url_for('product_admin'))
    return render_template('product_edit.html', product=prod)

@app.route('/admin/products/delete/<id>')
def product_delete(id):
    products_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('product_admin'))

# ------------- TÌM KIẾM SẢN PHẨM ---------------
@app.route('/search', methods=['GET', 'POST'])
def search():
    result = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        result = list(products_col.find({
            'name': {'$regex': keyword, '$options': 'i'}
        }))
    return render_template('search.html', products=result)

# ------------- GIỎ HÀNG & ĐẶT HÀNG ---------------
@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

@app.route('/add_to_cart/<id>')
def add_to_cart(id):
    product = products_col.find_one({'_id': ObjectId(id)})
    cart = session.get('cart', [])
    found = False
    for item in cart:
        if str(item['product_id']) == str(id):
            item['quantity'] += 1
            found = True
            break
    if not found:
        cart.append({
            'product_id': str(product['_id']),
            'name': product['name'],
            'price': product['price'],
            'quantity': 1
        })
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<id>')
def remove_from_cart(id):
    cart = session.get('cart', [])
    cart = [item for item in cart if item['product_id'] != id]
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    if request.method == 'POST':
        customer_name = request.form['name']
        customer_phone = request.form['phone']
        customer_address = request.form['address']
        orders_col.insert_one({
            'items': cart,
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'customer_address': customer_address,
            'total': total,
            'status': 'pending'
        })
        session['cart'] = []
        return render_template('order_success.html')
    return render_template('checkout.html', cart=cart, total=total)

# ------------- QUẢN LÝ USER & ĐĂNG NHẬP (CƠ BẢN) ---------------
@app.route('/users')
def users():
    users = list(users_col.find())
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if users_col.find_one({'username': username}):
            return render_template('add_user.html', error="Tài khoản đã tồn tại")
        users_col.insert_one({'username': username, 'password': password, 'role': role})
        return redirect(url_for('users'))
    return render_template('add_user.html')

@app.route('/users/delete/<user_id>')
def delete_user(user_id):
    users_col.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('users'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_col.find_one({"username": username, "password": password})
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            error = "Sai tên đăng nhập hoặc mật khẩu!"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
