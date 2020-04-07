"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os

from flask import Flask, request, jsonify, url_for, make_response
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap, send_sms
from models import db
from models import User
from models import Todo
from functools import wraps
import jwt
import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)

CORS(app)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]

        if not token:
            return jsonify({'message' : "Token is missing!"}), 401

        try:
            data = jwt.decode(token, 'secret')
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': "Token is invalid"}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route("/", methods=["GET"])
def get_sitemap():
    return generate_sitemap(app)

@app.route("/user", methods=["GET"])
# @token_required
def get_all_users():
    users = User.query.all()
    users = list(map(lambda x: x.serialize(), users))
    return jsonify(users), 200

@app.route("/user/<public_id>", methods=["GET"])
@token_required
def get_one_user(current_user, public_id):

    if not current_user.admin:
        return jsonify({"message" : "Cannot perform that function!"})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({"message" : "No user found!"})
    
    user_data = {}
    user_data["public_id"] = user.public_id
    user_data["name"] = user.name
    user_data["last_name"] = user.last
    user_data["email"] = user.email
    user_data["password"] = user.password
    user_data["phone"] = user.phone
    user_data["admin"] = user.admin

    return jsonify({"user" : user_data})

@app.route("/user", methods=["POST"])
def create_user():
    data = request.get_json()
    password=data["password"]
    hashed_password = generate_password_hash(password, method="sha256")
    new_user = User(public_id=str(uuid.uuid4()), name=data["name"], last=data["last"], password=hashed_password, email=data["email"], phone=data["phone"], todos=data["todos"], admin=True)
    db.session.add(new_user)
    db.session.commit()

    send_sms("Welcome! " + data["name"],data["phone"])

    return jsonify({"message":"New User Created!"})

@app.route("/user/<public_id>", methods=["PUT"])
@token_required
def promote_user(current_user, public_id):

    if not current_user.admin:
        return jsonify({"message" : "Cannot perform that function!"})

    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({"message" : "No user found!"})
    user.admin = True
    db.session.commit()
    return jsonify({"message" : "The User has been promoted to Admin!"})    

@app.route("/user/<public_id>", methods=["DELETE"])
@token_required
def delete_user(current_user, public_id):

    if not current_user.admin:
        return jsonify({"message" : "Cannot perform that function!"})

    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({"message" : "No user found!"})
    
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message" : "The user has been Deleted forever!"})
@app.route("/login")
def login():
    
    auth = request.authorization
    if not auth or not auth.username or not auth.password:  
        return make_response("Could not verify", 401, {"WWW-Authenticate" : "Basic realm='Login required!'" })

    user = User.query.filter_by(email=auth.username).first()

    if not user:
        return make_response("Could not verify", 401, {"WWW-Authenticate" : "Basic realm='Login required!'" })
        
    if check_password_hash(user.password, auth.password):
        token = jwt.encode({"public_id" : user.public_id, "exp" : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},  'secret')
        return jsonify({"token": token.decode("UTF-8"), "LoggedIn User id": user.id})

    return make_response("Could not verify", 401, {"WWW-Authenticate" : "Basic realm='Login required!'" })

@app.route("/todo", methods=["GET"])
# @token_required
def get_all_todos():
    todos = Todo.query.all()
    todos = list(map(lambda x: x.serialize(), todos))
    return jsonify(todos), 200

@app.route("/todo/<todo_id>", methods=["GET"])
@token_required
def get_one_todo(current_user, todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()

    if not todo:
        return jsonify({"message" : "No such Todo found"})
    
    todo_data = {}
    todo_data["id"] = todo.id
    todo_data["text"] = todo.text
    todo_data["complete"] = todo.complete

    return jsonify(todo_data)

# @app.route("/todo/<user_id>", methods=["PUT"])
# def inbound_sms():
#     response = twiml.Response()
#     # we get the SMS message from the request. we could also get the 
#     # "To" and the "From" phone number as well
#     inbound_message = request.form.get("Body")
#     # we can now use the incoming message text in our Python application
#     #   add a function to trigger the put command to update the most current task to completed array
#     if inbound_message == "task done":
#         response.message("Congrats! Keep going!")
#     else:
#         response.message("Hi! Not quite sure what you meant, Please respond with 'task done' to remove your most current todo!.")
#     # we return back the mimetype because Twilio needs an XML response
#     return Response(str(response), mimetype="application/xml"), 200

@app.route("/todo/<user_id>", methods=["POST"])
# @token_required
def create_todo(user_id):
    data = request.get_json()
    print(user_id)
    new_todo = Todo(text=data["text"], complete=False, user_id=user_id, dueDate=data["dueDate"], createdDate=data["createdDate"])
    db.session.add(new_todo)
    db.session.commit()
    user = User.query.filter_by(id=user_id).first()
    send_sms("New task added! " + data["text"] + " " + data["dueDate"], user.phone)

    return jsonify({"message" : "Todo created!"})

@app.route("/todo/<todo_id>", methods=["PUT"])
@token_required
def complete_todo(current_user, todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    print(todo)
    if not todo:
        return jsonify({"message" : "No such Todo found"})

    todo.complete = True
    
    db.session.commit()

    return jsonify({"message" : "Todo Marked completed =) Well done!"})

@app.route("/todo/<todo_id>", methods=["DELETE"])
@token_required
def delete_todo(current_user, todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()

    if not todo:
        return jsonify({"message" : "No such Todo found"})

    db.session.delete(todo)
    db.session.commit()

    return jsonify ({"message" : "Successfully deleted the Todo item! Great!"})

# # generate sitemap with all your endpoints
# @app.route('/')
# def sitemap():
#     return generate_sitemap(app)

# @app.route('/hello', methods=['POST', 'GET'])
# def handle_hello():

#     response_body = {
#         "hello": "world"
#     }

#     return jsonify(response_body), 200

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
