from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import Product, Order, Sale, Seller, SellerProductSubmission, User, CartItem, OrderItem, OrderTracking, Complaint
from .forms import ProductForm, SaleForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sessions.models import Session
from django.urls import reverse
from django.db.models.functions import TruncDate
import datetime

@staff_member_required
def admin_dashboard(request):
    today = timezone.now().date()
    week_ago = today - datetime.timedelta(days=7)
    month_ago = today - datetime.timedelta(days=30)

    sales_data = {
        'today': Order.objects.filter(created_at__date=today).aggregate(
            total=Sum('total_amount'), count=Count('id')),
        'week': Order.objects.filter(created_at__gte=week_ago).aggregate(
            total=Sum('total_amount'), count=Count('id')),
        'month': Order.objects.filter(created_at__gte=month_ago).aggregate(
            total=Sum('total_amount'), count=Count('id'))
    }

    customer_stats = {
        'total': User.objects.count(),
        'new_week': User.objects.filter(date_joined__gte=week_ago).count()
    }

    low_stock = Product.objects.filter(stock__lt=5).order_by('stock')
    recent_orders = Order.objects.order_by('-created_at')[:5]
    sales_trend = Order.objects.filter(
        created_at__gte=month_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        sales=Sum('total_amount')
    ).order_by('date')

    context = {
        'sales_data': sales_data,
        'customer_stats': customer_stats,
        'low_stock': low_stock,
        'recent_orders': recent_orders,
        'sales_trend': sales_trend,
    }
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
def admin_products(request):
    search_query = request.GET.get('q', '')
    if search_query:
        products = Product.objects.filter(
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query)
        ).order_by('name')
    else:
        products = Product.objects.all().order_by('name')
    
    context = {
        'products': products,
        'search_query': search_query,
    }
    return render(request, 'admin/products.html', context)

@staff_member_required
def admin_product_edit(request, product_id=None):
    if product_id:
        product = get_object_or_404(Product, id=product_id)
    else:
        product = None

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product saved successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'admin/product_edit.html', {
        'form': form,
        'product': product
    })

@staff_member_required
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('admin_products')
    return render(request, 'admin/product_edit.html', {
        'product': product,
        'delete_confirmation': True
    })

@staff_member_required
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin/orders.html', {'orders': orders})

@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.order_items.all()
    tracking_history = order.tracking_history.all()
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        if new_status in dict(Order.STATUS_CHOICES):
            if order.status != new_status:
                order.status = new_status
                order.save()
                OrderTracking.objects.create(
                    order=order,
                    status=new_status,
                    notes=notes
                )
                messages.success(request, f'Order status updated to {new_status}')
                try:
                    send_mail(
                        subject=f'Order #{order.id} Status Update',
                        message=f'Your order #{order.id} has been updated to {new_status}. Notes: {notes}',
                        from_email='shopAura002@gmail.com',
                        recipient_list=[order.user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    messages.warning(request, f'Status updated, but failed to send notification email: {str(e)}')
            else:
                messages.info(request, 'No status change detected.')
            return redirect('admin_order_detail', order_id=order_id)
    return render(request, 'admin/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'tracking_history': tracking_history,
        'status_choices': Order.STATUS_CHOICES
    })

@staff_member_required
def admin_customers(request):
    search_query = request.GET.get('q', '')
    if search_query:
        customers = User.objects.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query),
            is_staff=False,
            is_superuser=False
        ).exclude(id__in=Seller.objects.values('user_id'))
    else:
        customers = User.objects.filter(
            is_staff=False,
            is_superuser=False
        ).exclude(id__in=Seller.objects.values('user_id'))
    
    context = {
        'customers': customers.order_by('-date_joined'),
        'search_query': search_query,
    }
    return render(request, 'admin/customers.html', context)

@staff_member_required
def admin_inventory(request):
    products = Product.objects.all().order_by('stock')
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_stock = request.POST.get('stock')
        if product_id and new_stock:
            try:
                new_stock = int(new_stock)
                if new_stock < 0:
                    messages.error(request, 'Stock value cannot be negative.')
                else:
                    product = get_object_or_404(Product, id=product_id)
                    product.stock = new_stock
                    product.save()
                    messages.success(request, f'Updated stock for {product.name} to {new_stock}')
            except ValueError:
                messages.error(request, 'Invalid stock value.')
            return redirect('admin_inventory')
    
    context = {
        'products': products,
    }
    return render(request, 'admin/inventory.html', context)

