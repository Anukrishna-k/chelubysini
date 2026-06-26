from django.contrib import admin
from .models import Category, Product, Review, Coupon, HappyCustomer, HeroSlide, BoutiqueSettings

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'featured', 'best_seller', 'created_at')
    list_filter = ('category', 'featured', 'best_seller', 'created_at')
    list_editable = ('price', 'stock', 'featured', 'best_seller')
    search_fields = ('name', 'description')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'active', 'valid_until')
    list_filter = ('active', 'valid_until')
    search_fields = ('code',)

@admin.register(HappyCustomer)
class HappyCustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'created_at')
    search_fields = ('name', 'location', 'quote')

@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('id', 'subtitle', 'title', 'order', 'created_at')
    list_editable = ('order',)
    search_fields = ('title', 'subtitle', 'button_text')

@admin.register(BoutiqueSettings)
class BoutiqueSettingsAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'phone', 'email', 'shipping_rate', 'hours')




