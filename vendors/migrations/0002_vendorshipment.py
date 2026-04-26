import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_shippingrate'),
        ('vendors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorShipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('carrier', models.CharField(
                    choices=[
                        ('tpc', 'Tanzania Posts Corporation'),
                        ('dhl', 'DHL Express'),
                        ('fedex', 'FedEx'),
                        ('aramex', 'Aramex'),
                        ('courier', 'Local Courier'),
                        ('self', 'Self / Hand Delivery'),
                        ('other', 'Other'),
                    ],
                    max_length=20,
                )),
                ('carrier_other', models.CharField(blank=True, help_text='Carrier name if "Other" is selected', max_length=100)),
                ('tracking_number', models.CharField(blank=True, max_length=200)),
                ('tracking_url', models.URLField(blank=True, help_text='Optional direct tracking link')),
                ('estimated_delivery', models.DateField(blank=True, null=True, help_text='Expected delivery date shown to customer')),
                ('notes', models.TextField(blank=True, help_text='Packing notes or instructions visible to admin')),
                ('shipped_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shipments',
                    to='order.order',
                )),
                ('vendor', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shipments',
                    to='vendors.vendor',
                )),
            ],
            options={
                'verbose_name': 'Vendor Shipment',
                'verbose_name_plural': 'Vendor Shipments',
                'ordering': ['-shipped_at'],
                'unique_together': {('order', 'vendor')},
            },
        ),
    ]
