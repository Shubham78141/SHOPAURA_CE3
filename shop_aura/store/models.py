from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.http import HttpRequest
from django.contrib.sites.models import Site

def validate_discount(value):
    if value < 0:
        raise ValidationError("Discount cannot be negative.")
    if value > 100:
        raise ValidationError("Discount cannot exceed 100.")

class CustomUserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier for authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model with email as the unique identifier."""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Sale(models.Model):
    """Model to store site-wide sale details."""
    name = models.CharField(max_length=100)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    image_url = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.discount_percentage}% off)"

    class Meta:
        ordering = ['-start_date']

class Product(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Fallback description if Flask API unavailable")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    stock = models.IntegerField(default=0)
    category = models.CharField(max_length=50)
    available_sizes = models.CharField(max_length=100, blank=True, help_text="Comma-separated sizes for fashion products (e.g., S,M,L,XL)")
    attributes = models.CharField(max_length=255, blank=True, help_text="Comma-separated attributes (e.g., color, material)")
    seller = models.ForeignKey('Seller', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')

    def __str__(self):
        return self.name

    @property
    def price(self):
        """Calculate the discounted price, considering both product-specific and active sale discounts."""
        price = self.original_price
        if self.discount_percentage > 0:
            discount = (self.discount_percentage / 100) * price
            price -= discount
        active_sale = Sale.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        if active_sale and active_sale.discount_percentage > 0:
            sale_discount = (active_sale.discount_percentage / 100) * price
            price -= sale_discount
        return max(price, 0)

class CartItem(models.Model):
    """Cart item model linking users to products with quantity and size."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    selected_size = models.CharField(max_length=20, blank=True, help_text="Selected size for fashion products")
    selected_attributes = models.CharField(max_length=255, blank=True, help_text="Selected attributes (e.g., color)")

    def __str__(self):
        size_info = f" (Size: {self.selected_size})" if self.selected_size else ""
        return f"{self.quantity} x {self.product.name}{size_info}"

    @property
    def total_price(self):
        return self.quantity * self.product.price

class Order(models.Model):
    """Order model to track customer purchases."""
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    
    address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.email}"

class OrderItem(models.Model):
    """Individual items within an order."""
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    selected_size = models.CharField(max_length=20, blank=True)
    selected_attributes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        size_info = f" (Size: {self.selected_size})" if self.selected_size else ""
        return f"{self.quantity} x {self.product.name}{size_info} in Order #{self.order.id}"
    
    @property
    def total_price(self):
        return self.quantity * self.price

class OrderTracking(models.Model):
    """Model to track the status history of an order."""
    order = models.ForeignKey(Order, related_name='tracking_history', on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=Order.STATUS_CHOICES)
    updated_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.order.id} - {self.status} at {self.updated_at}"

    class Meta:
        ordering = ['-updated_at']

class Seller(models.Model):
    """Model for sellers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    company_name = models.CharField(max_length=100, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.email} - {self.company_name}"

class SellerProductSubmission(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image_url = models.CharField(max_length=255)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    stock = models.IntegerField(default=0)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    submitted_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_comments = models.TextField(blank=True)
    available_sizes = models.CharField(max_length=100, blank=True, help_text="Comma-separated sizes for fashion products (e.g., S,M,L,XL)")
    attributes = models.CharField(max_length=255, blank=True, help_text="Comma-separated attributes (e.g., color, material)")

    def __str__(self):
        return f"{self.name} - {self.seller.user.email} ({self.status})"

class Complaint(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Resolved', 'Resolved'),
        ('In Progress', 'In Progress'),
    )
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    submitted_at = models.DateTimeField(default=timezone.now)
    response = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Complaint from {self.name} - {self.status}"

    class Meta:
        ordering = ['-submitted_at']

# Store the old stock value before saving
@receiver(pre_save, sender=Product)
def store_old_stock(sender, instance, **kwargs):
    print(f"pre_save triggered for product {instance.name} (ID: {instance.id})")
    try:
        old_instance = Product.objects.get(id=instance.id)
        instance._old_stock = old_instance.stock
        print(f"Old stock for {instance.name}: {instance._old_stock}")
    except Product.DoesNotExist:
        instance._old_stock = None
        print(f"Product {instance.name} is new, no old stock")

# Signal to handle out-of-stock notifications
@receiver(post_save, sender=Product)
def notify_seller_on_out_of_stock(sender, instance, **kwargs):
    print(f"post_save triggered for product {instance.name} (ID: {instance.id})")
    # Check if stock has changed to 0
    old_stock = getattr(instance, '_old_stock', None)
    print(f"Old stock: {old_stock}, New stock: {instance.stock}")
    if old_stock is None:  # New product
        print("Skipping email: Product is new")
        return
    if instance.stock == 0 and old_stock > 0:  # Stock changed to 0
        print("Stock changed to 0, proceeding to send email")
        try:
            # Ensure the product has a seller
            if not instance.seller:
                print("Skipping email: No seller associated with this product")
                return

            # Get seller details
            seller_name = instance.seller.user.get_full_name() or instance.seller.user.email
            print(f"Seller: {seller_name} ({instance.seller.user.email})")

            # Get the current site domain dynamically
            current_site = Site.objects.get_current()
            domain = current_site.domain
            protocol = 'https' if getattr(current_site, 'is_secure', True) else 'http'
            dashboard_url = f"{protocol}://{domain}{reverse('seller_dashboard')}"
            print(f"Dashboard URL: {dashboard_url}")

            # Prepare product details for the email
            product_details = {
                'name': instance.name,
                'category': instance.category,
                'available_sizes': instance.available_sizes if instance.available_sizes else "Not specified",
                'attributes': instance.attributes if instance.attributes else "Not specified",
            }

            # Render email templates
            html_content = render_to_string('email_product_out_of_stock.html', {
                'seller_name': seller_name,
                'product': product_details,
                'dashboard_url': dashboard_url,
            })
            text_content = f"""
            Dear {seller_name},

            Your product "{instance.name}" (Category: {product_details['category']}) is currently out of stock on SHOP.CO. 
            Details:
            - Sizes: {product_details['available_sizes']}
            - Attributes: {product_details['attributes']}
            
            To continue selling, please restock this product as soon as possible.

            You can manage your inventory by visiting your seller dashboard: {dashboard_url}

            For assistance, reach out to us at support@shop.co.

            Best regards,
            The SHOP.CO Team
            """

            # Send email
            print("Attempting to send email...")
            email = EmailMultiAlternatives(
                subject=f'Product Out of Stock: {instance.name}',
                body=text_content,
                from_email='shopAura002@gmail.com',
                to=[instance.seller.user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            print(f"Email sent successfully to {instance.seller.user.email}")

        except Exception as e:
            # Log the error with more details
            print(f"Failed to send out-of-stock email for product {instance.name} (ID: {instance.id}) to {instance.seller.user.email}: {str(e)}")