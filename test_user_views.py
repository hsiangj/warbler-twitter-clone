"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

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


class UserViewTestCase(TestCase):
    
    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.test = User.signup(username="test", email="test@test.com", password="test", image_url=None)
        self.test.id=11111
        self.u2 = User.signup(username='u2', email='u2@test.com',password='password', image_url=None)
        self.u2.id=22222
        self.u3 = User.signup(username='u3',email='u3@test.com',password='password', image_url=None)
        self.u3.id=33333
        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_user_list(self):
        with self.client as c:
          res = c.get('/users')

          self.assertEqual(res.status_code, 200)
          self.assertIn('@test', str(res.data))
          self.assertIn('@u2', str(res.data))
          self.assertIn('@u3', str(res.data))
    
    def test_user_search(self):
        with self.client as c:
          res = c.get('/users?q=test')

          self.assertEqual(res.status_code, 200)
          self.assertNotIn('@u2', str(res.data))
          self.assertNotIn('@u3', str(res.data))
          self.assertIn('@test', str(res.data))
    
    def test_show_user(self):
        with self.client as c:
          res = c.get(f'/users/{self.test.id}')

          self.assertEqual(res.status_code, 200)
          self.assertIn('@test', str(res.data))
          self.assertNotIn('@u2', str(res.data))
    
    def setup_likes(self):
        m1 = Message(text='warble 1', user_id=self.test.id)
        m2 = Message(text='warble 2', user_id=self.test.id)
        m3 = Message(id=9876, text="like this warble", user_id=self.u2.id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.test.id, message_id=9876)

        db.session.add(l1)
        db.session.commit()

    def test_show_stats(self):
        self.setup_likes()

        with self.client as c:
          res = c.get(f'/users/{self.test.id}')

          self.assertIn('@test', str(res.data))
          soup = BeautifulSoup(str(res.data), 'html.parser')
          found = soup.find_all('li', {'class':'stat'})
          
          self.assertEqual(len(found), 4)
          #messages
          self.assertIn('2',found[0].text)
          #following
          self.assertIn('0',found[1].text)
          #followers
          self.assertIn('0',found[2].text)
          #likes
          self.assertIn('1',found[3].text)
      
    def test_add_like(self):
        m = Message(id=2000, text='s club 7', user_id=self.u2.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
          with c.session_transaction() as sess:
              sess[CURR_USER_KEY] = self.test.id
          
          res = c.post('/users/add_like/2000', follow_redirects=True)
          self.assertEqual(res.status_code, 200)

          likes = Likes.query.filter(Likes.message_id==2000).all()
          self.assertEqual(len(likes), 1)
          self.assertEqual(likes[0].user_id, self.test.id)
      
    def test_remove_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=='like this warble').one()
        self.assertNotEqual(m.user_id, self.test.id)

        l = Likes.query.filter(Likes.user_id==self.test.id and Message.id==m.id).one()
        self.assertIsNotNone(l)
        
        with self.client as c:
          with c.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.test.id
          res = c.post(f'/users/add_like/{m.id}', follow_redirects=True)
          
          self.assertEqual(res.status_code, 200)
          self.assertEqual(len(self.test.likes),0)

          l = Likes.query.filter(Message.id==m.id).all()
          self.assertEqual(len(l),0)
          
    def test_unauthenticated_like(self):
      self.setup_likes()

      m = Message.query.filter(Message.text == 'like this warble').one()

      with self.client as c:
        res = c.post(f'/users/add_like/{m.id}', follow_redirects=True) 
        self.assertIn('Access unauthorized', str(res.data))

    def setup_followers(self):
      f1 = Follows(user_being_followed_id=self.u2.id, user_following_id=self.test.id)
      f2 = Follows(user_being_followed_id=self.u3.id, user_following_id=self.test.id)
      f3 = Follows(user_being_followed_id=self.test.id, user_following_id=self.u2.id)

      db.session.add_all([f1,f2,f3])
      db.session.commit()
    
    