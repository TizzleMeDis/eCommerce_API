from flask import Flask, jsonify, request
#Flask - gives us all the tools we need to run a flask app by creating an instance of this class
#jsonify - converts data to JSON
#request - allows us to interact with HTTP method requests as objects
from flask_sqlalchemy import SQLAlchemy
#SQLAlchemy = ORM to connect and relate python classes to SQL tables
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
#DeclarativeBase - gives us the base model functionallity to create the Classes as Model Classes for our db tables
#Mapped - Maps a Class attribute to a table column or relationship
#mapped_column - sets our Column and allows us to add any constraints we need (unique,nullable, primary_key)
from flask_marshmallow import Marshmallow
#Marshmallow - allows us to create a schema to valdite, serialize, and deserialize JSON data
from datetime import date
#date - use to create date type objects
from typing import List
#List - is used to creat a relationship that will return a list of Objects
from marshmallow import ValidationError, fields
#ValidationError - catch error messages into the database
#fields - lets us set a schema field which includes datatype and constraints
from sqlalchemy import ForeignKey, Table, String, Column, Date, Float, select, delete
#select - acts as our SELECT FROM query
#delete - acts as our DELETE query


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:****@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)


#============================== MODELS ===============================

# Association Table (Orders - Products) (Many - Many)
order_products = Table(
    "order_products",
    Base.metadata,
    Column('order_id', ForeignKey("orders.id"), primary_key=True),
    Column('product_id', ForeignKey("products.id"), primary_key=True)
)

class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(225), nullable=False)
    email: Mapped[str] = mapped_column(String(225))
    address: Mapped[str] = mapped_column(String(225))
    
    orders: Mapped[List["Order"]] = relationship(back_populates='customer')


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))

    customer: Mapped[Customer] = relationship(back_populates='orders')
    products: Mapped[List["Product"]] = relationship(secondary=order_products, back_populates="orders")

class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    orders: Mapped[List["Order"]] = relationship(secondary=order_products, back_populates="products")

#=================================== SCHEMAS =====================================

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True) #Allows for the serialization of a List of Customer objects

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
#==================================================================================================
#==================================================================================================
#============================== Customer CRUD =====================================================
@app.route("/customers", methods=["POST"])  #   ---CREATE CUSTOMER---
def add_customer():
    
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    print(customer_data)
    new_customer = Customer(name=customer_data["name"], email=customer_data["email"], address=customer_data["address"])

    db.session.add(new_customer)
    db.session.commit()

    return jsonify({"Message": "New customer added successfully", "customer": customer_schema.dump(new_customer)}), 201
#==================================================================================================
@app.route("/customers", methods=["GET"])  #   ---READ CUSTOMERS---
def get_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()

    return customers_schema.jsonify(customers), 200
#==================================================================================================
@app.route("/customers/<int:customer_id>", methods=["GET"]) #    ---READ CUSTOMER---
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"message": "Invalid customer id"}), 400
    return jsonify({"message": f"This is user {customer.name}", "customer_info": customer_schema.dump(customer)}), 200
#==================================================================================================
@app.route("/customers/<int:customer_id>", methods=["PUT"]) #   ---UPDATE CUSTOMER---
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"message": "Invalid customer id"}), 400
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.message), 400
    
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.address = customer_data['address']

    db.session.commit()
    return jsonify({
        "message": "updated successfully", 
        "Updated": customer_schema.dump(customer)
    }), 200

#==================================================================================================
@app.route("/customers/<int:customer_id>", methods=["DELETE"]) #    ---DELETE CUSTOMER---
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"message": "Invalid customer id"}), 400
    
    db.session.delete(customer)
    db.session.commit()

    return jsonify({"message": f"successfully deleted customer {customer.name}"}), 200
#==================================================================================================
#==================================================================================================
#============================== Product CRUD ======================================================
@app.route('/products', methods=['POST'])   #   ---CREATE PRODUCT---
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.message), 400
    
    new_product = Product(product_name=product_data['product_name'], price=product_data['price'])

    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({
        "message": "Product created successfully",
        "product": product_schema.dump(new_product)
    }), 201
#==================================================================================================
@app.route('/products', methods=['GET'])   #   ---READ PRODUCTS---
def get_products():
    query = select(Product)
    products = db.session.execute(query).scalars().all()
    return products_schema.jsonify(products), 200
