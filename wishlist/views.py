from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from products.models import Product
from cart.cart import Cart
from .models import Wishlist

@login_required
def wishlist_detail(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'wishlist/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Get or create wishlist item
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if created:
        messages.success(request, f"Saved {product.name} to your Wishlist.")
    else:
        messages.info(request, f"{product.name} is already in your Wishlist.")
        
    # Redirect back to where user came from, or wishlist
    next_url = request.META.get('HTTP_REFERER', 'wishlist:wishlist_detail')
    return redirect(next_url)

@login_required
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product)
    
    if wishlist_item.exists():
        wishlist_item.delete()
        messages.success(request, f"Removed {product.name} from your Wishlist.")
    else:
        messages.error(request, f"{product.name} is not in your Wishlist.")
        
    return redirect('wishlist:wishlist_detail')

@login_required
def wishlist_move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product)
    
    if wishlist_item.exists():
        # Remove from wishlist
        wishlist_item.delete()
        
        # Add to cart
        cart = Cart(request)
        cart.add(product=product, quantity=1)
        messages.success(request, f"Moved {product.name} to your shopping bag.")
    else:
        messages.error(request, f"{product.name} is not in your Wishlist.")
        
    return redirect('wishlist:wishlist_detail')
