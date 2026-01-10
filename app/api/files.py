from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import FileRecord, FileTransaction, User
from app import db

api = Blueprint("files_api", __name__)

# Helper decorator for admin-only endpoints
def admin_required():
    claims = get_jwt()
    if claims.get("role") != "admin":
        abort(403)

# GET all files
@api.route("/files", methods=["GET"])
@jwt_required()
def api_files():
    files = FileRecord.query.all()
    return jsonify([
        {
            "id": f.id,
            "file_number": f.file_number,
            "title": f.title,
            "department": f.department,
            "is_issued": f.is_issued
        } for f in files
    ])

# GET single file by ID
@api.route("/files/<int:file_id>", methods=["GET"])
@jwt_required()
def api_file_detail(file_id):
    f = FileRecord.query.get_or_404(file_id)
    return jsonify({
        "id": f.id,
        "file_number": f.file_number,
        "title": f.title,
        "department": f.department,
        "is_issued": f.is_issued,
        "transactions": [
            {
                "user": t.user.name,
                "checkout_time": t.checkout_time.isoformat(),
                "return_time": t.return_time.isoformat() if t.return_time else None,
                "purpose": t.purpose,
                "comments": t.comments
            } for t in f.transactions
        ]
    })

# POST: check out a file
@api.route("/files/<int:file_id>/checkout", methods=["POST"])
@jwt_required()
def api_checkout_file(file_id):
    data = request.json
    user_id = get_jwt_identity()

    file = FileRecord.query.get_or_404(file_id)
    if file.is_issued:
        return {"error": "File already issued"}, 400

    tx = FileTransaction(
        file_id=file.id,
        user_id=user_id,
        purpose=data.get("purpose", "")
    )
    db.session.add(tx)
    file.is_issued = True
    db.session.commit()

    return {"status": "checked out", "file_number": file.file_number}, 201

# POST: return a file
@api.route("/files/<int:file_id>/return", methods=["POST"])
@jwt_required()
def api_return_file(file_id):
    data = request.json
    user_id = get_jwt_identity()

    file = FileRecord.query.get_or_404(file_id)
    tx = FileTransaction.query.filter_by(file_id=file.id, user_id=user_id, return_time=None).first()
    if not tx:
        return {"error": "No active checkout found"}, 400

    tx.return_time = data.get("return_time")
    tx.comments = data.get("comments", "")
    file.is_issued = False
    db.session.commit()

    return {"status": "returned", "file_number": file.file_number}, 200
