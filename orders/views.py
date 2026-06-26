from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from cart.cart import Cart
from products.models import Product, Category, HappyCustomer, Coupon, BoutiqueSettings
from .models import Order, OrderItem
from decimal import Decimal
import razorpay
import collections


@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, "Your shopping bag is empty. Add products before checking out.")
        return redirect('products:product_list')
        
    profile = request.user.profile
    discount_percent = request.session.get('discount_percent', 0)
    coupon_code = request.session.get('coupon_code')
    
    subtotal = cart.get_total_price()
    discount = (subtotal * Decimal(discount_percent / 100)) if discount_percent > 0 else Decimal('0.00')
    total = subtotal - discount
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        payment_method = request.POST.get('payment_method', 'COD')
        
        # Simple validation
        if not all([name, email, phone, address, city, state, pincode]):
            messages.error(request, "Please fill in all shipping details.")
            return render(request, 'orders/checkout.html', {'cart': cart, 'profile': profile, 'total_price': total})
            
        # Create order
        order = Order.objects.create(
            user=request.user,
            name=name,
            email=email,
            phone_number=phone,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            total_price=total,
            coupon_code=coupon_code,
            discount=discount,
            payment_method=payment_method,
            payment_status=False,
            status='Processing'
        )
        
        # Save order items and decrement stock
        for item in cart:
            product = item['product']
            OrderItem.objects.create(
                order=order,
                product=product,
                price=item['price'],
                quantity=item['quantity']
            )
            # Update product stock
            product.stock = max(0, product.stock - item['quantity'])
            product.save()
            
        # Update user profile address details if they are currently blank
        if not profile.phone_number:
            profile.phone_number = phone
        if not profile.address:
            profile.address = address
        if not profile.city:
            profile.city = city
        if not profile.state:
            profile.state = state
        if not profile.pincode:
            profile.pincode = pincode
        profile.save()
        
        if payment_method == 'COD':
            # Clear cart and coupon sessions
            cart.clear()
            if 'coupon_code' in request.session:
                del request.session['coupon_code']
            if 'discount_percent' in request.session:
                del request.session['discount_percent']
                
            messages.success(request, f"Order #{order.id} placed successfully! Thank you for shopping with us.")
            return redirect('orders:order_detail', pk=order.id)
        else:
            return redirect('orders:payment_page', pk=order.id)
        
    context = {
        'cart': cart,
        'profile': profile,
        'coupon_code': coupon_code,
        'discount_percent': discount_percent,
        'discount_amount': discount,
        'subtotal': subtotal,
        'total_price': total,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def payment_page(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    # If already paid, redirect to detail
    if order.payment_status:
        return redirect('orders:order_detail', pk=order.id)
        
    razorpay_order_id = None
    is_real_razorpay = False
    amount_paise = int(order.total_price * 100)
    
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_placeholder')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_test_secret_placeholder')
    
    if key_id != 'rzp_test_placeholder' and key_secret != 'rzp_test_secret_placeholder':
        try:
            client = razorpay.Client(auth=(key_id, key_secret))
            data = {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"receipt_order_{order.id}",
                "payment_capture": 1
            }
            razorpay_order = client.order.create(data=data)
            razorpay_order_id = razorpay_order['id']
            is_real_razorpay = True
        except Exception as e:
            is_real_razorpay = False
            
    boutique_settings = BoutiqueSettings.objects.first()
    if not boutique_settings:
        boutique_settings = BoutiqueSettings.objects.create()

    context = {
        'order': order,
        'razorpay_key_id': key_id,
        'razorpay_order_id': razorpay_order_id,
        'is_real_razorpay': is_real_razorpay,
        'amount_paise': amount_paise,
        'boutique_settings': boutique_settings,
    }
    return render(request, 'orders/payment.html', context)


@csrf_exempt
@login_required
def payment_verify(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        is_payment_valid = False
        
        if razorpay_payment_id and razorpay_order_id and razorpay_signature:
            key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_placeholder')
            key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_test_secret_placeholder')
            client = razorpay.Client(auth=(key_id, key_secret))
            try:
                params_dict = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }
                client.utility.verify_payment_signature(params_dict)
                is_payment_valid = True
            except Exception as e:
                is_payment_valid = False
        else:
            status = request.POST.get('status')
            if status == 'success':
                is_payment_valid = True
                
        if is_payment_valid:
            order.payment_status = True
            order.save()
            
            # Clear the cart & coupon sessions since checkout payment succeeded!
            cart = Cart(request)
            cart.clear()
            if 'coupon_code' in request.session:
                del request.session['coupon_code']
            if 'discount_percent' in request.session:
                del request.session['discount_percent']
                
            messages.success(request, f"Payment for Order #{order.id} completed successfully!")
            return redirect('orders:order_detail', pk=order.id)
        else:
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('orders:payment_page', pk=order.id)
            
    return redirect('orders:payment_page', pk=order.id)

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@staff_member_required
def admin_dashboard(request):
    orders = Order.objects.all().order_by('-created_at')
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    happy_customers = HappyCustomer.objects.all().order_by('-created_at')
    
    total_sales = sum(o.total_price for o in orders)
    total_orders = orders.count()
    pending_orders = orders.filter(status__in=['Processing', 'Packed']).count()
    
    # Analytics data: monthly sales (ordered chronologically)
    orders_chrono = Order.objects.all().order_by('created_at')
    monthly_dict = collections.OrderedDict()
    for o in orders_chrono:
        month_str = o.created_at.strftime('%B %Y')
        monthly_dict[month_str] = monthly_dict.get(month_str, 0.0) + float(o.total_price)
        
    if not monthly_dict:
        from django.utils import timezone
        current_month = timezone.now().strftime('%B %Y')
        monthly_dict[current_month] = 0.0
        
    chart_labels = list(monthly_dict.keys())
    chart_data = list(monthly_dict.values())
    
    # CRM customers
    customers_list = []
    users = User.objects.all()
    for u in users:
        user_orders = u.orders.all()
        order_count = user_orders.count()
        ltv = sum(o.total_price for o in user_orders)
        customers_list.append({
            'username': u.username,
            'email': u.email or 'N/A',
            'is_staff': u.is_staff,
            'date_joined': u.date_joined,
            'order_count': order_count,
            'ltv': ltv,
        })
    customers_list.sort(key=lambda x: x['ltv'], reverse=True)
    
    # Coupons list
    coupons = Coupon.objects.all().order_by('-valid_until')
    
    # Boutique global settings
    boutique_settings = BoutiqueSettings.objects.first()
    if not boutique_settings:
        boutique_settings = BoutiqueSettings.objects.create()
        
    context = {
        'orders': orders,
        'products': products,
        'categories': categories,
        'happy_customers': happy_customers,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'customers': customers_list,
        'coupons': coupons,
        'boutique_settings': boutique_settings,
    }
    return render(request, 'orders/dashboard.html', context)

@staff_member_required
def admin_order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        payment_status = request.POST.get('payment_status') == 'True'
        tracking_number = request.POST.get('tracking_number', '').strip()
        courier_partner = request.POST.get('courier_partner', '').strip()
        
        order.status = status
        order.payment_status = payment_status
        order.tracking_number = tracking_number if tracking_number else None
        order.courier_partner = courier_partner if courier_partner else None
        order.save()
        
        messages.success(request, f"Order #{order.id} updated successfully.")
    return redirect('orders:admin_dashboard')

@staff_member_required
def admin_product_add(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        image = request.FILES.get('image')
        featured = request.POST.get('featured') == 'on'
        best_seller = request.POST.get('best_seller') == 'on'
        
        if all([category_id, name, description, price, stock, image]):
            category = get_object_or_404(Category, id=category_id)
            Product.objects.create(
                category=category,
                name=name,
                description=description,
                price=Decimal(price),
                stock=int(stock),
                image=image,
                featured=featured,
                best_seller=best_seller
            )
            messages.success(request, f"Product '{name}' added successfully.")
        else:
            messages.error(request, "Failed to add product. Please fill in all fields and upload an image.")
            
    return redirect('orders:admin_dashboard')

@staff_member_required
def admin_customer_photo_upload(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        quote = request.POST.get('quote')
        image = request.FILES.get('image')
        
        if name and image:
            HappyCustomer.objects.create(
                name=name,
                location=location,
                quote=quote,
                image=image
            )
            messages.success(request, f"Uploaded testimonial photo for '{name}'.")
        else:
            messages.error(request, "Failed to upload photo. Name and Image are required.")
            
    return redirect('orders:admin_dashboard')

@staff_member_required
def admin_coupon_add(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount_percent = request.POST.get('discount_percent')
        valid_until = request.POST.get('valid_until')
        active = request.POST.get('active') == 'on' or 'active' in request.POST
        
        if code and discount_percent and valid_until:
            try:
                from django.utils.dateparse import parse_datetime
                from django.utils import timezone
                naive_dt = parse_datetime(valid_until)
                if naive_dt:
                    aware_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
                else:
                    aware_dt = timezone.now()
                
                Coupon.objects.create(
                    code=code,
                    discount_percent=int(discount_percent),
                    active=active,
                    valid_until=aware_dt
                )
                messages.success(request, f"Promo code '{code}' created successfully.")
            except Exception as e:
                messages.error(request, f"Error creating coupon: {str(e)}")
        else:
            messages.error(request, "Failed to create coupon. All fields are required.")
    return redirect('orders:admin_dashboard')

@staff_member_required
def admin_settings_update(request):
    if request.method == 'POST':
        store_name = request.POST.get('store_name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        shipping_rate = request.POST.get('shipping_rate', '0.00').strip()
        hours = request.POST.get('hours', '').strip()
        upi_qr_code = request.FILES.get('upi_qr_code')
        
        if store_name and address and phone and email:
            settings_obj = BoutiqueSettings.objects.first()
            if not settings_obj:
                settings_obj = BoutiqueSettings()
            
            settings_obj.store_name = store_name
            settings_obj.address = address
            settings_obj.phone = phone
            settings_obj.email = email
            settings_obj.shipping_rate = Decimal(shipping_rate)
            settings_obj.hours = hours
            
            if upi_qr_code:
                settings_obj.upi_qr_code = upi_qr_code
                
            settings_obj.save()
            
            messages.success(request, "Boutique global settings updated successfully.")
        else:
            messages.error(request, "Failed to update settings. Please check all fields.")
    return redirect('orders:admin_dashboard')



