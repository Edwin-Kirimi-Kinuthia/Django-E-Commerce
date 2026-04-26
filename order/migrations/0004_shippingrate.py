from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_orderitem_vendor'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShippingRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('method', models.CharField(
                    choices=[('standard', 'Standard Shipping'), ('express', 'Express Shipping'), ('free', 'Free Shipping')],
                    default='standard',
                    max_length=20,
                )),
                ('country', models.CharField(blank=True, help_text='Leave blank to apply to all countries', max_length=100)),
                ('rate', models.DecimalField(decimal_places=2, max_digits=8)),
                ('min_order_amount', models.DecimalField(
                    decimal_places=2, default=0, max_digits=10,
                    help_text='Minimum order amount to qualify for this rate',
                )),
                ('free_shipping_threshold', models.DecimalField(
                    blank=True, decimal_places=2, max_digits=10, null=True,
                    help_text='Orders above this amount get free shipping (leave blank to disable)',
                )),
                ('estimated_days', models.CharField(blank=True, help_text='e.g. 3-5 business days', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Shipping Rate',
                'verbose_name_plural': 'Shipping Rates',
                'db_table': 'ShippingRate',
                'ordering': ['rate'],
            },
        ),
    ]
