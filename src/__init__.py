from flask import Flask, redirect
from flask.json import jsonify
from src.auth import auth
from src.bookmarks import bookmarks
from src.database import db, Bookmark
from flask_jwt_extended import JWTManager
from flasgger import Swagger, swag_from  # enables us to create yaml file where we can describe the spec
from src.constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from src.config.swagger import template, swagger_config
import os


def create_app(test_config=None):
    """ Construct core application with application factory"""
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:

        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY'),
            SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DB_URI'),
            SQLALCHEMY_TRACK_MODIFICATIONS=os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS'),
            JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY'),
            SWAGGER={
                'title': 'Bookmarks API',
                'uiversion': 3
            }

        )

        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookmark.db'

    else:
        app.config.from_mapping(test_config)

    db.init_app(app)

    JWTManager(app)
    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    # Configure swagger
    Swagger(app, config=swagger_config, template=template)

    @app.get('/<short_url>')
    @swag_from('./docs/short_url.yaml')
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()

        if bookmark:
            bookmark.visits += 1
            db.session.commit()

            return redirect(bookmark.url)

    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        """
        Provide error handling for code 404
        :param e:
        :return: json
        """
        return jsonify({"error": "Not found"}), HTTP_404_NOT_FOUND

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_500(e):
        """
        Provide error handling for code 500
        :param e:
        :return: json
        """
        return jsonify({"error": "Interval server error. Try again."}), HTTP_500_INTERNAL_SERVER_ERROR

    return app
