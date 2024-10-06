from flask import Blueprint, jsonify, request
from core.models import db, Teacher  # Ensure you have the Teacher model imported
from core.libs.exceptions import FyleError

principal_teachers_resources = Blueprint('principal_teachers_resources', __name__)

@principal_teachers_resources.route('/teachers', methods=['GET'])
def get_teachers():
    try:
        # Query the database to get all teachers
        teachers = Teacher.query.all()
        data = [{
            'id': teacher.id,
            'created_at': teacher.created_at.isoformat(),
            'updated_at': teacher.updated_at.isoformat(),
            'user_id': teacher.user_id
        } for teacher in teachers]

        return jsonify({'data': data}), 200
    except Exception as e:
        raise FyleError(str(e), status_code=500)
