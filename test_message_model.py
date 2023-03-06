"""Message model tests"""
import os
from unittest import TestCase
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

db.drop_all()
db.create_all()

class MessageModelTestCase(TestCase):
  def setUp(self):
    """Create test client, add sample data."""

    User.query.delete()
    Message.query.delete()
    Follows.query.delete()

    u = User.signup('test', 'test@email.com', 'password', None)
    self.uid = 12345
    u.id = self.uid
    db.session.add(u)
    db.session.commit()

    self.u = User.query.get(u.id)

    self.client = app.test_client()

  def tearDown(self):
    """Clean up any fouled transaction."""
    ### any other teardown the parent/ancestor may have, do it here too.
    res = super().tearDown()
    db.session.rollback()
    return res

  def test_message_model(self):
    m = Message(text='warble test', user_id=self.u.id)
    db.session.add(m)
    db.session.commit()

    self.assertEqual(len(self.u.messages),1)
    self.assertEqual(self.u.messages[0].text, 'warble test')

  def test_message_likes(self):
    m1 = Message(text='warble test', user_id=self.u.id)
    m2 = Message(text='warble to be liked', user_id=self.u.id)
    u2 = User.signup('liker', 'like@email.com', 'password', None)
    u2.id = 54321
    db.session.add_all([m1, m2, u2])
    db.session.commit()

    u2.likes.append(m2)

    self.assertEqual(len(u2.likes), 1)
    self.assertEqual(u2.likes[0].user_id, self.u.id)
    self.assertNotEqual(u2.likes[0].user_id, u2.id)
    self.assertEqual(len(self.u.likes), 0)

