import time
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class AdminSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Protect all custom admin dashboard routes starting with /orders/dashboard/
        if request.path.startswith('/orders/dashboard/'):
            if not request.user.is_authenticated:
                messages.warning(request, "Access Denied. Please log in as an administrator.")
                return redirect(f"{reverse('accounts:login')}?next={request.path}")
            elif not (request.user.is_staff or request.user.is_superuser):
                messages.error(request, "Access Denied. Administrator privileges required.")
                return redirect('products:home')

        # 2. Automatically log out inactive admins after 30 minutes (1800 seconds)
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            last_activity = request.session.get('admin_last_activity')
            now = time.time()
            if last_activity:
                inactive_duration = now - last_activity
                if inactive_duration > 1800:  # 30 minutes
                    logout(request)
                    messages.warning(request, "Your administrator session has expired due to inactivity. Please log in again.")
                    return redirect('accounts:login')
            # Update the last activity timestamp
            request.session['admin_last_activity'] = now

        response = self.get_response(request)
        return response
