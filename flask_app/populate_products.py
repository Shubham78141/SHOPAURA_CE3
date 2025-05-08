import sqlite3
import random
import string
from faker import Faker
import os

# Initialize Faker for generating realistic data
fake = Faker()

# Connect to Flask database
flask_db_path = 'products.db'  # Adjust if Flask db is in a different location
flask_conn = sqlite3.connect(flask_db_path)
flask_cursor = flask_conn.cursor()

# Create Flask ProductDescription table if not exists
flask_cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_description (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        image_url TEXT NOT NULL
    )
''')

# Connect to Django database
django_db_path = 'D:\\At Last\\At Last\\final shopaura\\shop_aura\\db.sqlite3'
django_conn = sqlite3.connect(django_db_path)
django_cursor = django_conn.cursor()

# Clear existing data (optional, comment out if you want to append)
flask_cursor.execute('DELETE FROM product_description')
django_cursor.execute('DELETE FROM store_product')  # Updated table name

# Generate 100 products
products = []
categories = ['electronics', 'fashion', 'home-living', 'beauty', 'sports-outdoors']
for i in range(1, 101):
    name = f"{fake.word().capitalize()} {fake.word().capitalize()} {i}"
    description = fake.paragraph(nb_sentences=3)
    image_url = f"https://example.com/images/product_{i}.jpg"  # Placeholder image URL
    category = random.choice(categories)
    original_price = round(random.uniform(10.0, 500.0), 2)
    stock = random.randint(0, 100)
    discount_percentage = random.choice([0.0, 10.0, 20.0, 30.0])
    
    products.append({
        'product_id': i,
        'name': name,
        'description': description,
        'image_url': image_url,
        'category': category,
        'original_price': original_price,
        'stock': stock,
        'discount_percentage': discount_percentage,
        'available_sizes': 'S,M,L,XL' if category == 'fashion' else '',
        'attributes': 'Red,Blue,Green' if random.choice([True, False]) else ''
    })

# Insert into Flask database
for product in products:
    flask_cursor.execute('''
        INSERT INTO product_description (product_id, name, description, image_url)
        VALUES (?, ?, ?, ?)
    ''', (
        product['product_id'],
        product['name'],
        product['description'],
        product['image_url']
    ))

# Insert into Django database
for product in products:
    django_cursor.execute('''
        INSERT INTO store_product (
            name, image_url, description, original_price, discount_percentage, stock, 
            category, available_sizes, attributes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        product['name'],
        product['image_url'],
        product['description'],  # Added description
        product['original_price'],
        product['discount_percentage'],
        product['stock'],
        product['category'],
        product['available_sizes'],
        product['attributes']
    ))

# Commit changes and close connections
flask_conn.commit()
django_conn.commit()
flask_conn.close()
django_conn.close()

print("Successfully populated 100 products in both Flask and Django databases.")