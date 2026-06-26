from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import Product, Coupon
from .cart import Cart
from django.utils import timezone
from decimal import Decimal

def cart_detail(request):
    cart = Cart(request)
    coupon_code = request.session.get('coupon_code')
    discount_percent = request.session.get('discount_percent', 0)
    
    subtotal = cart.get_total_price()
    discount = (subtotal * Decimal(discount_percent / 100)) if discount_percent > 0 else Decimal('0.00')
    total = subtotal - discount
    
    context = {
        'cart': cart,
        'coupon_code': coupon_code,
        'discount_percent': discount_percent,
        'discount_amount': discount,
        'total_price': total,
        'subtotal': subtotal,
    }
    return render(request, 'cart/cart.html', context)

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override', 'False') == 'True'
    
    if product.stock < quantity and not override:
        messages.error(request, f"Sorry, only {product.stock} items of {product.name} are available.")
        return redirect('products:product_detail', pk=product_id)
        
    cart.add(product=product, quantity=quantity, override_quantity=override)
    messages.success(request, f"Added {product.name} to your shopping bag.")
    return redirect('cart:cart_detail')

@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if product.stock < quantity:
        messages.error(request, f"Sorry, only {product.stock} items of {product.name} are available.")
    else:
        cart.add(product=product, quantity=quantity, override_quantity=True)
        messages.success(request, f"Updated quantity for {product.name}.")
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f"Removed {product.name} from your shopping bag.")
    return redirect('cart:cart_detail')

@require_POST
def apply_coupon(request):
    code = request.POST.get('coupon_code', '').strip()
    now = timezone.now()
    
    try:
        coupon = Coupon.objects.get(code__iexact=code, active=True, valid_until__gte=now)
        request.session['coupon_code'] = coupon.code
        request.session['discount_percent'] = coupon.discount_percent
        messages.success(request, f"Coupon '{coupon.code}' applied! You got {coupon.discount_percent}% off.")
    except Coupon.DoesNotExist:
        # Clear coupon if invalid is entered
        if 'coupon_code' in request.session:
            del request.session['coupon_code']
        if 'discount_percent' in request.session:
            del request.session['discount_percent']
        messages.error(request, "Invalid or expired coupon code.")
        
    return redirect('cart:cart_detail')

@require_POST
def remove_coupon(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
    if 'discount_percent' in request.session:
        del request.session['discount_percent']
    messages.success(request, "Coupon removed.")
    return redirect('cart:cart_detail')
