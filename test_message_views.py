"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data



# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.id = 11111

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_no_session(self):
        with self.client as c:
            res = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = res.get_data(as_text = True)

            self.assertEqual(res.status_code,200)
            self.assertIn('Access unauthorized',html)

    def test_add_message_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 543210

            res = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True) 
            html = res.get_data(as_text = True)

            self.assertEqual(res.status_code,200)
            self.assertIn('Access unauthorized',html)

    def test_show_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            m = Message(id=888,  text = 'warble test', user_id = self.testuser.id)
            db.session.add(m)
            db.session.commit()

            m = Message.query.get(m.id)
            res = c.get(f'/messages/{m.id}')
            
            self.assertEqual(res.status_code, 200)
            self.assertIn(m.text, str(res.data))

    def test_delete_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message(id=888, text = 'warble test', user_id = self.testuser.id)
            db.session.add(m)
            db.session.commit()

            res = c.post(f'/messages/888/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            m = Message.query.get(888)
            self.assertIsNone(m)

    def test_delete_message_no_session(self):
        with self.client as c:
            m = Message(id=888, text = 'warble test', user_id = self.testuser.id)
            db.session.add(m)
            db.session.commit()

            res = c.post(f'/messages/888/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))
            m = Message.query.get(888)
            self.assertIsNotNone(m)
    
    def test_delete_message_wrong_user(self):
        # second user to try deletion of tesuser's message
        u = User.signup(username='another-user', password='password', email='anotheruser@email.com', image_url=None)
        u.id = 999
        # message by testuser
        m = Message(id=7890, text = 'warble test', user_id = self.testuser.id)

        db.session.add_all([u, m])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 999
            
            res = c.post(f'/messages/7890/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))
            m = Message.query.get(7890)
            self.assertIsNotNone(m)


