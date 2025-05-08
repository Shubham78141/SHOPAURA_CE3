from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from decimal import Decimal
from random import choice
import logging
import random
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
import requests
from django.utils.crypto import get_random_string
from .forms import SignUpForm, ProfileUpdateForm, ComplaintForm, ShippingForm, LoginForm, SellerProductSubmissionForm, SellerSignUpForm
from .models import OrderTracking, Sale, User, Product, CartItem, Order, OrderItem, Seller, SellerProductSubmission, Complaint

logger = logging.getLogger(__name__)

def home(request):
    if request.user.is_authenticated and request.user.is_superuser:
        logout(request)
        messages.info(request, "Admin session ended. Please log in as a customer or seller.")
        return redirect('login')
    all_products = list(Product.objects.all())
    random.shuffle(all_products)
    products = all_products[:25]
    for product in products:
        if product.available_sizes:
            product.size_list = product.available_sizes.split(',')
        else:
            product.size_list = []
        if product.attributes:
            product.attribute_list = product.attributes.split(',')
        else:
            product.attribute_list = []
    sales = Sale.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('-created_at')
    context = {
        'products': products,
        'sales': sales,
    }
    return render(request, 'index.html', context)

def about(request):
    return render(request, 'aboutus.html')

def contact(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save()
            messages.success(request, 'Your complaint has been submitted successfully!')
            try:
                html_message = render_to_string('emails/complaint_confirmation.html', {
                    'name': complaint.name,
                    'message': complaint.message,
                    'website_url': request.build_absolute_uri(reverse('home'))
                })
                plain_message = strip_tags(html_message)
                send_mail(
                    subject='SHOPAURA - Complaint Received',
                    message=plain_message,
                    html_message=html_message,
                    from_email='shopAura002@gmail.com',
                    recipient_list=[complaint.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send complaint confirmation email to {complaint.email}: {str(e)}")
                messages.warning(request, 'Complaint submitted, but failed to send confirmation email.')
            return redirect('contact')
    else:
        form = ComplaintForm()
    return render(request, 'contact.html', {'form': form})

def category_page(request, category):
    products = Product.objects.filter(category=category)
    for product in products:
        if product.available_sizes:
            product.size_list = product.available_sizes.split(',')
        else:
            product.size_list = []
        if product.attributes:
            product.attribute_list = product.attributes.split(',')
        else:
            product.attribute_list = []
    print(f"Category: {category}, Products found: {len(products)}")
    category_description = get_category_description(category)
    context = {
        'category': category,
        'category_description': category_description,
        'products': products,
    }
    return render(request, 'category.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check Flask API availability
    try:
        response = requests.get(f'http://localhost:5000/api/product/{product_id}/comments', timeout=5)
        if response.status_code != 200:
            logger.warning(f"Flask API unavailable: returned status {response.status_code}, Response: {response.text}")
            return render(request, 'service_unavailable.html')
    except requests.RequestException as e:
        logger.error(f"Flask API unavailable: {str(e)}")
        return render(request, 'service_unavailable.html')

    # Use local Django Product model data
    product.api_name = product.name
    product.api_description = product.description
    product.api_image_url = product.image_url

    # Fetch comments from Flask API (already confirmed available)
    comments = []
    try:
        logger.info(f"Comments API request to http://localhost:5000/api/product/{product_id}/comments returned status {response.status_code}")
        if response.status_code == 200:
            comments = response.json()
            logger.info(f"Comments received: {len(comments)}")
        else:
            logger.warning(f"Comments API returned non-200 status: {response.status_code}, Response: {response.text}")
            messages.error(request, f'Failed to load comments: API returned status {response.status_code}')
    except requests.RequestException as e:
        logger.error(f"Failed to fetch comments from Flask API: {str(e)}")
        messages.error(request, 'Comments service is currently unavailable. Please try again later.')
        comments = []  # Fallback to empty list

    # Determine if comments are editable by the current user
    current_username = (request.user.first_name if request.user.is_authenticated and hasattr(request.user, 'first_name') and request.user.first_name else request.user.email) if request.user.is_authenticated else None
    for comment in comments:
        comment['is_editable'] = request.user.is_authenticated and comment['username'] == current_username

    # Fetch similar products
    similar_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:4]
    for similar_product in similar_products:
        if similar_product.available_sizes:
            similar_product.size_list = similar_product.available_sizes.split(',')
        else:
            similar_product.size_list = []
        if similar_product.attributes:
            similar_product.attribute_list = similar_product.attributes.split(',')
        else:
            similar_product.attribute_list = []

    if product.available_sizes:
        product.size_list = product.available_sizes.split(',')
    else:
        product.size_list = []
    if product.attributes:
        product.attribute_list = product.attributes.split(',')
    else:
        product.attribute_list = []
    return render(request, 'product_detail.html', {
        'product': product,
        'comments': comments,
        'similar_products': similar_products
    })

@login_required
def submit_comment(request, product_id):
    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        if not comment_text:
            messages.error(request, 'Comment cannot be empty.')
            return redirect('product_detail', product_id=product_id)
        try:
            # Use first_name if available and non-empty, fallback to email
            username = request.user.first_name if hasattr(request.user, 'first_name') and request.user.first_name else request.user.email
            response = requests.post(
                f'http://localhost:5000/api/product/{product_id}/comments',
                json={
                    'username': username,
                    'comment': comment_text
                },
                timeout=5
            )
            logger.info(f"Comment submission to http://localhost:5000/api/product/{product_id}/comments returned status {response.status_code}, Response: {response.text}")
            if response.status_code == 201:
                messages.success(request, 'Comment submitted successfully!')
            else:
                logger.warning(f"Comment submission failed: {response.status_code}, Response: {response.text}")
                messages.error(request, f'Failed to submit comment: API returned status {response.status_code}. Please try again.')
        except requests.RequestException as e:
            logger.error(f"Failed to submit comment to Flask API: {str(e)}")
            messages.error(request, 'Unable to submit comment due to a server error. Please try again later.')
        return redirect('product_detail', product_id=product_id)
    return redirect('product_detail', product_id=product_id)

@login_required
def update_comment(request, comment_id):
    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        if not comment_text:
            messages.error(request, 'Comment cannot be empty.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        try:
            username = request.user.first_name if hasattr(request.user, 'first_name') and request.user.first_name else request.user.email
            response = requests.put(
                f'http://localhost:5000/api/product/comments/{comment_id}',
                json={
                    'username': username,
                    'comment': comment_text
                },
                timeout=5
            )
            logger.info(f"Comment update to http://localhost:5000/api/product/comments/{comment_id} returned status {response.status_code}, Response: {response.text}")
            if response.status_code == 200:
                messages.success(request, 'Comment updated successfully!')
            elif response.status_code == 403:
                messages.error(request, 'You are not authorized to update this comment.')
            elif response.status_code == 404:
                messages.error(request, 'Comment not found.')
            else:
                logger.warning(f"Comment update failed: {response.status_code}, Response: {response.text}")
                messages.error(request, f'Failed to update comment: API returned status {response.status_code}. Please try again.')
        except requests.RequestException as e:
            logger.error(f"Failed to update comment to Flask API: {str(e)}")
            messages.error(request, 'Unable to update comment due to a server error. Please try again later.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    return redirect('home')

@login_required
def delete_comment(request, comment_id):
    if request.method == 'POST':
        try:
            username = request.user.first_name if hasattr(request.user, 'first_name') and request.user.first_name else request.user.email
            response = requests.delete(
                f'http://localhost:5000/api/product/comments/{comment_id}',
                json={'username': username},
                timeout=5
            )
            logger.info(f"Comment deletion to http://localhost:5000/api/product/comments/{comment_id} returned status {response.status_code}, Response: {response.text}")
            if response.status_code == 200:
                messages.success(request, 'Comment deleted successfully!')
            elif response.status_code == 403:
                messages.error(request, 'You are not authorized to delete this comment.')
            elif response.status_code == 404:
                messages.error(request, 'Comment not found.')
            else:
                logger.warning(f"Comment deletion failed: {response.status_code}, Response: {response.text}")
                messages.error(request, f'Failed to delete comment: API returned status {response.status_code}. Please try again.')
        except requests.RequestException as e:
            logger.error(f"Failed to delete comment to Flask API: {str(e)}")
            messages.error(request, 'Unable to delete comment due to a server error. Please try again later.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    return redirect('home')

def search_results(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(category__icontains=query)
        )
        for product in products:
            if product.available_sizes:
                product.size_list = product.available_sizes.split(',')
            else:
                product.size_list = []
            if product.attributes:
                product.attribute_list = product.attributes.split(',')
            else:
                product.attribute_list = []
    else:
        products = []
    return render(request, 'search_results.html', {'products': products, 'query': query})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                messages.error(request, 'An account with this email already exists.')
                return redirect('signup')
            user = form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                request.session['otp'] = otp
                request.session['otp_email'] = email
                request.session['otp_user_id'] = user.id
                request.session['remember_me'] = bool(request.POST.get('remember_me'))
                request.session.set_expiry(300)
                html_message = render_to_string('emails/otp_email.html', {
                    'otp': otp,
                    'valid_minutes': 5
                })
                plain_message = strip_tags(html_message)
                try:
                    send_mail(
                        subject='Your OTP for SHOPAURA Login',
                        message=plain_message,
                        html_message=html_message,
                        from_email='shopAura002@gmail.com',
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    messages.success(request, 'An OTP has been sent to your email.')
                    return redirect('verify_otp')
                except Exception as e:
                    logger.error(f"Failed to send OTP to {email}: {str(e)}")
                    messages.error(request, 'Failed to send OTP. Please check your email settings or try again later.')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '')
        stored_otp = request.session.get('otp')
        email = request.session.get('otp_email')
        user_id = request.session.get('otp_user_id')
        if not stored_otp or not email or not user_id:
            messages.error(request, 'OTP session expired or invalid. Please try logging in again.')
            return redirect('login')
        if entered_otp == stored_otp:
            try:
                user = User.objects.get(id=user_id, email=email)
                login(request, user)
                remember_me = request.session.get('remember_me', False)
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)
                try:
                    html_message = render_to_string('emails/welcome_email.html', {
                        'user': user,
                        'website_url': request.build_absolute_uri(reverse('home'))
                    })
                    plain_message = strip_tags(html_message)
                    send_mail(
                        subject='Welcome to SHOPAURA!',
                        message=plain_message,
                        html_message=html_message,
                        from_email='shopAura002@gmail.com',
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    logger.info(f"Welcome email sent to {email}")
                except Exception as e:
                    logger.error(f"Failed to send welcome email to {email}: {str(e)}")
                    messages.warning(request, 'Login successful, but failed to send welcome email.')
                # Safely clean up session keys
                if 'otp' in request.session:
                    del request.session['otp']
                if 'otp_email' in request.session:
                    del request.session['otp_email']
                if 'otp_user_id' in request.session:
                    del request.session['otp_user_id']
                if 'otp_user_id' in request.session:
                    del request.session['otp_user_id']
                if 'remember_me' in request.session:
                    del request.session['remember_me']
                messages.success(request, 'Login successful!')
                return redirect('home')
            except User.DoesNotExist:
                messages.error(request, 'User not found. Please try again.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    return render(request, 'verify_otp.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

@login_required
def profile(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at').prefetch_related('order_items')
    context = {
        'user': user,
        'orders': orders,
    }
    return render(request, 'profile.html', context)

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    if not cart_items:
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart')
    total = sum(item.total_price for item in cart_items)
    discount_savings = sum(
        item.quantity * (item.product.original_price - item.product.price)
        for item in cart_items
        if item.product.discount_percentage > 0 or Sale.objects.filter(is_active=True).exists()
    )
    shipping_details = request.session.get('shipping_details', {})
    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            address=shipping_details.get('address'),
            city=shipping_details.get('city'),
            state=shipping_details.get('state'),
            zip_code=shipping_details.get('zip_code'),
            country=shipping_details.get('country'),
        )
        OrderTracking.objects.create(
            order=order,
            status='Pending',
            notes='Order placed by customer.'
        )
        for cart_item in cart_items:
            product = cart_item.product
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=cart_item.quantity,
                price=product.price,
                selected_size=cart_item.selected_size,
                selected_attributes=cart_item.selected_attributes,
            )
            product.stock -= cart_item.quantity
            product.save()
        cart_items.delete()  # Bulk delete after processing
        if 'shipping_details' in request.session:
            del request.session['shipping_details']
        return redirect('payment', order_id=order.id)
    context = {
        'cart_items': [
            {
                'product': item.product,
                'quantity': item.quantity,
                'selected_size': item.selected_size,
                'selected_attributes': item.selected_attributes,
                'total_price': item.total_price
            } for item in cart_items
        ],
        'total': total,
        'discount_savings': discount_savings,
        'shipping_details': shipping_details,
    }
    return render(request, 'checkout.html', context)

@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    tracking_history = order.tracking_history.all()
    status_order = ['Pending', 'Processing', 'Shipped', 'Delivered']
    current_status = order.status
    if current_status == 'Cancelled':
        progress = 0
    else:
        status_index = status_order.index(current_status) if current_status in status_order else 0
        progress = ((status_index + 1) / len(status_order)) * 100
    completed_statuses = []
    if current_status != 'Cancelled':
        for status in status_order:
            status_index = status_order.index(status)
            current_index = status_order.index(current_status) if current_status in status_order else -1
            if status_index <= current_index:
                completed_statuses.append(status)
    context = {
        'order': order,
        'tracking_history': tracking_history,
        'progress': progress,
        'status_order': status_order,
        'completed_statuses': completed_statuses,
    }
    return render(request, 'order_tracking.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(item.total_price for item in cart_items)
    discount_savings = sum(
        item.quantity * (item.product.original_price - item.product.price)
        for item in cart_items
        if item.product.discount_percentage > 0 or Sale.objects.filter(is_active=True).exists()
    )
    context = {
        'cart_items': cart_items,
        'total': total,
        'discount_savings': discount_savings,
    }
    return render(request, 'cart.html', context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        selected_size = request.POST.get('size', '')
        selected_attributes = request.POST.get('attributes', '')
        # Require size selection only if the product has available sizes
        if product.available_sizes and not selected_size:
            messages.warning(request, 'Please select a size for this item.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('product_detail', args=[product_id])))
        # Require attributes selection only if the product has attributes
        if product.attributes and not selected_attributes:
            messages.warning(request, 'Please select an attribute for this item.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('product_detail', args=[product_id])))
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            selected_size=selected_size,
            selected_attributes=selected_attributes,
            defaults={'quantity': 1}
        )
        if not created:
            if cart_item.quantity + 1 <= product.stock:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, 'Product quantity updated in cart!')
            else:
                messages.warning(request, f'Sorry, only {product.stock} item(s) available in stock!')
        else:
            if product.stock > 0:
                messages.success(request, 'Product added to cart!')
            else:
                messages.warning(request, 'Sorry, this product is out of stock!')
                cart_item.delete()
    else:
        # For GET requests, check if size or attributes are required
        if product.available_sizes or product.attributes:
            if product.available_sizes and not product.attributes:
                messages.warning(request, 'Please select a size for this item.')
            elif product.attributes and not product.available_sizes:
                messages.warning(request, 'Please select an attribute for this item.')
            else:
                messages.warning(request, 'Please select a size and attribute for this item.')
            return redirect('product_detail', product_id=product_id)
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': 1}
        )
        if not created:
            if cart_item.quantity + 1 <= product.stock:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, 'Product quantity updated in cart!')
            else:
                messages.warning(request, f'Sorry, only {product.stock} item(s) available in stock!')
        else:
            if product.stock > 0:
                messages.success(request, 'Product added to cart!')
            else:
                messages.warning(request, 'Sorry, this product is out of stock!')
                cart_item.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('home')))

@login_required
def update_cart(request, product_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, user=request.user, product_id=product_id)
        product = cart_item.product
        quantity = int(request.POST.get('quantity', 0))
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, 'Product removed from cart!')
        elif quantity <= product.stock:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully!')
        else:
            cart_item.quantity = product.stock
            cart_item.save()
            messages.warning(request, f'Quantity adjusted to available stock ({product.stock})!')
    return redirect('cart')

@login_required
def remove_from_cart(request, product_id):
    cart_item = get_object_or_404(CartItem, user=request.user, product_id=product_id)
    cart_item.delete()
    messages.success(request, 'Product removed from cart!')
    return redirect('cart')

@login_required
def shipping(request):
    if request.method == 'POST':
        form = ShippingForm(request.POST)
        if form.is_valid():
            request.session['shipping_details'] = {
                'address': form.cleaned_data['address'],
                'city': form.cleaned_data['city'],
                'state': form.cleaned_data['state'],
                'zip_code': form.cleaned_data['zip_code'],
                'country': form.cleaned_data['country'],
            }
            return redirect('checkout')
    else:
        form = ShippingForm()
    return render(request, 'shipping.html', {'form': form})

@login_required
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        logger.info(f"POST request received for order #{order.id}")
        order.payment_status = 'Completed'
        order.status = 'Processing'
        order.save()
        logger.info(f"Order #{order.id} marked as Completed")
        subtotal = sum(item.price * item.quantity for item in order.order_items.all())
        discount_savings = sum(
            item.quantity * (item.product.original_price - item.price)
            for item in order.order_items.all()
            if item.product.discount_percentage > 0
        )
        try:
            html_message = render_to_string('emails/billing_invoice_email.html', {
                'user': request.user,
                'order': order,
                'subtotal': subtotal,
                'discount_savings': discount_savings,
                'website_url': request.build_absolute_uri(reverse('home'))
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject=f'ShopAura - Billing Invoice for Order #{order.id}',
                message=plain_message,
                html_message=html_message,
                from_email='shopAura002@gmail.com',
                recipient_list=[request.user.email],
                fail_silently=False,
            )
            logger.info(f"Billing invoice email sent to {request.user.email} for order #{order.id}")
        except Exception as e:
            logger.error(f"Failed to send billing invoice email to {request.user.email}: {str(e)}")
            messages.warning(request, 'Payment successful, but failed to send billing invoice email.')
        messages.success(request, f'Payment successful for Order #{order.id}!')
        return redirect('profile')
    context = {
        'order': order,
        'total': order.total_amount,
        'shipping_details': {
            'address': order.address,
            'city': order.city,
            'state': order.state,
            'zip_code': order.zip_code,
            'country': order.country,
        },
    }
    return render(request, 'payment.html', context)

def get_category_description(category):
    descriptions = {
        'electronics': 'Discover the latest in technology with our premium electronic devices and accessories.',
        'fashion': 'Express yourself with our trendy collection of fashion items and accessories.',
        'home-living': 'Transform your living space with our elegant home décor and furniture collection.',
        'beauty': 'Enhance your natural beauty with our premium beauty and skincare products.',
        'sports-outdoors': 'Get active with our high-quality sports equipment and outdoor gear.'
    }
    return descriptions.get(category, 'Explore our amazing products')

def seller_signup(request):
    if request.method == 'POST':
        user_form = SignUpForm(request.POST)
        seller_form = SellerSignUpForm(request.POST)
        if user_form.is_valid() and seller_form.is_valid():
            email = user_form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                messages.error(request, 'An account with this email already exists.')
                return redirect('seller_signup')
            user = user_form.save()
            seller = seller_form.save(commit=False)
            seller.user = user
            seller.save()
            messages.success(request, 'Seller account created! Awaiting admin approval.')
            send_mail(
                'New Seller Registration',
                f'A new seller has registered: {user.email}. Please review in the admin panel.',
                'nikhilloomba30@gmail.com',
                ['admin@example.com'],
                fail_silently=True,
            )
            return redirect('seller_login')
    else:
        user_form = SignUpForm()
        seller_form = SellerSignUpForm()
    return render(request, 'seller_signup.html', {
        'user_form': user_form,
        'seller_form': seller_form
    })

@login_required
def seller_dashboard(request):
    if not hasattr(request.user, 'seller_profile'):
        messages.error(request, 'You are not registered as a seller.')
        return redirect('home')
    seller = request.user.seller_profile
    if not seller.is_approved:
        messages.warning(request, 'Your seller account is awaiting admin approval.')
        return render(request, 'seller_dashboard.html', {'submissions': [], 'is_approved': False})
    submissions = SellerProductSubmission.objects.filter(seller=seller)
    return render(request, 'seller_dashboard.html', {
        'submissions': submissions,
        'is_approved': True
    })

@login_required
def seller_product_submit(request):
    if not hasattr(request.user, 'seller_profile') or not request.user.seller_profile.is_approved:
        messages.error(request, 'Your seller account is not approved yet.')
        return redirect('home')
    if request.method == 'POST':
        form = SellerProductSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.seller = request.user.seller_profile
            submission.save()
            messages.success(request, 'Product submitted for admin review!')
            send_mail(
                'New Product Submission',
                f'A new product "{submission.name}" has been submitted by {request.user.email}. Please review in the admin panel.',
                'nikhilloomba30@gmail.com',
                ['admin@example.com'],
                fail_silently=True,
            )
            return redirect('seller_dashboard')
    else:
        form = SellerProductSubmissionForm()
    return render(request, 'seller_product_submit.html', {'form': form})

def seller_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if hasattr(user, 'seller_profile'):
                    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                    request.session['otp'] = otp
                    request.session['otp_email'] = email
                    request.session['otp_user_id'] = user.id
                    request.session['remember_me'] = bool(request.POST.get('remember_me'))
                    request.session.set_expiry(300)  # 5 minutes
                    request.session.modified = True  # Ensure session is saved
                    logger.info(f"OTP generated for {email}: {otp}")
                    html_message = render_to_string('emails/otp_email.html', {
                        'otp': otp,
                        'valid_minutes': 5
                    })
                    plain_message = strip_tags(html_message)
                    try:
                        send_mail(
                            subject='Your OTP for SHOPAURA Seller Login',
                            message=plain_message,
                            html_message=html_message,
                            from_email='shopAura002@gmail.com',
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        logger.info(f"OTP email sent to {email}")
                        messages.success(request, 'An OTP has been sent to your email.')
                        return redirect('verify_seller_otp')
                    except Exception as e:
                        logger.error(f"Failed to send OTP to {email}: {str(e)}")
                        messages.error(request, 'Failed to send OTP. Please check your email settings or try again later.')
                else:
                    messages.error(request, 'This account is not registered as a seller.')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm()
    return render(request, 'seller_login.html', {'form': form})

def verify_seller_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '')
        stored_otp = request.session.get('otp')
        email = request.session.get('otp_email')
        user_id = request.session.get('otp_user_id')
        # Log session state for debugging
        logger.info(f"Verifying OTP for email: {email}, user_id: {user_id}, stored_otp: {stored_otp}")
        if not stored_otp or not email or not user_id:
            messages.error(request, 'OTP session expired or invalid. Please try logging in again.')
            return redirect('seller_login')
        if entered_otp == stored_otp:
            try:
                user = User.objects.get(id=user_id, email=email)
                if hasattr(user, 'seller_profile'):
                    login(request, user)
                    remember_me = request.session.get('remember_me', False)
                    if not remember_me:
                        request.session.set_expiry(0)
                    else:
                        request.session.set_expiry(1209600)
                    try:
                        html_message = render_to_string('emails/welcome_email.html', {
                            'user': user,
                            'website_url': request.build_absolute_uri(reverse('home'))
                        })
                        plain_message = strip_tags(html_message)
                        send_mail(
                            subject='Welcome to SHOPAURA!',
                            message=plain_message,
                            html_message=html_message,
                            from_email='shopAura002@gmail.com',
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        logger.info(f"Welcome email sent to {email}")
                    except Exception as e:
                        logger.error(f"Failed to send welcome email to {request.user.email}: {str(e)}")
                        messages.warning(request, 'Login successful, but failed to send welcome email.')
                    # Safely clean up session keys
                    if 'otp' in request.session:
                        del request.session['otp']
                    if 'otp_email' in request.session:
                        del request.session['otp_email']
                    if 'otp_user_id' in request.session:
                        del request.session['otp_user_id']
                    if 'remember_me' in request.session:
                        del request.session['remember_me']
                    messages.success(request, 'Seller login successful!')
                    return redirect('seller_dashboard')
                else:
                    messages.error(request, 'This account is not registered as a seller.')
                    return redirect('seller_login')
            except User.DoesNotExist:
                messages.error(request, 'User not found. Please try again.')
                return redirect('seller_login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    return render(request, 'verify_seller_otp.html')

def test_email(request):
    try:
        otp = get_random_string(length=6, allowed_chars='0123456789')
        html_message = render_to_string('emails/otp_email.html', {
            'otp': otp,
            'valid_minutes': 5
        })
        plain_message = strip_tags(html_message)
        send_mail(
            subject='Test OTP Email',
            message=plain_message,
            html_message=html_message,
            from_email='shopAura002@gmail.com',
            recipient_list=['test@example.com'],
            fail_silently=False,
        )
        logger.info(f"Test email sent successfully to test@example.com with OTP: {otp}")
        return HttpResponse("Email sent successfully!")
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return HttpResponse(f"Failed to send email: {str(e)}")