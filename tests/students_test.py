def test_get_assignments_student_1(client, h_student_1):
    response = client.get(
        '/student/assignments',
        headers=h_student_1
    )

    assert response.status_code == 200

    data = response.json['data']
    for assignment in data:
        assert assignment['student_id'] == 1


def test_get_assignments_student_2(client, h_student_2):
    response = client.get(
        '/student/assignments',
        headers=h_student_2
    )

    assert response.status_code == 200

    data = response.json['data']
    for assignment in data:
        assert assignment['student_id'] == 2


def test_post_assignment_null_content(client, h_student_1):
    """
    failure case: content cannot be null
    """
    response = client.post(
        '/student/assignments',
        headers=h_student_1,
        json={
            'content': None
        })

    assert response.status_code == 400
    assert 'Content cannot be empty or null' in response.json['message']['content'][0]


def test_submit_assignment_student_1(client, h_student_1):
    # First, create a new assignment
    create_response = client.post(
        '/student/assignments',
        headers=h_student_1,
        json={
            'content': 'Test assignment content'
        }
    )
    assert create_response.status_code == 200
    new_assignment_id = create_response.json['data']['id']

    # Now, submit the newly created assignment
    submit_response = client.post(
        '/student/assignments/submit',
        headers=h_student_1,
        json={
            'id': new_assignment_id,
            'teacher_id': 2
        }
    )
    
    assert submit_response.status_code == 200
    print(f"Response JSON: {submit_response.json}")  # Add this line for debugging
    assert submit_response.json['data']['state'] == 'SUBMITTED'
    assert submit_response.json['data']['teacher_id'] == 2


def test_submit_assignment_student_1(client, h_student_1):
    # First, create a new assignment
    create_response = client.post(
        '/student/assignments',
        headers=h_student_1,
        json={
            'content': 'Test assignment content'
        }
    )
    assert create_response.status_code == 200
    new_assignment_id = create_response.json['data']['id']

    # Now, submit the newly created assignment
    submit_response = client.post(
        '/student/assignments/submit',
        headers=h_student_1,
        json={
            'id': new_assignment_id,
            'teacher_id': 2
        }
    )
    
    assert submit_response.status_code == 200
    print(f"Response JSON: {submit_response.json}")  # Add this line for debugging
    assert submit_response.json['data']['state'] == 'SUBMITTED'
    assert submit_response.json['data']['teacher_id'] == 2

def test_assignment_resubmit_error(client, h_student_1):
    # First, submit the assignment
    client.post(
        '/student/assignments/submit',
        headers=h_student_1,
        json={
            'id': 2,
            'teacher_id': 2
        })
    
    # Then, try to resubmit the same assignment
    response = client.post(
        '/student/assignments/submit',
        headers=h_student_1,
        json={
            'id': 2,
            'teacher_id': 2
        })
    
    assert response.status_code == 400
    assert 'Only a draft assignment can be submitted' in response.json['message']
