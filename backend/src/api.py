import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES
@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()

    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks] # return list of drinks with short representation
    }), 200

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()

    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in drinks] # return list of drinks with long representation
    }), 200

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks') # check for permission
def create_drink(payload):
    body = request.get_json()

    if body is None:
        abort(400)

    try:
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)

        drink = Drink(title=new_title, recipe=json.dumps(new_recipe))

        drink.insert()

        return jsonify({
			'success': True,
			'drinks': [drink.long()] # return a list contatining only the created drink
		}), 200

    except:
        abort(422)

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks') # check for permission
def update_drink(payload, id):
    body = request.get_json()

    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(404)

        updated_title = body.get('title', None)
        updated_recipe = body.get('recipe', None)
        
        if updated_title: # check if title was updated
            drink.title = updated_title

        if updated_recipe: # check if recipe is updated
            drink.recipe = json.dumps(updated_recipe) # convert the list of ingredients in the recipe to a string before updating it in the databse

        drink.update()

        return jsonify({
			'success': True,
			'drinks': [drink.long()] # return a list contatining only the updated drink
		}), 200

    except:
        abort(400)

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks') # check for permission
def delete_drink(payload, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if drink is None:
            abort(404)

        drink.delete()

        return jsonify({
            'success': True,
            'delete': id
        })

    except:
      abort(422)



## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
    }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
    }), 404

@app.errorhandler(AuthError)
def auth_error(AuthError): 
    return jsonify({
            "success": False, 
            "error": AuthError.status_code,
            "message": AuthError.error['description']
    }), AuthError.status_code