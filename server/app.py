#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

# Route to fetch restaurants
@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    # Fetch all restaurants from the database using SQLAlchemy
    restaurants = Restaurant.query.all()

    # Prepare JSON data to return
    restaurant_data = [{
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address
    } for restaurant in restaurants]

    return jsonify(restaurant_data)


# Route to Get restaurant by ID
@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    # Check if the restaurant exists
    restaurant = Restaurant.query.get(id)
    
    if restaurant is None:
        # If restaurant does not exist, return 404 Not Found
        return {
            "error": "Restaurant not found"
        }, 404
    
    # Get associated RestaurantPizzas
    restaurant_pizzas = restaurant.restaurant_pizzas
    
    # Convert Restaurant and RestaurantPizzas to JSON format
    restaurant_json = {
        "address": restaurant.address,
        "id": restaurant.id,
        "name": restaurant.name,
        "restaurant_pizzas": []
    }
    
    for restaurant_pizza in restaurant_pizzas:
        pizza = restaurant_pizza.pizza
        restaurant_pizza_json = {
            "id": restaurant_pizza.id,
            "pizza": {
                "id": pizza.id,
                "ingredients": pizza.ingredients,
                "name": pizza.name
            },
            "pizza_id": restaurant_pizza.pizza_id,
            "price": restaurant_pizza.price,
            "restaurant_id": restaurant_pizza.restaurant_id
        }
        restaurant_json["restaurant_pizzas"].append(restaurant_pizza_json)
    
    # Return JSON data
    return restaurant_json


# Route to Delete restaurant by ID
@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    # Check if the restaurant exists
    restaurant = Restaurant.query.get(id)
    
    if restaurant is None:
        # If restaurant does not exist, return 404 Not Found
        return {
            "error": "Restaurant not found"
        }, 404
    
    # SQLAlchemy ORM delete for associated RestaurantPizzas
    RestaurantPizza.query.filter_by(restaurant_id=id).delete()
    
    # Delete the restaurant
    db.session.delete(restaurant)
    db.session.commit()
    
    # Return 204 No Content response if successful
    return {}, 204


# Route to fetch pizzas
@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    # Fetch all pizzas from the database using SQLAlchemy
    pizzas = Pizza.query.all()

    # Prepare JSON data to return
    pizza_data = [{
        "id": pizza.id,
        "name": pizza.name,
        "ingredients": pizza.ingredients
    } for pizza in pizzas]

    return jsonify(pizza_data)


# Route to update restaurant_pizzas
@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()
    if not data:
        return jsonify({'errors': ['No data provided']}), 400

    price = data.get('price')
    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')

    # Check if the required data is provided
    if not all([price, pizza_id, restaurant_id]):
        return jsonify({'errors': ['Missing data. Please provide price, pizza_id, and restaurant_id.']}), 400

    # Validate price range using model validation
    try:
        validated_price = RestaurantPizza().validate_price(None, price)
    except ValueError as e:
        return jsonify({'errors': [str(e)]}), 400

    # Validate restaurant_id using model validation
    try:
        validated_restaurant_id = RestaurantPizza().validate_restaurant_id(None, restaurant_id)
    except ValueError as e:
        return jsonify({'errors': [str(e)]}), 400


    # Check if the pizza and restaurant exist
    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)
    if not pizza or not restaurant:
        return jsonify({'errors': ['Pizza or Restaurant not found.']}), 404

    # Create a new RestaurantPizza
    restaurant_pizza = RestaurantPizza(price=validated_price, pizza=pizza, restaurant=restaurant)
    try:
        db.session.add(restaurant_pizza)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'errors': [f'Database error: {str(e)}']}), 400

    # Prepare the response data
    response_data = {
        'id': restaurant_pizza.id,
        'pizza': {
            'id': pizza.id,
            'name': pizza.name,
            'ingredients': pizza.ingredients
        },
        'pizza_id': pizza_id,
        'price': validated_price,
        'restaurant': {
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address
        },
        'restaurant_id': restaurant_id
    }

    return jsonify(response_data), 201

if __name__ == "__main__":
    app.run(port=5000, debug=True)
