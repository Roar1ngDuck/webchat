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
    assert b"Password too weak" in response.data


def test_register_unmatching_password(test_client):
    new_user_data = {
        "username": "testuser3",
        "password": "VBt8fETYzn$64ecARjmG",
        "confirm_password": "wc5rd6ePdLHct&5EM3i3"
    }

    response = test_client.post('/register', data=new_user_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Passwords don" in response.data


def test_create_area(test_client):
    new_area_data = {"topic": "Test Area 123"}
    response = test_client.post('/create_area', data=new_area_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Test Area 123" in response.data  # Check if the new area is listed


def test_create_invalid_area(test_client):
    new_area_data = {"topic": "A" * 100}
    response = test_client.post('/create_area', data=new_area_data, follow_redirects=True)

    assert b"Invalid area topic" in response.data  # Check if the new area is listed


def test_view_nonexistent_area(test_client):
    response = test_client.get('/area/100', follow_redirects=True)

    assert b"Area does not exist" in response.data


def test_create_thread(test_client):
    new_thread_data = {"title": "Test Thread 123", "message": "Thread initial message"}
    response = test_client.post('/area/1/create_thread', data=new_thread_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Test Thread 123" in response.data  # Check if the new thread is listed
    assert b">1</span>" in response.data  # Check if initial message is listed


def test_create_invalid_thread(test_client):
    new_thread_data = {"title": "A" * 100, "message": "Thread initial message"}
    response = test_client.post('/area/1/create_thread', data=new_thread_data, follow_redirects=True)

    assert b"Invalid thread title" in response.data


def test_view_nonexistent_thread(test_client):
    response = test_client.get('/thread/100', follow_redirects=True)

    assert b"Thread does not exist" in response.data


def test_send_message(test_client):
    new_message_data = {"message": "New message in thread"}
    response = test_client.post('/thread/1/send_message', data=new_message_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"New message in thread" in response.data  # Check if the new message is listed in the thread


def test_send_invalid_message(test_client):
    new_message_data = {"message": "A" * 2000}
    response = test_client.post('/thread/1/send_message', data=new_message_data, follow_redirects=True)

    assert b"Invalid message" in response.data


def test_search(test_client):
    response = test_client.get('/search?query=t', follow_redirects=True)

    assert b"Test Area 123" in response.data
    assert b"Test Thread 123" in response.data
    assert b"Thread initial message" in response.data
    assert b"New message in thread" in response.data


def test_delete_message(test_client):
    response = test_client.post('/delete_message/1/1', follow_redirects=True)

    assert response.status_code == 200
    assert b"Thread initial message" not in response.data


def test_delete_thread(test_client):
    response = test_client.post('/delete_thread/1', data={}, follow_redirects=True)

    assert response.status_code == 200
    assert b"Test Thread 123" not in response.data
