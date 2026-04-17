import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_get_todos_empty(client):
    response = client.get('/todos')
    assert response.status_code == 200
    assert response.get_json() == []

def test_create_todo_success(client):
    response = client.post('/todos', json={'title': 'Test Todo'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == 'Test Todo'
    assert data['completed'] is False
    assert 'id' in data

def test_create_todo_missing_title(client):
    response = client.post('/todos', json={})
    assert response.status_code == 400

def test_get_todo_by_id_found(client):
    # First, create a todo
    post_response = client.post('/todos', json={'title': 'Find Me'})
    todo_id = post_response.get_json()['id']
    # Retrieve the created todo
    get_response = client.get(f'/todos/{todo_id}')
    assert get_response.status_code == 200
    data = get_response.get_json()
    assert data['id'] == todo_id
    assert data['title'] == 'Find Me'

def test_get_todo_by_id_not_found(client):
    response = client.get('/todos/999')
    assert response.status_code == 404

def test_update_todo_success(client):
    # Create a todo
    post_response = client.post('/todos', json={'title': 'Update Me'})
    todo_id = post_response.get_json()['id']
    # Update the todo
    response = client.put(f'/todos/{todo_id}', json={'title': 'Updated Title', 'completed': True})
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == todo_id
    assert data['title'] == 'Updated Title'
    assert data['completed'] is True

def test_update_todo_not_found(client):
    response = client.put('/todos/999', json={'title': 'Nope'})
    assert response.status_code == 404

def test_delete_todo_success(client):
    # Create a todo
    post_response = client.post('/todos', json={'title': 'Delete Me'})
    todo_id = post_response.get_json()['id']
    # Delete the todo
    response = client.delete(f'/todos/{todo_id}')
    assert response.status_code == 204
    # Verify deletion
    get_response = client.get(f'/todos/{todo_id}')
    assert get_response.status_code == 404

def test_delete_todo_not_found(client):
    response = client.delete('/todos/999')
    assert response.status_code == 404