"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u1 = User.signup('test1', 'test1@email.com', 'test1', None)
        u1.id = 11111
        u2 = User.signup('test2', 'test2@email.com', 'test2', None)
        u2.id = 22222
        db.session.commit()

        u1 = User.query.get(u1.id)
        u2 = User.query.get(u2.id)

        self.u1 = u1
        self.u1.id = u1.id
        self.u2 = u2
        self.u2.id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
    
    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()
        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        # Test repr method
        self.assertEqual(repr(u), f'<User #{u.id}: testuser, test@test.com>')
    
    ###### Test follows
    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following),1)
        self.assertEqual(len(self.u2.following),0)
        self.assertEqual(self.u1.following[0].id, self.u2.id)
        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.followers),0)
        self.assertEqual(len(self.u2.followers),1)
        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    ###### Test authentication
    def test_valid_authentiation(self):
        u = User.authenticate(self.u1.username, 'test1')
        self.assertIsNotNone(u)
        self.assertEqual(self.u1.id, u.id)

    def test_invalid_password(self):
        u = User.authenticate(self.u1.username, 'invalidpassword')  
        self.assertFalse(u) 
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate('invaliduser', 'test1'))
    
    ###### Test signup
    def test_valid_signup(self):
        test_user = User.signup('testuser','test@email.com','testpassword', None)
        test_user_id = 99999
        test_user.id = test_user_id
        db.session.commit()

        test_user = User.query.get(test_user_id)
        self.assertIsNotNone(test_user)
        self.assertEqual(test_user.username, 'testuser')
        self.assertEqual(test_user.email, 'test@email.com')
        self.assertNotEqual(test_user.password, 'testpassword')
        self.assertTrue(test_user.password.startswith('$2b$'))
    
    def test_invalid_username_signup(self):
        invalid_username = User.signup(None, 'test@email.com', 'testpassword', None)
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_duplicate_username_signup(self):
        duplicate_username = User.signup('test1', 'test@email.com', 'test', None)
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid_email = User.signup('test', None, 'testpassword', None)
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError):
            User.signup('test', 'test@email.com', None, None)
        with self.assertRaises(ValueError):
            User.signup('test', 'test@email.com', "", None)



        #Rethink setup
        
    