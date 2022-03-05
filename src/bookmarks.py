from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended.view_decorators import jwt_required
from src.constants.http_status_codes import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_201_CREATED, HTTP_200_OK, \
    HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT
from src.database import Bookmark, db
from flasgger import swag_from
import validators

bookmarks = Blueprint("bookmarks", __name__, url_prefix="/api/v1/bookmarks")


@bookmarks.route('/', methods=['POST', 'GET'])
@jwt_required()
@swag_from('./docs/bookmarks/get_all_bookmarks.yaml', methods=['GET'])
@swag_from('./docs/bookmarks/post_bookmarks.yaml', methods=['POST'])
def handle_bookmarks():
    current_user = get_jwt_identity()

    if request.method == 'POST':

        body = request.get_json().get('body', '')
        url = request.get_json().get('url', '')

        if not validators.url(url):
            return jsonify({'error': 'Must enter a valid url'}), HTTP_400_BAD_REQUEST

        if Bookmark.query.filter_by(url=url).first():
            return jsonify({
                'error': 'URL already exist'
            }), HTTP_409_CONFLICT

        bookmark = Bookmark(url=url, body=body, user_id=current_user)
        db.session.add(bookmark)
        db.session.commit()

        return jsonify({
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "visit": bookmark.visits,
            "body": bookmark.body,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at,
        }), HTTP_201_CREATED

    else:

        page = request.args.get('page', 1, type=int)

        per_page = request.args.get('per_page', 5, type=int)

        all_bookmark = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)

        data = []

        for bookmark in all_bookmark.items:
            data.append({
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "visit": bookmark.visits,
                "body": bookmark.body,
                "created_at": bookmark.created_at,
                "updated_at": bookmark.updated_at,
            })

        meta = {
            "page": all_bookmark.page,
            "pages": all_bookmark.pages,
            "total_count": all_bookmark.total,
            "prev_page": all_bookmark.prev_num,
            "next_page": all_bookmark.next_num,
            "has_next": all_bookmark.has_next,
            "has_prev": all_bookmark.has_prev,
        }

        return jsonify({"data": data, "meta": meta}), HTTP_200_OK


@bookmarks.get('/<int:id>')
@jwt_required()
@swag_from('./docs/bookmarks/get_single_bookmark.yaml')
def get_bookmark(id):

    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

    if not bookmark:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND

    return jsonify({
        "id": bookmark.id,
        "url": bookmark.url,
        "short_url": bookmark.short_url,
        "visit": bookmark.visits,
        "body": bookmark.body,
        "created_at": bookmark.created_at,
        "updated_at": bookmark.updated_at,
    }), HTTP_200_OK


@bookmarks.delete('/<int:id>')
@jwt_required()
@swag_from('./docs/bookmarks/delete_bookmarks.yaml')
def delete_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

    if not bookmark:
        return jsonify({
            "message": "Item not found"
        }), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT


@bookmarks.put('/<int:id>')
@bookmarks.patch('/<int:id>')
@jwt_required()
@swag_from('./docs/bookmarks/put_bookmark.yaml', methods=['PUT'])
@swag_from('./docs/bookmarks/patch_bookmark.yaml', methods=['PATCH'])
def edit_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

    if not bookmark:
        return jsonify({
            'message': 'Item not found'
        }), HTTP_404_NOT_FOUND

    body = request.get_json().get('body', '')
    url = request.get_json().get('url', '')

    if not validators.url(url):
        return jsonify({'error': 'Must enter a valid url'}), HTTP_400_BAD_REQUEST

    bookmark.url = url
    bookmark.body = body

    db.session.commit()

    return jsonify({
        'id': bookmark.id,
        'url': bookmark.url,
        'short_url': bookmark.short_url,
        'visit': bookmark.visits,
        'body': bookmark.body,
        'created_at': bookmark.created_at,
        'updated_at': bookmark.updated_at,
    }), HTTP_200_OK


@bookmarks.get('/stats')
@jwt_required()
@swag_from('./docs/bookmarks/stats.yaml')
def get_stats():

    current_user = get_jwt_identity()

    data = []

    items = Bookmark.query.filter_by(user_id=current_user).all()

    for item in items:
        new_link = {
            'id': item.id,
            'visits': item.visits,
            'short_url': item.short_url,
            'url': item.url
        }

        data.append(new_link)

    return jsonify({'data': data}), HTTP_200_OK
