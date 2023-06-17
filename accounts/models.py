# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


from django.db import models
from django.contrib.auth.models import User


class ProductData(models.Model):
    gender = models.CharField(max_length=500, blank=True, null=True)
    brand = models.CharField(max_length=500, blank=True, null=True)
    category = models.CharField(max_length=500, blank=True, null=True)
    sub_category = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    condition = models.TextField(max_length=500, blank=True, null=True)
    condition2 = models.TextField(max_length=500, blank=True, null=True)
    material = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=500, blank=True, null=True)
    currency = models.CharField(max_length=500, blank=True, null=True)
    price = models.CharField(max_length=500, blank=True, null=True)
    live_price = models.DecimalField( max_digits=10, decimal_places=2)
    special_price = models.DecimalField( max_digits=10, decimal_places=2)
    aggregate_price = models.DecimalField( max_digits=10, decimal_places=2,blank=True, null=True)
    est_retail_price = models.DecimalField( max_digits=10, decimal_places=2)
    discount = models.DecimalField( max_digits=10, decimal_places=2)
    website = models.CharField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=500, blank=True, null=True)
    datetime_stamp = models.DateField(auto_now=False, auto_now_add=False)
    status = models.CharField(max_length=500, blank=True, null=True)
    sold_date = models.DateField(auto_now=False, auto_now_add=False,null=True,blank=True)

class Configurations(models.Model):
    classification = models.CharField(max_length=500, blank=False, null=False)
    description = models.CharField(max_length=500, blank=False, null=False)
    percentage = models.DecimalField( max_digits=10, decimal_places=2)
    
    def __str__(self) -> str:

        return f'{self.parameter}'
