import requests

session = requests.Session()
# Login first
login_data = {
    'username': 'admin', # Assuming admin is the username, I will check create_test_user.py
    'password': 'password'
}
# Wait, do I need CSRF?
# Let's bypass login by just setting the session cookie if we can, or just look at what the server logs say.
