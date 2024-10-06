from flask import Blueprint, request, jsonify
from core.models.assignments import Assignment, AssignmentStateEnum, GradeEnum
from core.models.teachers import Teacher
from core.libs.helpers import get_json_from_header
from core import db
import json
from core.apis.decorators import AuthPrincipal
from marshmallow import ValidationError
from core.libs.exceptions import FyleError
import logging

# Change the name to reflect its purpose
principal_routes = Blueprint('principal_routes', __name__)

@principal_routes.route('/assignments', methods=['GET'])
def get_assignments():
    headers = request.headers.get('X-Principal')
    principal_info = get_json_from_header(headers)
    
    assignments = Assignment.query.filter(Assignment.state.in_([AssignmentStateEnum.SUBMITTED.value, AssignmentStateEnum.GRADED.value])).all()
    data = [
        {
            "id": assignment.id,
            "content": assignment.content,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at,
            "grade": assignment.grade,
            "state": assignment.state,
            "student_id": assignment.student_id,
            "teacher_id": assignment.teacher_id
        }
        for assignment in assignments
    ]
    return jsonify({"data": data}), 200

@principal_routes.route('/teachers', methods=['GET'])
def get_teachers():
    headers = request.headers.get('X-Principal')
    principal_info = get_json_from_header(headers)
    
    teachers = Teacher.query.all()
    data = [
        {
            "id": teacher.id,
            "user_id": teacher.user_id,
            "created_at": teacher.created_at,
            "updated_at": teacher.updated_at
        }
        for teacher in teachers
    ]
    return jsonify({"data": data}), 200

@principal_routes.route('/assignments/grade', methods=['POST'])
def grade_assignment():
    try:
        principal_header = request.headers.get('X-Principal')
        if not principal_header:
            return jsonify({"error": "Missing X-Principal header"}), 400

        principal_data = json.loads(principal_header)
        auth_principal = AuthPrincipal(principal_data)
        
        payload = request.json
        assignment_id = payload.get('id')
        new_grade = payload.get('grade')

        if not assignment_id or not new_grade:
            return jsonify({"error": "Assignment ID and grade are required"}), 400

        graded_assignment = Assignment.mark_grade(
            _id=assignment_id,
            grade=new_grade,
            auth_principal=auth_principal
        )
        
        db.session.commit()
        
        data = {
            "id": graded_assignment.id,
            "content": graded_assignment.content,
            "created_at": graded_assignment.created_at.isoformat(),
            "updated_at": graded_assignment.updated_at.isoformat(),
            "grade": graded_assignment.grade,
            "state": graded_assignment.state,
            "student_id": graded_assignment.student_id,
            "teacher_id": graded_assignment.teacher_id
        }
        return jsonify({"data": data}), 200
    except ValidationError as e:
        db.session.rollback()
        return jsonify({"error": str(e), "error_type": "ValidationError"}), 400
    except FyleError as e:
        db.session.rollback()
        return jsonify({"error": str(e), "error_type": "FyleError"}), e.status_code
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in principal grade_assignment: {str(e)}")
        return jsonify({"error": "An unexpected error occurred", "error_type": "InternalServerError"}), 500