@staff_member_required
def admin_marketing(request):
    month_ago = timezone.now() - datetime.timedelta(days=30)
    new_customers = User.objects.filter(date_joined__gte=month_ago).count()
    total_orders = Order.objects.filter(created_at__gte=month_ago).count()
    total_revenue = Order.objects.filter(created_at__gte=month_ago).aggregate(
        Sum('total_amount')
    )['total_amount__sum'] or 0
    
    context = {
        'new_customers': new_customers,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
    }
    return render(request, 'admin/marketing.html', context)

@staff_member_required
def admin_sales_report(request):
    period = request.GET.get('period', '30')
    days = int(period) if period in ['7', '30', '90'] else 30
    start_date = timezone.now() - datetime.timedelta(days=days)
    sales_by_day = Order.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('date')
    top_products = OrderItem.objects.filter(
        order__created_at__gte=start_date
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        revenue=Sum('price')
    ).order_by('-total_sold')[:5]
    total_stats = Order.objects.filter(
        created_at__gte=start_date
    ).aggregate(
        total_revenue=Sum('total_amount'),
        total_orders=Count('id')
    )
    context = {
        'sales_by_day': sales_by_day,
        'top_products': top_products,
        'total_stats': total_stats,
        'period': days,
    }
    return render(request, 'admin/sales_report.html', context)

