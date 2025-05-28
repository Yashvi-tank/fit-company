import unittest
from src.fit.app import app
from src.fit.database import init_db, db_session
from src.fit.models_db import Base, UserModel
import json
from unittest.mock import patch
import jwt
import datetime

class TestUserAPI(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Set up test database
        init_db()
        self.db = db_session()
        
        # Create a mock admin token
        token_data = {
            "sub": "admin@test.com",
            "name": "Test Admin",
            "role": "admin",
            "iss": "fit-api",
            "iat": datetime.datetime.now(datetime.UTC),
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=30)
        }
        self.admin_token = jwt.encode(token_data, "fit-secret-key", algorithm="HS256")
        
    def tearDown(self):
        # Clean up the database after each test
        self.db.close()
        Base.metadata.drop_all(bind=self.db.get_bind())
        
    def test_create_user_success(self):
        # Test data
        test_user = {
            "email": "test@example.com",
            "password": "securepass123",
            "name": "Test User",
            "role": "user"
        }
        
        # Make the request with admin token
        response = self.client.post(
            '/users',
            data=json.dumps(test_user),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        # Assert response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['email'], test_user['email'])
        self.assertEqual(data['name'], test_user['name'])
        self.assertEqual(data['role'], test_user['role'])
        
    def test_create_user_invalid_data(self):
        # Test with invalid data (missing required fields)
        invalid_user = {
            "email": "invalid_email",  # Invalid email format
            "name": "Test User",
            "role": "user"
        }
        
        # Make the request with admin token
        response = self.client.post(
            '/users',
            data=json.dumps(invalid_user),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        # Assert response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main() 