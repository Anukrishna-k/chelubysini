import time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

class AdminAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create normal customer
        self.customer = User.objects.create_user(
            username='customer_user',
            email='customer@example.com',
            password='Password123'
        )
        
        # Create admin staff user
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='Password123',
            is_staff=True
        )

    def test_unauthenticated_dashboard_redirect(self):
        """Unauthenticated requests to the dashboard should redirect to the login page."""
        response = self.client.get(reverse('orders:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)
        self.assertIn('next=/orders/dashboard/', response.url)

    def test_customer_dashboard_access_denied(self):
        """Authenticated customer users should be blocked from accessing the admin dashboard."""
        self.client.login(username='customer_user', password='Password123')
        response = self.client.get(reverse('orders:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('products:home'))
        
        # Check messages
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Access Denied. Administrator privileges required." in str(m) for m in messages))

    def test_admin_dashboard_access_allowed(self):
        """Staff/superuser accounts should successfully access the admin dashboard."""
        # Need to log in and set last activity
        self.client.login(username='admin_user', password='Password123')
        session = self.client.session
        session['admin_last_activity'] = time.time()
        session.save()
        
        response = self.client.get(reverse('orders:admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_login_success(self):
        """Logging in with valid admin credentials via admin form should succeed and redirect."""
        response = self.client.post(reverse('accounts:admin_login'), {
            'username': 'admin_user',
            'password': 'Password123',
            'remember_me': 'on'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('orders:admin_dashboard'))

    def test_admin_login_failed_for_customer(self):
        """Standard customer credentials on the admin login form should show Access Denied."""
        response = self.client.post(reverse('accounts:admin_login'), {
            'username': 'customer_user',
            'password': 'Password123'
        })
        self.assertEqual(response.status_code, 200) # Re-renders login.html
        self.assertContains(response, "Access Denied. Administrator privileges required.")

    def test_admin_login_failed_invalid_credentials(self):
        """Invalid credentials should show a validation error."""
        response = self.client.post(reverse('accounts:admin_login'), {
            'username': 'admin_user',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username/email or password.")

    def test_admin_session_inactivity_logout(self):
        """Admin sessions should automatically log out after 30 minutes of inactivity."""
        self.client.login(username='admin_user', password='Password123')
        
        # Simulating inactivity: set last activity to 31 minutes ago
        session = self.client.session
        session['admin_last_activity'] = time.time() - 1900
        session.save()
        
        response = self.client.get(reverse('orders:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:login'))
        
        # Verify user is logged out
        self.assertFalse(response.wsgi_request.user.is_authenticated)
