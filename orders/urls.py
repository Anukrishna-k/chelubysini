from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('history/', views.order_history, name='order_history'),
    path('detail/<int:pk>/', views.order_detail, name='order_detail'),
    path('confirmation/<int:pk>/', views.order_confirmation, name='order_confirmation'),
    path('payment/<int:pk>/', views.payment_page, name='payment_page'),
    path('payment/verify/<int:pk>/', views.payment_verify, name='payment_verify'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/order/update/<int:pk>/', views.admin_order_update, name='admin_order_update'),
    path('dashboard/product/add/', views.admin_product_add, name='admin_product_add'),
    path('dashboard/product/edit/<int:pk>/', views.admin_product_edit, name='admin_product_edit'),
    path('dashboard/product/delete/<int:pk>/', views.admin_product_delete, name='admin_product_delete'),
    path('dashboard/happy-customer/add/', views.admin_customer_photo_upload, name='admin_customer_photo_upload'),
    path('dashboard/happy-customer/edit/<int:pk>/', views.admin_customer_photo_edit, name='admin_customer_photo_edit'),
    path('dashboard/happy-customer/delete/<int:pk>/', views.admin_customer_photo_delete, name='admin_customer_photo_delete'),
    path('dashboard/heroslide/add/', views.admin_heroslide_add, name='admin_heroslide_add'),
    path('dashboard/heroslide/edit/<int:pk>/', views.admin_heroslide_edit, name='admin_heroslide_edit'),
    path('dashboard/heroslide/delete/<int:pk>/', views.admin_heroslide_delete, name='admin_heroslide_delete'),
    path('dashboard/coupon/add/', views.admin_coupon_add, name='admin_coupon_add'),
    path('dashboard/settings/update/', views.admin_settings_update, name='admin_settings_update'),
]

