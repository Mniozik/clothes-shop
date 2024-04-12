# DONE
# python3 app.py
# http://localhost:5000/users


from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    version = db.Column(db.Integer, default=1)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    color = db.Column(db.String(50))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref=db.backref('products', lazy=False))
    version = db.Column(db.Integer, default=1)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    version = db.Column(db.Integer, default=1)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    version = db.Column(db.Integer, default=1)
    
class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True)
    used = db.Column(db.Boolean, default=False)



# -------------- TOKENS
@app.route('/tokens', methods=['POST'])
def generate_token():
    generated_token = secrets.token_hex(16)

    token = Token(token=generated_token)
    db.session.add(token)
    db.session.commit()
    return jsonify({'message': 'Token created', 'token': generated_token})


# -------------- USERS
@app.route('/users', methods=['GET'])
def get_all_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    users = User.query.paginate(page=page, per_page=per_page)
    user_list = [{'id': user.id, 'name': user.name, 'email:': user.email} for user in users.items]
    return jsonify({
        'users': user_list,
        'total_pages': users.pages,
        'current_page': users.page,
        'per_page': users.per_page,
        'total_users': users.total
    })
# 'version': user.version

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        response = make_response(jsonify({'id': user.id, 'name': user.name, 'email:': user.email}))
        response.headers['Version'] = str(user.version)
        return response
    return jsonify({'message': 'User not found'}), 404


@app.route('/users', methods=['POST'])
def add_user():
    token_header = request.headers.get('Token')
    if not token_header:
        return jsonify({'message': 'Token has been not sent in headers'}), 400

    token = Token.query.filter_by(token=token_header).first()
    if not token:
        return jsonify({'message': 'Token is not correct. Not found in database'}), 401

    if token.used:
        return jsonify({'message': 'Token has been used already'}), 403
    token.used = True
    db.session.commit()

    data = request.get_json()
    name = data['name']
    email = data['email']
    new_user = User(name=name, email=email)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if user:
        version_header = request.headers.get('Version')
        data = request.get_json()
        if user.version == int(version_header):
            user.name = data['name']
            user.email = data['email']
            user.version += 1
            db.session.commit()
            return jsonify({'message': 'User updated successfully'}), 200
        return jsonify({'message': 'User updated by another client'}), 409 #409 = Conflict
    return jsonify({'message': 'User not found'}), 404


@app.route('/users/<int:user_id>', methods=['PATCH'])
def modify_user(user_id):
    user = User.query.get(user_id)
    if user:
        data = request.get_json()
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        try:
            db.session.commit()
            return jsonify({'message': 'User modified successfully'}), 200
        except:
            db.session.rollback()
            return jsonify({'message': 'Failed to modify user'}) #500
    return jsonify({'message': 'User not found'}), 404



@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    return jsonify({'message': 'User not found'}), 404


# -------------- PRODUCTS
@app.route('/products', methods=['GET'])
def get_all_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    products = Product.query.paginate(page=page, per_page=per_page)
    product_list = [{'id': product.id, 'name': product.name, 'color': product.color, 'category': product.category_id} for product in products]
    return jsonify({
        'products': product_list,
        'total_pages': products.pages,
        'current_page': products.page,
        'per_page': products.per_page,
        'total_products': products.total
    })

# , 'version': product.version


@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        response = make_response(jsonify({'id': product.id, 'name': product.name, 'color': product.color, 'category': product.category_id}))
        response.headers['Version'] = str(product.version)
        return response
    return jsonify({'message': 'Product not found'}), 404


@app.route('/products', methods=['POST'])
def add_product():
    token_header = request.headers.get('Token')
    if not token_header:
        return jsonify({'message': 'Token has been not sent in headers'}), 400

    token = Token.query.filter_by(token=token_header).first()
    if not token:
        return jsonify({'message': 'Token is not correct. Not found in database'}), 401

    if token.used:
        return jsonify({'message': 'Token has been used already'}), 403
    token.used = True
    db.session.commit()

    # POST 
    data = request.get_json()
    name = data['name']
    color = data['color']
    category_id = data['category_id']

    new_product = Product(name=name, color=color, category_id=category_id)
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product created successfully'}), 201


@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get(product_id)
    if product:
        version_header = request.headers.get('Version')
        data = request.get_json()
        if product.version == int(version_header):
            product.name = data['name']
            product.color = data['color']
            product.category_id = data['category_id']
            product.version += 1
            db.session.commit()
            return jsonify({'message': 'Product updated successfully'}), 200
        return jsonify({'message': 'Product updated by another client'}), 409
    return jsonify({'message': 'Product not found'}), 404

@app.route('/products/<int:product_id>', methods=['PATCH'])
def modify_product(product_id):
    product = Product.query.get(product_id)
    if product:
        data = request.get_json()
        if 'name' in data:
            product.name = data['name']
        if 'color' in data:
            product.color = data['color']
        if 'category_id' in data:
            product.category_id = data['category_id']
        try:
            db.session.commit()
            return jsonify({'message': 'Product modified successfully'}), 200
        except:
            db.session.rollback()
            return jsonify({'message': 'Failed to modify product'})
    return jsonify({'message': 'Product not found'}), 404



@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'})
    return jsonify({'message': 'Product not found'}), 404



