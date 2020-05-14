"""Test account views"""
from django.contrib.auth import SESSION_KEY
#from django.urls import reverse
from test_plus import TestCase

from improved_user.factories import UserFactory


class AccountViewTests(TestCase):
    """Ensure login and logout workon via the browser"""

    user_factory = UserFactory

    @classmethod
    def setUpTestData(cls):
        """Create a user for test usage"""
        cls.password = "securepassword!"
        cls.user = cls.make_user(password=cls.password)

    def test_login_get(self):
        """Can Users GET a login form?"""
        response = self.get_check_200("auth:login")
        self.assertInContext("form")
        templates = [
            "base.html",
            "registration/base.html",
            "registration/login.html",
        ]
        for t_name in templates:
            with self.subTest(template=t_name):
                self.assertTemplateUsed(response, t_name)

    def test_login_post(self):
        """Can users login?"""
        response = self.post("auth:login", data={
            "username": self.user.email,
            "password": self.password,},)
        self.assertIn(SESSION_KEY, self.client.session)
        self.assertRedirects(response, "/")

    def test_logout_get(self):
        """Can Users logout via GET request?"""
        with self.login(self.user, password=self.password):
            response = self.get_check_200("auth:login")
            self.assertNotIn(SESSION_KEY, self.client.session)
            templates = [
                    "base.html",
                    "registration/base.html",
                    "registration/login.html",
            ]
            for t_name in templates:
                with self.subTest(template=t_name):
                    self.assertTemplateUsed(response, t_name)
            
