import enum
from core import db
from core.apis.decorators import AuthPrincipal
from core.libs import helpers, assertions
from core.models.teachers import Teacher
from core.models.students import Student
from sqlalchemy.types import Enum as BaseEnum
from core.libs.exceptions import FyleError
import logging
from marshmallow import ValidationError

class GradeEnum(str, enum.Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'


class AssignmentStateEnum(str, enum.Enum):
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    GRADED = 'GRADED'


class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, db.Sequence('assignments_id_seq'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey(Student.id), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey(Teacher.id), nullable=True)
    content = db.Column(db.Text)
    grade = db.Column(BaseEnum(GradeEnum), nullable=True)
    state = db.Column(BaseEnum(AssignmentStateEnum), default=AssignmentStateEnum.DRAFT, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=helpers.get_utc_now, nullable=False)
    updated_at = db.Column(db.TIMESTAMP(timezone=True), default=helpers.get_utc_now, nullable=False, onupdate=helpers.get_utc_now)

    def __repr__(self):
        return '<Assignment %r>' % self.id

    @classmethod
    def filter(cls, *criterion):
        db_query = db.session.query(cls)
        return db_query.filter(*criterion)

    @classmethod
    def get_by_id(cls, _id):
        return cls.filter(cls.id == _id).first()

    @classmethod
    def upsert(cls, assignment_new: 'Assignment'):
        if assignment_new.id is not None:
            assignment = Assignment.get_by_id(assignment_new.id)
            assertions.assert_found(assignment, 'No assignment with this id was found')
            assertions.assert_valid(assignment.state == AssignmentStateEnum.DRAFT,
                                    'Only assignments in draft state can be edited')

            assignment.content = assignment_new.content
        else:
            assignment = assignment_new
            db.session.add(assignment_new)

        db.session.flush()
        return assignment

    @staticmethod
    def submit(_id, teacher_id, auth_principal):
        """Submit an assignment with teacher ID"""
        assignment = Assignment.query.filter_by(id=_id, student_id=auth_principal.student_id).first()
        logging.info(f"Attempting to submit assignment: {assignment}")
        
        if not assignment:
            logging.error(f"Assignment not found: id={_id}, student_id={auth_principal.student_id}")
            raise FyleError(message="Assignment not found")
        
        if assignment.state != 'DRAFT':
            logging.error(f"Invalid assignment state: {assignment.state}")
            raise FyleError(message="Only a draft assignment can be submitted")
        
        assignment.teacher_id = teacher_id
        assignment.state = 'SUBMITTED'
        logging.info(f"Assignment submitted successfully: {assignment}")
        return assignment

    @classmethod
    def get_assignments_by_student(cls, student_id):
        return cls.filter(cls.student_id == student_id).all()

    @classmethod
    def get_assignments_by_teacher(cls, teacher_id):
        """Fetch assignments by teacher ID"""
        return cls.filter(cls.teacher_id == teacher_id, cls.state.in_([AssignmentStateEnum.SUBMITTED, AssignmentStateEnum.GRADED])).all()

    @classmethod
    def mark_grade(cls, _id, grade, auth_principal: AuthPrincipal):
        try:
            assignment = cls.get_by_id(_id)
            if not assignment:
                raise FyleError("No assignment with this id was found", status_code=404)
            
            if hasattr(auth_principal, 'teacher_id'):
                # Teacher grading
                if assignment.teacher_id != auth_principal.teacher_id:
                    raise FyleError("This assignment is not assigned to you", status_code=400)
            
            if assignment.state != AssignmentStateEnum.SUBMITTED:
                raise FyleError("Only submitted assignments can be graded", status_code=400)
            
            if not isinstance(grade, str) or grade not in GradeEnum.__members__:
                raise ValidationError("Invalid grade. Allowed grades are A, B, C, D")

            assignment.grade = grade
            assignment.state = AssignmentStateEnum.GRADED
            
            return assignment
        except (ValidationError, FyleError):
            raise
        except Exception as e:
            logging.error(f"Unexpected error in mark_grade: {str(e)}")
            raise FyleError(str(e), status_code=500)