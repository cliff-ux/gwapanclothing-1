from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure MySQL Connection 
# Format: mysql+pymysql://username:password@localhost/database_name
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:your_password@localhost/gwapaffection_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app = Flask(__name__)

# This goes inside your app.py file:
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://cliff:Muhangani%40001@localhost/gwapaffection_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# 1. Product Model (Replaces hardcoded HTML products)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "image_url": self.image_url,
            "description": self.description
        }

# 2. Order Model (Logs orders before they go to WhatsApp)
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Float, nullable=False)
    order_details = db.Column(db.Text, nullable=False) # JSON string or summary of items
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "total_amount": self.total_amount,
            "order_details": self.order_details,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

# Initialize database tables
with app.app_context():
    db.create_all()

# --- API ROUTES ---

# Get all products to display on your frontend
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

# Save order to database when checkout happens
@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    
    new_order = Order(
        total_amount=data.get('total_amount'),
        order_details=str(data.get('items'))
    )
    
    db.session.add(new_order)
    db.session.commit()
    
    return jsonify({"message": "Order saved successfully!", "order_id": new_order.id}), 201

if __name__ == '__main__':
    app.run(debug=True)