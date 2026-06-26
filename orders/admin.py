from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'email', 'total_price', 'payment_method', 'payment_status', 'status', 'created_at')
    list_filter = ('payment_status', 'status', 'created_at', 'payment_method')
    list_editable = ('payment_status', 'status')
    search_fields = ('name', 'email', 'phone_number', 'address')
    inlines = [OrderItemInline]