# -------------- CATEGORY
@app.route('/categories', methods=['GET'])
def get_all_categories():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    categories = Category.query.paginate(page=page, per_page=per_page)
    category_list = [{'id': category.id, 'name': category.name} for category in categories]    
    return jsonify({
        'categories': category_list,
        'total_pages': categories.pages,
        'current_page': categories.page,
        'per_page': categories.per_page,
        'total_categories': categories.total
    })
# , 'version': category.version


@app.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    category = Category.query.get(category_id)
    if category:
        response = make_response(jsonify({'id': category.id, 'name': category.name}))
        response.headers['Version'] = str(category.version)
        return response
    return jsonify({'message': 'Category not found'}), 404


@app.route('/categories/<int:category_id>/products', methods=['GET'])
def get_category_products(category_id):
    category = Category.query.get(category_id)
    if category:
        products = category.products  # Lista produktów przypisanych do kategorii
        product_list = [{'id': product.id, 'name': product.name, 'color': product.color, 'category': product.category_id} for product in products]
        return jsonify(product_list)
    return jsonify({'message': 'Category not found'}), 404
# , 'version': product.version


@app.route('/categories', methods=['POST'])
def add_category():
    token_header = request.headers.get('Token')
    if not token_header:
        return jsonify({'message': 'Token has been not sent in headers'}), 400

    token = Token.query.filter_by(token=token_header).first()
    if not token:
        return jsonify({'message': 'Token is not correct. Not found in database'}), 401

    if token.used:
        return jsonify({'message': 'Token has been used already'}), 403
    token.used = True
    db.session.commit()

    data = request.get_json()
    name = data['name']
    
    new_category = Category(name=name)
    db.session.add(new_category)
    db.session.commit()
    return jsonify({'message': 'Category created successfully'}), 201

@app.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    category = Category.query.get(category_id)
    if category:
        version_header = request.headers.get('Version')
        data = request.get_json()
        if category.version == int(version_header):
            category.name = data['name']
            category.version += 1
            db.session.commit()
            return jsonify({'message': 'Category updated successfully'}), 200
        return jsonify({'message': 'Category updated by another client'}), 409
    return jsonify({'message': 'Category not found'}), 404


# 3. kontrolery umożliwiające atomowe wykonanie aktualizacji kilku innych zasobów,
@app.route('/categories/<int:category_id>', methods=['PATCH'])
def modify_category(category_id):
    category = Category.query.get(category_id)
    if category:
        data = request.get_json()

        # Aktualizacja nazwy kategorii, jesli jest
        if 'name' in data:
            new_category_name = data['name']
            category.name = new_category_name

        # Aktualizacja powiazanych produktow, jesli sa 
        if 'products' in data:
            products_data = data['products']
            for product_data in products_data:
                product_id = product_data['id']
                new_product_name = product_data['name']
                product = Product.query.get(product_id)
                if product:
                    product.name = new_product_name
        try:
            db.session.commit()
            return jsonify({'message': 'Category and associated products modified successfully'})
        except:
            db.session.rollback()
            return jsonify({'message': 'Failed to modify category and associated products'}), 500
    return jsonify({'message': 'Category not found'}), 404




@app.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = Category.query.get(category_id)
    if category:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'message': 'Category deleted successfully'})
    return jsonify({'message': 'Category not found'}), 404



# -------------- ORDERS/PURCHASES
@app.route('/orders', methods=['GET'])
def get_all_orders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    orders = Order.query.paginate(page=page, per_page=per_page)
    order_list = [{'id': order.id, 'product_id': order.product_id, 'user_id': order.user_id} for order in orders]
    return jsonify({
        'users': order_list,
        'total_pages': orders.pages,
        'current_page': orders.page,
        'per_page': orders.per_page,
        'total_users': orders.total
    })
# , 'version': order.version


@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get(order_id)
    if order:
        response = make_response(jsonify({'id': order.id, 'product_id': order.product_id, 'user_id': order.user_id}))
        response.headers['Version'] = str(order.version)        
        return response
    return jsonify({'message': 'Order not found'}), 404


@app.route('/orders', methods=['POST'])
def add_order():
    token_header = request.headers.get('Token')
    if not token_header:
        return jsonify({'message': 'Token has been not sent in headers'}), 400

    token = Token.query.filter_by(token=token_header).first()
    if not token:
        return jsonify({'message': 'Token is not correct. Not found in database'}), 401

    if token.used:
        return jsonify({'message': 'Token has been used already'}), 403  #409 (Conflict?)
    token.used = True
    db.session.commit()


    data = request.get_json()
    user_id = data['user_id'] 
    product_id = data['product_id']
    
    new_order = Order(user_id=user_id, product_id=product_id)
    db.session.add(new_order)
    db.session.commit()
    return jsonify({'message': 'Order created successfully'}), 201


@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    order = Order.query.get(order_id)
    if order:
        version_header = request.headers.get('Version')
        data = request.get_json()
        if order.version == int(version_header):
            order.product_id = data['product_id']
            order.user_id = data['user_id']
            order.version += 1
            db.session.commit()
            return jsonify({'message': 'Order updated successfully'}), 200
        return jsonify({'message': 'Order updated by another client'}), 409
    return jsonify({'message': 'Order not found'}), 404


@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get(order_id)
    if order:
        db.session.delete(order)
        db.session.commit()
        return jsonify({'message': 'Order deleted successfully'})
    return jsonify({'message': 'Order not found'}), 404



if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Utworzenie tabeli w bazie danych
    app.run()
    # app.run(debug=True)

