import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_aura.settings')
django.setup()

from store.models import Product

def add_sample_products():
    # Check if products already exist to avoid duplicates
    if Product.objects.exists():
        print("Products already exist in the database.")
        return
    
    # Sample products to add
    products = [
        # Electronics
        {'name': 'Smartphone X', 'category': 'electronics', 'price': 799.99, 'stock': 20, 'image_url': './static/images/placeholder.jpg'},
        {'name': 'Wireless Headphones', 'category': 'electronics', 'price': 149.99, 'stock': 30, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Smart Watch', 'category': 'electronics', 'price': 249.99, 'stock': 15, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Laptop Pro', 'category': 'electronics', 'price': 1299.99, 'stock': 10, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Digital Camera', 'category': 'electronics', 'price': 499.99, 'stock': 8, 'image_url': '/static/images/placeholder.jpg'},
        
        # Fashion
        {'name': 'Casual T-Shirt', 'category': 'fashion', 'price': 24.99, 'stock': 50, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Designer Jeans', 'category': 'fashion', 'price': 79.99, 'stock': 30, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Leather Jacket', 'category': 'fashion', 'price': 199.99, 'stock': 15, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Casual Sneakers', 'category': 'fashion', 'price': 89.99, 'stock': 25, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Formal Watch', 'category': 'fashion', 'price': 199.99, 'stock': 10, 'image_url': '/static/images/placeholder.jpg'},
        
        # Home & Living
        {'name': 'Modern Coffee Table', 'category': 'home-living', 'price': 299.99, 'stock': 10, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Decorative Throw Pillows', 'category': 'home-living', 'price': 39.99, 'stock': 40, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Ceramic Dinner Set', 'category': 'home-living', 'price': 129.99, 'stock': 20, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Bedside Lamp', 'category': 'home-living', 'price': 49.99, 'stock': 30, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Comfortable Sofa', 'category': 'home-living', 'price': 899.99, 'stock': 5, 'image_url': '/static/images/placeholder.jpg'},
        
        # Beauty
        {'name': 'Facial Cleanser', 'category': 'beauty', 'price': 24.99, 'stock': 40, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Moisturizing Cream', 'category': 'beauty', 'price': 34.99, 'stock': 30, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Premium Lipstick', 'category': 'beauty', 'price': 19.99, 'stock': 50, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Hair Styling Kit', 'category': 'beauty', 'price': 99.99, 'stock': 15, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Essential Oils Set', 'category': 'beauty', 'price': 49.99, 'stock': 25, 'image_url': '/static/images/placeholder.jpg'},
        
        # Sports & Outdoors
        {'name': 'Yoga Mat', 'category': 'sports-outdoors', 'price': 29.99, 'stock': 35, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Fitness Tracker', 'category': 'sports-outdoors', 'price': 79.99, 'stock': 20, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Mountain Bike', 'category': 'sports-outdoors', 'price': 599.99, 'stock': 10, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Running Shoes', 'category': 'sports-outdoors', 'price': 129.99, 'stock': 25, 'image_url': '/static/images/placeholder.jpg'},
        {'name': 'Camping Tent', 'category': 'sports-outdoors', 'price': 199.99, 'stock': 15, 'image_url': '/static/images/placeholder.jpg'},
    ]
    
    # Create products
    for product_data in products:
        Product.objects.create(**product_data)
    
    print(f"Added {len(products)} sample products to the database.")

if __name__ == "__main__":
    add_sample_products()