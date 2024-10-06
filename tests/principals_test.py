import json
import pytest
from core.models.assignments import Assignment, AssignmentStateEnum, GradeEnum
from core import db

@pytest.fixture
def h_principal():
    return {
        'X-Principal': json.dumps({"user_id": 1, "student_id": 1})
    }

def test_get_assignments(client, h_principal):
    response = client.get(
        '/principal/assignments',
        headers=h_principal
    )

    assert response.status_code == 200

    data = response.json['data']
    for assignment in data:
        assert assignment['state'] in [AssignmentStateEnum.SUBMITTED.value, AssignmentStateEnum.GRADED.value]

def test_get_teachers(client, h_principal):
    response = client.get(
        '/principal/teachers',
        headers=h_principal
    )

    assert response.status_code == 200

    data = response.json['data']
    assert isinstance(data, list)
    for teacher in data:
        assert 'id' in teacher
        assert 'created_at' in teacher
        assert 'updated_at' in teacher
        assert 'user_id' in teacher

def test_grade_assignment_draft_assignment(client, h_principal):
    """
    failure case: If an assignment is in Draft state, it cannot be graded by principal
    """
    response = client.post(
        '/principal/assignments/grade',
        json={
            'id': 5,
            'grade': GradeEnum.A.value
        },
        headers=h_principal
    )

    assert response.status_code == 400

def submit_assignment(client, h_principal, assignment_id):
    """Helper function to ensure assignment is submitted before testing grading"""
    response = client.post(
        '/student/assignments/submit',
        headers=h_principal,
        json={
            "id": assignment_id,
            "teacher_id": 1
        }
    )
    assert response.status_code == 200
    return response

def test_grade_assignment(client, h_principal):
    # Ensure the assignment is in DRAFT state
    assignment = Assignment.get_by_id(4)
    if assignment.state != AssignmentStateEnum.DRAFT:
        assignment.state = AssignmentStateEnum.DRAFT
        db.session.commit()

    # Submit the assignment
    submit_response = submit_assignment(client, h_principal, assignment_id=4)
    assert submit_response.status_code == 200
    
    # Then try to grade it
    response = client.post(
        '/principal/assignments/grade',
        json={
            'id': 4,
            'grade': GradeEnum.C.value
        },
        headers=h_principal
    )
    print(response.json)  # This will print the error message if there is one.
    
    assert response.status_code == 200
    assert response.json['data']['state'] == AssignmentStateEnum.GRADED.value
    assert response.json['data']['grade'] == GradeEnum.C.value

def test_regrade_assignment(client, h_principal):
    # Ensure the assignment is in DRAFT state
    assignment = Assignment.get_by_id(4)
    if assignment.state != AssignmentStateEnum.DRAFT:
        assignment.state = AssignmentStateEnum.DRAFT
        db.session.commit()

    # Submit the assignment
    submit_response = submit_assignment(client, h_principal, assignment_id=4)
    assert submit_response.status_code == 200
    
    # Grade the assignment
    grade_response = client.post(
        '/principal/assignments/grade',
        json={
            'id': 4,
            'grade': GradeEnum.C.value
        },
        headers=h_principal
    )
    assert grade_response.status_code == 200
    
    # Then try to regrade it
    response = client.post(
        '/principal/assignments/grade',
        json={
            'id': 4,
            'grade': GradeEnum.B.value
        },
        headers=h_principal
    )
    print(response.json)  # This will print the error message if there is one.
    
    assert response.status_code == 400  # Expecting a bad request because we can't regrade
    assert 'error' in response.json
    assert 'Only submitted assignments can be graded' in response.json['error']