from flask import Blueprint
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment
from core.libs.exceptions import FyleError
from marshmallow import ValidationError
import logging
from .schema import AssignmentSchema, AssignmentSubmitSchema

student_assignments_resources = Blueprint('student_assignments_resources', __name__)


@student_assignments_resources.route('/assignments', methods=['GET'], strict_slashes=False)
@decorators.authenticate_principal
def list_assignments(p):
    """Returns list of assignments"""
    students_assignments = Assignment.get_assignments_by_student(p.student_id)
    students_assignments_dump = AssignmentSchema().dump(students_assignments, many=True)
    return APIResponse.respond(data=students_assignments_dump)


@student_assignments_resources.route('/assignments', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def upsert_assignment(p, incoming_payload):
    """Create or Edit an assignment"""
    try:
        assignment = AssignmentSchema().load(incoming_payload)
    except ValidationError as err:
        return APIResponse.error(err.messages, 400)
    
    if not assignment.content:
        return APIResponse.error("Content cannot be null", 400)
    
    assignment.student_id = p.student_id
    upserted_assignment = Assignment.upsert(assignment)
    db.session.commit()
    upserted_assignment_dump = AssignmentSchema().dump(upserted_assignment)
    return APIResponse.respond(data=upserted_assignment_dump)

@student_assignments_resources.route('/assignments/submit', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def submit_assignment(p, incoming_payload):
    """Submit an assignment"""
    try:
        submit_assignment_payload = AssignmentSubmitSchema().load(incoming_payload)
        logging.info(f"Received payload: {submit_assignment_payload}")
        
        submitted_assignment = Assignment.submit(
            _id=submit_assignment_payload.id,
            teacher_id=submit_assignment_payload.teacher_id,
            auth_principal=p
        )
        db.session.commit()
        
        submitted_assignment_dump = AssignmentSchema().dump(submitted_assignment)
        logging.info(f"Assignment submitted successfully: {submitted_assignment_dump}")
        return APIResponse.respond(data=submitted_assignment_dump)
    
    except ValidationError as err:
        logging.error(f"Validation error: {err.messages}")
        return APIResponse.error(message=err.messages, status=400)
    except FyleError as e:
        logging.error(f"FyleError: {str(e)}")
        return APIResponse.error(message=str(e), status=400)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return APIResponse.error(message="An unexpected error occurred", status=500)

# Assignment model methods

@staticmethod
def get_assignments_by_student(student_id):
    """Fetch assignments by student ID"""
    return Assignment.query.filter_by(student_id=student_id).all()

@staticmethod
def upsert(assignment):
    """Create or update an assignment"""
    if assignment.id:
        existing_assignment = Assignment.query.filter_by(id=assignment.id).first()
        existing_assignment.content = assignment.content
        return existing_assignment
    db.session.add(assignment)
    return assignment

@staticmethod
def submit(_id, teacher_id, auth_principal):
    """Submit an assignment with teacher ID"""
    assignment = Assignment.query.filter_by(id=_id, student_id=auth_principal.student_id).first()
    if assignment.state != 'DRAFT':
        raise FyleError(message='only a draft assignment can be submitted', status_code=400)
    assignment.teacher_id = teacher_id
    assignment.state = 'SUBMITTED'
    return assignment