#==================================================================================================
@app.route('/products/<int:product_id>', methods=['GET'])   #   ---READ PRODUCT---
def get_product(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    return jsonify({
        "message": f"Product {product_id} found",
        "Product": product_schema.dump(product)
    }), 200
#==================================================================================================
@app.route('/products/<int:product_id>', methods=['PUT'])   #   ---UPDATE PRODUCT---
def update_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.message), 400
    
    product.product_name = product_data['product_name']
    product.price = product_data['price']

    db.session.commit()

    return jsonify({
        "message": "Product updated successfully",
        "Product": product_schema.dump(product)
    }), 200
#==================================================================================================
@app.route('/products/<int:product_id>', methods=['DELETE'])   #   ---DELETE PRODUCT---
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    db.session.delete(product)
    db.session.commit()

    return jsonify({
        "message": "Product deleted successfully",
        "Product": product_schema.dump(product)
    }), 200
#==================================================================================================
#==================================================================================================
#============================== Order CRUD ========================================================
@app.route('/orders', methods=['POST'])  #   ---CREATE ORDER---
def create_order():

    try:
        order_data = request.get_json()
    except ValidationError as e:
        return jsonify(e.message), 400
    
    customer = db.session.get(Customer, order_data['customer_id'])
    
    if not customer:
        return jsonify({"message": "Invalid customer id"}), 400
    
    new_order = Order(order_date=order_data['order_date'], customer_id=order_data['customer_id'])

    for id in order_data['products']:
        product = db.session.get(Product, id)
        if not product:
            return jsonify({"message": f"Invalid product id {id}"}), 400
        new_order.products.append(product)
    
    db.session.add(new_order)
    db.session.commit()

    return jsonify({"Message": "New order created successfully", "order": order_schema.dump(new_order)}), 201
#==================================================================================================
@app.route('/orders/customers/<int:customer_id>', methods=['GET'])   #   ---READ ORDERS -> CUSTOMER---
def get_orders(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"message": "Invalid customer id"}), 400
    
    return jsonify({"orders": f"orders - {orders_schema.dump(customer.orders)}"}), 200
#==================================================================================================
@app.route('/orders/<int:order_id>/products', methods=['GET'])   #   ---READ PRODUCTS -> ORDER---
def get_order(order_id):
    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({"message": "Invalid order id"}), 400
    
    return jsonify({"order": f"products - {products_schema.dump(order.products)}"}), 200
#==================================================================================================
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])  # ---UPDATE PRODUCTS -> ORDER---
def update_order(order_id, product_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, product_id)

    if not order:
        return jsonify({"message": "Invalid order id"}), 400
    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    if product in order.products:
        return jsonify({"message": "duplicate entry of item"}), 400
    
    order.products.append(product)
    db.session.commit()

    return jsonify({
        "message": "Updated order successfully", 
        "order": products_schema.dump(order.products)
    }), 200

#==================================================================================================
@app.route('/orders/<int:order_id>/remove_products', methods=['DELETE'])   #   ---DELETE PRODUCT -> ORDER---
def delete_products(order_id):
    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({"message": "Invalid order id"}), 400
    
    try:
        product_deletion = request.get_json()
    except ValidationError as e:
        return jsonify(e.message), 400
    
    for id in product_deletion['products']:
        product = db.session.get(Product, id)
        if not product:
            return jsonify({"message": "Invalid product id "})
        if product in order.products:
            order.products.remove(product)

    db.session.commit()

    return jsonify({
        "message": "products deleted successfully",
        "Product": products_schema.dump(order.products)
    }), 200            
#==================================================================================================
@app.route('/orders/<int:order_id>/remove_order', methods=['DELETE'])   #   ---DELETE ORDER---
def delete_order(order_id):
    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({"message": "Invalid order id"}), 400
    
    db.session.delete(order)
    db.session.commit()

    return jsonify({
        "message": "Order deleted successfully",
        "Order": order_schema.dump(order)
    }), 200            
#==================================================================================================

if __name__ == '__main__':
    with app.app_context():
        #db.drop_all()
        db.create_all()
    app.run(debug=True, port=5001)
