# Generated by Django 4.1.3 on 2022-12-22 23:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_productdata_sold_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productdata',
            name='sold_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]