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

# Route to fetch restaurants by ID
@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    # Retrieve the restaurant from the database by ID
    restaurant = Restaurant.query.get(id)
    
    # If the restaurant is not found, return a 404 error
    if restaurant is None:
        return jsonify({"message": "Restaurant not found"}), 404
    
    # Initialize the restaurant data dictionary
    restaurant_data = {
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address,
        "restaurant_pizzas": []  # Fixed typo: "restaurant_pizzas" instead of "restaurant_pizza"
    }
    return jsonify(restaurant_data), 200
    # # Iterate over the pizzas associated with the restaurant
    # for pizza in restaurant.pizza_set.all():  # Replace with your actual related name or manager method
    #     pizza_data = {
    #         "id": pizza.id,
    #         "pizza": {
    #             "id": pizza.id,
    #             "name": pizza.name,
    #             "ingredients": pizza.ingredients
    #         },
    #         "pizza_id": pizza.id,
    #         "price": pizza.price,
    #         "restaurant_id": restaurant.id
    #     }
    #     restaurant_data["restaurant_pizzas"].append(pizza_data)
        
        # Return the restaurant data as JSON with a 200 status code


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


# Route to create a new RestaurantPizza
@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()
    price = data.get('price')
    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')

    # Check if the required data is provided
    if not all([price, pizza_id, restaurant_id]):
        return jsonify({'errors': ['Missing required data']}), 400

    # Check if the pizza and restaurant exist
    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)
    if not pizza or not restaurant:
        return jsonify({'errors': ['Pizza or restaurant not found']}), 404

    # Create a new RestaurantPizza
    restaurant_pizza = RestaurantPizza(price=price, pizza=pizza, restaurant=restaurant)
    try:
        db.session.add(restaurant_pizza)
        db.session.commit()
    except ValidationError as e:
        return jsonify({'errors': [str(e)]}), 400

    # Prepare the response data
    response_data = {
        'id': restaurant_pizza.id,
        'pizza': {
            'id': pizza.id,
            'ingredients': pizza.ingredients,
            'name': pizza.name
        },
        'pizza_id': pizza_id,
        'price': price,
        'estaurant': {
            'address': restaurant.address,
            'id': restaurant.id,
            'name': restaurant.name
        },
        'estaurant_id': restaurant_id
    }

    return jsonify(response_data), 201

if __name__ == "__main__":
    app.run(port=5555, debug=True)
