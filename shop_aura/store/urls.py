from django.shortcuts import render
from django.urls import path
from . import admin_views
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Basic pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    
    # Product browsing
    path('category/<str:category>/', views.category_page, name='category_page'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/comment/', views.submit_comment, name='submit_comment'),
    path('comment/<int:comment_id>/update/', views.update_comment, name='update_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('search/', views.search_results, name='search_results'),
    
    # Cart management
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Checkout process
    path('shipping/', views.shipping, name='shipping'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<int:order_id>/', views.payment, name='payment'),
    
    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    
    # Admin URLs
    path('admin/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/products/', admin_views.admin_products, name='admin_products'),
    path('admin/products/add/', admin_views.admin_product_edit, name='admin_product_add'),
    path('admin/products/edit/<int:product_id>/', admin_views.admin_product_edit, name='admin_product_edit'),
    path('admin/products/delete/<int:product_id>/', admin_views.admin_product_delete, name='admin_product_delete'),
    path('admin/orders/', admin_views.admin_orders, name='admin_orders'),
    path('admin/orders/<int:order_id>/', admin_views.admin_order_detail, name='admin_order_detail'),
    path('admin/customers/', admin_views.admin_customers, name='admin_customers'),
    path('admin/inventory/', admin_views.admin_inventory, name='admin_inventory'),
    path('admin/marketing/', admin_views.admin_marketing, name='admin_marketing'),
    path('admin/reports/', admin_views.admin_sales_report, name='admin_sales_report'),
    path('admin/sellers/', admin_views.admin_sellers, name='admin_sellers'),
    path('admin/product-submissions/', admin_views.admin_product_submissions, name='admin_product_submissions'),
    path('admin/sales/', admin_views.admin_sales, name='admin_sales'),
    path('admin/sales/add/', admin_views.admin_sale_edit, name='admin_sale_add'),
    path('admin/sales/edit/<int:sale_id>/', admin_views.admin_sale_edit, name='admin_sale_edit'),
    path('admin/sales/delete/<int:sale_id>/', admin_views.admin_sale_delete, name='admin_sale_delete'),
    path('admin/complaints/', admin_views.admin_complaints, name='admin_complaints'),
    path('admin/complaints/<int:complaint_id>/', admin_views.admin_complaint_detail, name='admin_complaint_detail'),
    
    # Seller URLs
    path('seller/signup/', views.seller_signup, name='seller_signup'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/product/submit/', views.seller_product_submit, name='seller_product_submit'),
    path('seller/login/', views.seller_login, name='seller_login'),
    path('seller/verify-otp/', views.verify_seller_otp, name='verify_seller_otp'),
    path('test-email/', views.test_email, name='test_email'),
    path('order-tracking/<int:order_id>/', views.order_tracking, name='order_tracking'),
]