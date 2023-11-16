import pytest
from app import create_app
from dotenv import load_dotenv

@pytest.fixture(scope='module')
def test_client():
    load_dotenv(dotenv_path='.env.test')
    # Setup Flask test app
    app = create_app()
    # Get a test client for the Flask app
    testing_client = app.test_client()

    # Establish an application context
    ctx = app.app_context()
    ctx.push()

    yield testing_client

    ctx.pop()

def login(test_client, username, password):
    return test_client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def logout(test_client):
    return test_client.get('/logout', follow_redirects=True)

def test_register(test_client):
    new_user_data = {
        "username": "testuser1",
        "password": "VBt8fETYzn$64ecARjmG",
        "confirm_password": "VBt8fETYzn$64ecARjmG"
    }

    response = test_client.post('/register', data=new_user_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Don't have an account?" in response.data  # Check for a redirect to login page

    login_response = login(test_client, new_user_data["username"], new_user_data["password"])
    assert login_response.status_code == 200
    assert b"Logged in as" in login_response.data  # Check for a logged in status

def test_register_weak_password(test_client):
    new_user_data = {
        "username": "testuser2",
        "password": "password123",
        "confirm_password": "password123"
    }

    response = test_client.post('/register', data=new_user_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Password is too weak" in response.data

def test_register_unmatching_password(test_client):
    new_user_data = {
        "username": "testuser3",
        "password": "VBt8fETYzn$64ecARjmG",
        "confirm_password": "wc5rd6ePdLHct&5EM3i3"
    }

    response = test_client.post('/register', data=new_user_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Passwords don" in response.data


def test_create_area_in_index_route(test_client):
    login(test_client, 'testuser1', 'VBt8fETYzn$64ecARjmG')

    new_area_data = {"topic": "Test Area 123"}
    response = test_client.post('/', data=new_area_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Test Area 123" in response.data  # Check if the new area is listed

    logout(test_client)

def test_create_thread_in_view_area_route(test_client):
    login(test_client, 'testuser1', 'VBt8fETYzn$64ecARjmG')

    area_id = 1
    new_thread_data = {"title": "Test Thread 123", "message" : "Thread initial message"}
    response = test_client.post(f'/area/{area_id}', data=new_thread_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Test Thread 123" in response.data  # Check if the new thread is listed
    assert b">1</span>" in response.data # Check if initial message is listed

    logout(test_client)

def test_create_message_in_view_thread_route(test_client):
    login(test_client, 'testuser1', 'VBt8fETYzn$64ecARjmG')

    thread_id = 1
    new_message_data = {"message": "New message in thread"}
    response = test_client.post(f'/thread/{thread_id}', data=new_message_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"New message in thread" in response.data  # Check if the new message is listed in the thread

    logout(test_client)
