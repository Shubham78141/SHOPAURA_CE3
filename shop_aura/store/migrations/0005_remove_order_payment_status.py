# Generated by Django 5.2 on 2025-04-11 12:25

from django.db import migrations



class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_order_payment_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='payment_status',
        ),
    ]
