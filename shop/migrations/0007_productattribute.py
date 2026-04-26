from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0006_productimage_productvariant'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',  models.CharField(max_length=100, help_text='e.g. Material, Color, Care Instructions')),
                ('value', models.CharField(max_length=500, help_text='e.g. 100% Cotton, Navy Blue, Machine wash 30°C')),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attributes',
                    to='shop.product',
                )),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('product', 'name')},
            },
        ),
    ]
