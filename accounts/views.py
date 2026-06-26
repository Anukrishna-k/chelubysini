from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from orders.models import Order
from wishlist.models import Wishlist

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'accounts/signup.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'accounts/signup.html')
            
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Log in the user
        login(request, user)
        messages.success(request, f"Welcome to Chelu by Sini, {user.username}!")
        return redirect('products:home')
        
    return render(request, 'accounts/signup.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')
        
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Support email login as well
        user = None
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(request, username=username_or_email, password=password)
            
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            # Redirect to 'next' if exists
            next_url = request.GET.get('next', 'products:home')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username/email or password.")
            
    return render(request, 'accounts/login.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, "Logged out successfully. See you soon!")
    return redirect('products:home')

@login_required
def profile_view(request):
    profile = request.user.profile
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    wishlist_items = Wishlist.objects.filter(user=request.user)[:4]
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        
        # Update user fields
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()
        
        # Update profile fields
        profile.phone_number = phone
        profile.address = address
        profile.city = city
        profile.state = state
        profile.pincode = pincode
        profile.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('accounts:profile')
        
    context = {
        'profile': profile,
        'orders': orders,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'accounts/profile.html', context)
