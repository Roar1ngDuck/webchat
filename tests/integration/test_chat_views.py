import pytest
from app import create_app
from dotenv import load_dotenv

@pytest.fixture(scope='module')
def test_client():
    load_dotenv(dotenv_path='.env.test')
    # Setup Flask test app
    app = create_app()
    # Get a test client for your Flask app
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

def test_register_route(test_client):
    # Test data for a new user
    new_user_data = {
        "username": "testuser",
        "password": "VBt8fETYzn$64ecARjmG",
        "confirm_password": "VBt8fETYzn$64ecARjmG"
    }

    # Test /register route
    response = test_client.post('/register', data=new_user_data, follow_redirects=True)
    print(response)
    assert response.status_code == 200
    assert b"Don't have an account?" in response.data  # Check for a redirect to login page

    # Check if user can login with the new account
    login_response = login(test_client, new_user_data["username"], new_user_data["password"])
    assert login_response.status_code == 200
    assert b"Logged in as" in login_response.data  # Check for a logged in status

def test_create_area_in_index_route(test_client):
    login(test_client, 'testuser', 'VBt8fETYzn$64ecARjmG')

    new_area_data = {"topic": "New Area"}
    response = test_client.post('/', data=new_area_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"New Area" in response.data  # Check if the new area is listed

    logout(test_client)

def test_create_thread_in_view_area_route(test_client):
    login(test_client, 'testuser', 'VBt8fETYzn$64ecARjmG')

    area_id = 1  # Replace with a valid area ID
    new_thread_data = {"title": "New Thread", "message" : "Thread initial message"}
    response = test_client.post(f'/area/{area_id}', data=new_thread_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"New Thread" in response.data  # Check if the new thread is listed
    assert b">1</span>" in response.data # Check if initial message is listed

    logout(test_client)

def test_create_message_in_view_thread_route(test_client):
    login(test_client, 'testuser', 'VBt8fETYzn$64ecARjmG')

    thread_id = 1
    new_message_data = {"message": "New message in thread"}
    response = test_client.post(f'/thread/{thread_id}', data=new_message_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"New message in thread" in response.data  # Check if the new message is listed in the thread

    logout(test_client)
