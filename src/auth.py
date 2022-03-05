from flask import Blueprint, request, jsonify
from src.constants.http_status_codes import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_201_CREATED, \
    HTTP_401_UNAUTHORIZED, HTTP_200_OK
from werkzeug.security import check_password_hash, generate_password_hash
from src.database import User, db
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from flask_jwt_extended.view_decorators import jwt_required
from flasgger import swag_from
import validators

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth.post('/register')
@swag_from('./docs/auth/register.yaml')
def register():
    """
    Registration for user with valid credentials and store information to database
    :return: json
    """
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    # check if password is less than 6
    if len(password) < 6:
        return jsonify({'error': 'Password is too short'}), HTTP_400_BAD_REQUEST

    # check if username is less than 3 characters
    if len(username) < 3:
        return jsonify({'error': 'Username is too short'}), HTTP_400_BAD_REQUEST

    # check if username is alphanumerical and there is no space
    if not username.isalnum() or " " in username:
        return jsonify({'error': 'Username should be alphanumeric and space is not allowed'}), HTTP_400_BAD_REQUEST

    # check if email is valid and that email is not taken
    if not validators.email(email):
        return jsonify({'error': 'Email has taken'}), HTTP_409_CONFLICT

    # check if email is not in database
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'Email is not valid'}), HTTP_400_BAD_REQUEST

    # check
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'error': 'Username is taken'}), HTTP_409_CONFLICT

    # hashing password
    pwd_hash = generate_password_hash(password)

    user = User(username=username, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User created!',
        'user': {
            'username': username, 'email': email
        }
    }), HTTP_201_CREATED


@auth.post('/login')
@swag_from('./docs/auth/login.yaml')
def login():
    """
    User logs into with valid credentials and user is given refresh and access token
    :return: json
    """
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = User.query.filter_by(email=email).first()

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            refresh_t = create_refresh_token(identity=user.id)
            access_t = create_access_token(identity=user.id)

            return jsonify({
                'user': {
                    'refresh token': refresh_t,
                    'access token': access_t,
                    'username': user.username,
                    'email': user.email
                }
            }), HTTP_201_CREATED

    return jsonify({'error': 'Wrong credentials'}), HTTP_401_UNAUTHORIZED


@auth.get('/me')
@jwt_required()
def me():

    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    return jsonify({
        'username': user.username,
        'email': user.email
    }), HTTP_200_OK


@auth.get('/token/refresh')
@jwt_required(refresh=True)  # requires refresh token
@swag_from('./docs/auth/refresh_token.yaml')
def refresh_users_token():
    """
    Refreshes user's access token
    :return: json
    """
    user_id = get_jwt_identity()
    access_t = create_access_token(identity=user_id)

    return jsonify({
        'new access token': access_t
    }), HTTP_200_OK
