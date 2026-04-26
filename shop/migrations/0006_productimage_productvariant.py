from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_product_is_featured_featuredslide'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='product/gallery')),
                ('alt_text', models.CharField(blank=True, max_length=250)),
                ('is_feature', models.BooleanField(default=False)),
                ('order', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='shop.product')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='e.g. Size, Color', max_length=100)),
                ('value', models.CharField(help_text='e.g. XL, Red', max_length=100)),
                ('price_modifier', models.DecimalField(
                    decimal_places=2, default=0, max_digits=10,
                    help_text='Added to base product price (can be negative)',
                )),
                ('stock', models.IntegerField(default=0)),
                ('sku', models.CharField(blank=True, max_length=100)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='shop.product')),
            ],
            options={
                'ordering': ['name', 'value'],
                'unique_together': {('product', 'name', 'value')},
            },
        ),
    ]