@staff_member_required
def admin_sellers(request):
    search_query = request.GET.get('q', '')
    if search_query:
        sellers = Seller.objects.filter(
            Q(user__email__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
    else:
        sellers = Seller.objects.all()
    
    if request.method == 'POST':
        seller_id = request.POST.get('seller_id')
        action = request.POST.get('action')
        seller = get_object_or_404(Seller, id=seller_id)
        
        try:
            # Build absolute URL for the seller dashboard
            dashboard_url = request.build_absolute_uri(reverse('seller_dashboard'))

            if action == 'approve':
                seller.is_approved = True
                seller.save()
                messages.success(request, f'Seller {seller.user.email} approved!')
                
                # Render approval email template
                html_message = render_to_string('emails/email_seller_approved.html', {
                    'seller_name': seller.user.get_full_name() or seller.user.email,
                    'dashboard_url': dashboard_url,
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject='Your SHOPAURA Seller Account Has Been Approved',
                    message=plain_message,
                    html_message=html_message,
                    from_email='shopAura002@gmail.com',
                    recipient_list=[seller.user.email],
                    fail_silently=False,
                )
            
            elif action in ['reject', 'delete']:
                seller_email = seller.user.email  # Store email before deletion
                seller_name = seller.user.get_full_name() or seller_email
                seller.delete()
                messages.success(request, f'Seller {seller_email} {"rejected and deleted" if action == "reject" else "deleted"}!')
                
                # Render rejection email template
                html_message = render_to_string('emails/email_seller_rejected.html', {
                    'seller_name': seller_name,
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject='SHOPAURA Seller Account Application Update',
                    message=plain_message,
                    html_message=html_message,
                    from_email='shopAura002@gmail.com',
                    recipient_list=[seller_email],
                    fail_silently=False,
                )
        except Exception as e:
            messages.warning(request, f'Action completed, but failed to send email: {str(e)}')
        
        return redirect('admin_sellers')
    
    context = {
        'sellers': sellers.order_by('-created_at'),
        'search_query': search_query,
    }
    return render(request, 'admin/sellers.html', context)

@staff_member_required
def admin_product_submissions(request):
    submissions = SellerProductSubmission.objects.all().order_by('-submitted_at')
    
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        action = request.POST.get('action')
        stock = request.POST.get('stock')
        admin_comments = request.POST.get('admin_comments', '')
        submission = get_object_or_404(SellerProductSubmission, id=submission_id)
        
        submission.admin_comments = admin_comments
        submission.reviewed_at = timezone.now()
        
        if action == 'approve':
            submission.status = 'Approved'
            submission.save()
            product = Product.objects.create(
                name=submission.name,
                image_url=submission.image_url,
                original_price=submission.original_price,
                discount_percentage=submission.discount_percentage,
                stock=int(stock) if stock else submission.stock,
                category=submission.category
            )
            messages.success(request, f'Product "{product.name}" approved and added to store!')
            send_mail(
                'Product Approved',
                f'Your product "{submission.name}" has been approved and added to SHOPAURA.',
                'from@example.com',
                [submission.seller.user.email],
                fail_silently=True,
            )
        elif action == 'reject':
            submission.status = 'Rejected'
            submission.save()
            messages.success(request, f'Product submission "{submission.name}" rejected!')
            send_mail(
                'Product Rejected',
                f'Your product "{submission.name}" was rejected. Comments: {admin_comments}',
                'from@example.com',
                [submission.seller.user.email],
                fail_silently=True,
            )
        return STREAMING_TEMPLATE('admin_product_submissions')
    
    context = {
        'submissions': submissions,
    }
    return render(request, 'admin/product_submissions.html', context)

@staff_member_required
def admin_sales(request):
    sales = Sale.objects.all().order_by('-start_date')
    context = {
        'sales': sales,
    }
    return render(request, 'admin/sales.html', context)

@staff_member_required
def admin_sale_edit(request, sale_id=None):
    if sale_id:
        sale = get_object_or_404(Sale, id=sale_id)
    else:
        sale = None

    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            was_active = sale.is_active if sale else False
            sale = form.save()
            if not was_active and sale.is_active:
                # Sale was activated, send emails to logged-in users
                active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
                user_ids = []
                for session in active_sessions:
                    session_data = session.get_decoded()
                    user_id = session_data.get('_auth_user_id')
                    if user_id:
                        user_ids.append(user_id)
                logged_in_users = User.objects.filter(id__in=user_ids).exclude(is_superuser=True)
                email_list = [user.email for user in logged_in_users]
                
                if email_list:
                    print("Sending email to:", email_list)  # Debug: Log the email list
                    html_message = render_to_string('emails/sale_activation_email.html', {
                        'sale_name': sale.name,
                        'discount_percentage': sale.discount_percentage,
                        'end_date': sale.end_date,
                        'website_url': request.build_absolute_uri(reverse('home'))
                    })
                    plain_message = strip_tags(html_message)
                    try:
                        send_mail(
                            subject=f'New Sale Alert: {sale.name} is Live!',
                            message=plain_message,
                            html_message=html_message,
                            from_email='shopAura002@gmail.com',
                            recipient_list=email_list,
                            fail_silently=False,
                        )
                        messages.info(request, f'Notification email sent to {len(email_list)} logged-in users.')
                    except Exception as e:
                        messages.warning(request, f'Sale saved, but failed to send notification emails: {str(e)}')
            
            messages.success(request, 'Sale saved successfully!')
            return redirect('admin_sales')
    else:
        form = SaleForm(instance=sale)

    return render(request, 'admin/sale_edit.html', {
        'form': form,
        'sale': sale
    })

@staff_member_required
def admin_sale_delete(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'Sale deleted successfully!')
        return redirect('admin_sales')
    return render(request, 'admin/sale_edit.html', {
        'sale': sale,
        'delete_confirmation': True
    })

@staff_member_required
def admin_complaints(request):
    complaints = Complaint.objects.all().order_by('-submitted_at')
    search_query = request.GET.get('q', '')
    if search_query:
        complaints = complaints.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    context = {
        'complaints': complaints,
        'search_query': search_query,
    }
    return render(request, 'admin/complaints.html', context)

@staff_member_required
def admin_complaint_detail(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == 'POST':
        response = request.POST.get('response')
        status = request.POST.get('status')
        if response and status in dict(Complaint.STATUS_CHOICES):
            complaint.response = response
            complaint.status = status
            complaint.responded_at = timezone.now()
            complaint.responded_by = request.user
            complaint.save()
            messages.success(request, 'Response sent successfully!')
            try:
                html_message = render_to_string('emails/complaint_response.html', {
                    'name': complaint.name,
                    'complaint_message': complaint.message,
                    'response': response,
                    'website_url': request.build_absolute_uri(reverse('home'))
                })
                plain_message = strip_tags(html_message)
                send_mail(
                    subject='SHOPAURA - Response to Your Complaint',
                    message=plain_message,
                    html_message=html_message,
                    from_email='shopAura002@gmail.com',
                    recipient_list=[complaint.email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f'Response saved, but failed to send email: {str(e)}')
            return redirect('admin_complaints')
    return render(request, 'admin/complaint_detail.html', {
        'complaint': complaint,
        'status_choices': Complaint.STATUS_CHOICES
    })