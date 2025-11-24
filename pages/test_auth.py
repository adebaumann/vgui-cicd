from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError


class AuthenticationTest(TestCase):
    """Test login, logout, and password change functionality"""
    
    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpass123',
            email='staff@example.com'
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
    
    def test_login_page_loads(self):
        """Test that login page loads correctly"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anmelden')
        self.assertContains(response, 'Benutzername:')
        self.assertContains(response, 'Passwort:')
    
    def test_login_valid_credentials(self):
        """Test successful login with valid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertRedirects(response, '/')  # Should redirect to main page
        
        # Check user is logged in
        response = self.client.get('/')
        self.assertContains(response, 'testuser')  # Username should appear in header
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials shows error"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertContains(response, 'Ihr Benutzername und Passwort stimmen nicht überein')
    
    def test_login_empty_credentials(self):
        """Test login with empty credentials"""
        response = self.client.post(reverse('login'), {
            'username': '',
            'password': ''
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        # Django's form validation should handle this
    
    def test_logout_functionality(self):
        """Test logout functionality"""
        # First login
        self.client.login(username='testuser', password='testpass123')
        
        # Verify user is logged in
        response = self.client.get('/')
        self.assertContains(response, 'testuser')
        
        # Logout using POST
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        self.assertRedirects(response, '/')  # Should redirect to main page
        
        # Verify user is logged out
        response = self.client.get('/')
        self.assertNotContains(response, 'testuser')
        self.assertContains(response, 'Anmelden')  # Should show login link
    
    def test_logout_requires_post(self):
        """Test that logout requires POST method"""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Try GET logout (should fail with 405)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # User should still be logged in
        response = self.client.get('/')
        self.assertContains(response, 'testuser')
    
    def test_password_change_page_loads(self):
        """Test that password change page loads for authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwort ändern')
        self.assertContains(response, 'Aktuelles Passwort:')
        self.assertContains(response, 'Neues Passwort:')
        self.assertContains(response, 'Neues Passwort bestätigen:')
    
    def test_password_change_requires_authentication(self):
        """Test that password change page requires authentication"""
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Should redirect to login page
        self.assertIn(reverse('login'), response.url)
    
    def test_password_change_valid(self):
        """Test successful password change"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('password_change'), {
            'old_password': 'testpass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertRedirects(response, '/')  # Should redirect to main page
        
        # Verify new password works
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'newpass456'
        })
        self.assertEqual(response.status_code, 302)  # Successful login
    
    def test_password_change_wrong_old_password(self):
        """Test password change with wrong old password"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('password_change'), {
            'old_password': 'wrongpassword',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        })
        self.assertEqual(response.status_code, 200)  # Stay on form page
        self.assertContains(response, 'Bitte korrigieren Sie die Fehler unten')
    
    def test_password_change_mismatched_new_passwords(self):
        """Test password change with mismatched new passwords"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('password_change'), {
            'old_password': 'testpass123',
            'new_password1': 'newpass456',
            'new_password2': 'differentpass789'
        })
        self.assertEqual(response.status_code, 200)  # Stay on form page
        self.assertContains(response, 'Bitte korrigieren Sie die Fehler unten')
    
    def test_password_change_same_as_old_password(self):
        """Test password change with same password as old"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('password_change'), {
            'old_password': 'testpass123',
            'new_password1': 'testpass123',
            'new_password2': 'testpass123'
        })
        # Django's default validators don't prevent same password, so it should succeed
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertRedirects(response, '/')  # Should redirect to main page
    
    def test_password_change_cancel_button(self):
        """Test password change cancel button"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Abbrechen')
        # The cancel button should link to main page
        self.assertContains(response, 'href="/"')
    
    def test_user_menu_display_for_authenticated_user(self):
        """Test that user menu displays correctly for authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')  # Username in menu
        self.assertContains(response, 'Passwort ändern')  # Password change link
        self.assertContains(response, 'Abmelden')  # Logout link
        self.assertNotContains(response, 'Anmelden')  # Should not show login link
    
    def test_login_link_display_for_anonymous_user(self):
        """Test that login link displays for anonymous users"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anmelden')  # Should show login link
        self.assertNotContains(response, 'testuser')  # Should not show username
        self.assertNotContains(response, 'Passwort ändern')  # Should not show password change
        self.assertNotContains(response, 'Abmelden')  # Should not show logout
    
    def test_staff_user_menu(self):
        """Test that staff users see appropriate menu"""
        self.client.login(username='staffuser', password='staffpass123')
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'staffuser')  # Username in menu
        self.assertContains(response, 'Passwort ändern')  # Password change link
        self.assertContains(response, 'Abmelden')  # Logout link
    
    def test_login_redirect_to_main_page(self):
        """Test that successful login redirects to main page"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        # Should end up on main page
        self.assertContains(response, 'Vorgaben Informatiksicherheit')
    
    def test_logout_redirect_to_main_page(self):
        """Test that logout redirects to main page"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        # Should end up on main page
        self.assertContains(response, 'Vorgaben Informatiksicherheit')
        # Should show login link for anonymous users
        self.assertContains(response, 'Anmelden')
    
    def test_password_change_redirect_to_main_page(self):
        """Test that successful password change redirects to main page"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('password_change'), {
            'old_password': 'testpass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        # Should end up on main page
        self.assertContains(response, 'Vorgaben Informatiksicherheit')
    
    def test_csrf_token_present_in_forms(self):
        """Test that CSRF tokens are present in authentication forms"""
        # Login form
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        # Password change form
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('password_change'))
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_login_with_next_parameter(self):
        """Test login with next parameter for redirect"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
            'next': '/dokumente/'
        })
        self.assertEqual(response.status_code, 302)
        # Should redirect to the specified next page
        self.assertRedirects(response, '/dokumente/')