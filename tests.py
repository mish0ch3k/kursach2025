import unittest

from app import create_app, db 
from app.models import User, Project
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class SystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()



    def register(self, username, email, password):
        return self.client.post('/register', data=dict(
            username=username, email=email, password=password
        ), follow_redirects=True)

    def login(self, email, password):
        return self.client.post('/login', data=dict(
            email=email, password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)


    def test_auth_flow(self):
        response = self.register('testuser', 'test@test.com', 'password')
        self.assertIn(b'alert-success', response.data) 
        
        response = self.login('test@test.com', 'password')
        self.assertIn(b'\xd0\x9c\xd0\xbe\xd1\x97 \xd0\xbf\xd1\x80\xd0\xbe\xd0\xb5\xd0\xba\xd1\x82\xd0\xb8', response.data)

        response = self.logout()
        self.assertIn(b'\xd0\x92\xd1\x85\xd1\x96\xd0\xb4', response.data)

    def test_profile_settings(self):
        self.register('u', 'u@u.com', 'p')
        self.login('u@u.com', 'p')
        
        response = self.client.post('/profile', data={'telegram_chat_id': '123456'}, follow_redirects=True)
        self.assertIn(b'Telegram ID', response.data)
        
        user = User.query.filter_by(email='u@u.com').first()
        self.assertEqual(user.telegram_chat_id, '123456')


    def test_project_collaboration(self):
        self.register('admin_user', 'admin@test.com', '123')
        self.login('admin@test.com', '123')
        
        self.client.post('/project/new', data={
            'name': 'Collab Project',
            'url': 'https://github.com/test/repo.git'
        }, follow_redirects=True)
        
        project = Project.query.filter_by(name='Collab Project').first()
        invite_code = project.invite_code
        self.assertIsNotNone(invite_code)
        self.logout()

        self.register('member_user', 'member@test.com', '123')
        self.login('member@test.com', '123')
        
        response = self.client.post('/project/join', data={'invite_code': invite_code}, follow_redirects=True)
        self.assertIn(b'Collab Project', response.data)
        
        project_db = Project.query.filter_by(name='Collab Project').first()
        members = [u.username for u in project_db.members]
        self.assertIn('member_user', members)
        self.assertIn('admin_user', members)

    def test_delete_project_permissions(self):
        self.register('owner', 'owner@test.com', '123')
        self.login('owner@test.com', '123')
        self.client.post('/project/new', data={'name': 'DelProj', 'url': 'git.git'})
        
        pid = Project.query.first().id
        invite_code = Project.query.first().invite_code
        self.logout()

        self.register('hacker', 'hacker@test.com', '123')
        self.login('hacker@test.com', '123')
        self.client.post('/project/join', data={'invite_code': invite_code})

        self.client.post(f'/project/{pid}/delete', follow_redirects=True)
        
        proj = db.session.get(Project, pid)
        self.assertIsNotNone(proj)
        self.assertNotIn('hacker', [u.username for u in proj.members])


    def test_admin_access(self):
        self.register('regular', 'reg@test.com', '123')
        self.login('reg@test.com', '123')
        

        response = self.client.get('/admin/users/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)


        user = User.query.filter_by(email='reg@test.com').first()
        user.is_admin = True
        db.session.commit()

        response = self.client.get('/admin/users/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_achievements_logic(self):
        self.register('achiever', 'a@test.com', '123')
        user = User.query.filter_by(email='a@test.com').first()
        
        is_new = user.add_achievement("Test Badge")
        db.session.commit()
        
        self.assertTrue(is_new)
        self.assertIn("Test Badge", user.get_achievements())
        
        is_new_again = user.add_achievement("Test Badge")
        self.assertFalse(is_new_again)

if __name__ == '__main__':
    unittest.main()