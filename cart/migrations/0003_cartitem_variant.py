from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0002_cartitem_user_alter_cart_id_alter_cartitem_id'),
        ('shop', '0006_productimage_productvariant'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='variant',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='cart_items',
                to='shop.productvariant',
            ),
        ),
    ]
