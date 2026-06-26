from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Category, Product, Review, HappyCustomer, HeroSlide
from django.db.models import Q

def home(request):
    categories = Category.objects.all()[:6]
    featured_products = Product.objects.filter(featured=True)[:4]
    best_sellers = Product.objects.filter(best_seller=True)[:4]
    new_arrivals = Product.objects.all().order_by('-created_at')[:4]
    happy_customers = HappyCustomer.objects.all().order_by('-created_at')[:6]
    
    hero_slides = HeroSlide.objects.all()
    if not hero_slides.exists():
        fallback_slides = []
        # Slide 1: Custom Logo slide
        fallback_slides.append({
            'subtitle': 'Where Tradition Blends with Trend',
            'title': 'Experience the Elegance of Chelu',
            'image': '/static/images/logo.jpg',
            'button_text': 'SHOP NOW',
            'button_url': '/shop/'
        })
        
        # Slide 2: Blue saree model
        fallback_slides.append({
            'subtitle': 'Exclusive Collection',
            'title': 'Vibrant Blue Stripes Handloom',
            'image': '/static/images/model_blue.jpg',
            'button_text': 'SHOP NOW',
            'button_url': '/shop/'
        })

        # Slide 3: Orange saree model
        fallback_slides.append({
            'subtitle': 'Bestsellers',
            'title': 'Traditional Orange & Green Edit',
            'image': '/static/images/model_orange.jpg',
            'button_text': 'SHOP NOW',
            'button_url': '/shop/'
        })

        # Slide 4: Green saree model
        fallback_slides.append({
            'subtitle': 'Festive Showcase',
            'title': 'Classic Green Cotton Drapes',
            'image': '/static/images/model_green.jpg',
            'button_text': 'SHOP NOW',
            'button_url': '/shop/'
        })
        
        p_zari = Product.objects.filter(name__icontains="kuthampully").first()
        if p_zari:
            fallback_slides.append({
                'subtitle': 'Kerala Weaves',
                'title': 'Traditional Kuthampully Double Zari',
                'image': p_zari.image,
                'button_text': 'SHOP NOW',
                'button_url': f'/product/{p_zari.id}/'
            })

        p_kasavu = Product.objects.filter(name__icontains="balaramapuram").first()
        if p_kasavu:
            fallback_slides.append({
                'subtitle': 'Festive Edit',
                'title': 'Balaramapuram Premium Kasavu Saree',
                'image': p_kasavu.image,
                'button_text': 'SHOP NOW',
                'button_url': f'/product/{p_kasavu.id}/'
            })
            
        if not fallback_slides:
            fallback_slides = [{
                'subtitle': 'Boutique Collection',
                'title': 'Handcrafted Elegance by Chelu',
                'image': None,
                'button_text': 'SHOP NOW',
                'button_url': '/shop/'
            }]
        hero_slides = fallback_slides
        
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'best_sellers': best_sellers,
        'new_arrivals': new_arrivals,
        'happy_customers': happy_customers,
        'hero_slides': hero_slides,
    }
    return render(request, 'home.html', context)


def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    
    # Category filter
    category_query = request.GET.get('category')
    if category_query:
        category_obj = get_object_or_404(Category, name__iexact=category_query)
        products = products.filter(category=category_obj)
        
    # Price filters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
        
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_query,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'products/category_products.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all().order_by('-created_at')
    # Fetch related products from same category, excluding current product
    related_products = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:4]
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)

def product_search(request):
    query = request.GET.get('query', '')
    categories = Category.objects.all()
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
        
    context = {
        'query': query,
        'products': products,
        'categories': categories,
    }
    return render(request, 'products/category_products.html', context)

@login_required
def submit_review(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=int(rating),
                comment=comment
            )
            messages.success(request, "Thank you! Your review has been submitted.")
        else:
            messages.error(request, "Please fill in all review fields.")
            
    return redirect('products:product_detail', pk=pk)

def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Simulate subscription
            messages.success(request, f"Welcome to the Chelu Club! Subscribed successfully with {email}.")
        else:
            messages.error(request, "Please enter a valid email address.")
    return redirect('products:home')

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Simulate contact form submission
        messages.success(request, f"Thank you {name}, we have received your message and will get back to you shortly!")
        return redirect('products:contact')
    return render(request, 'contact.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_conditions(request):
    return render(request, 'terms_conditions.html')

