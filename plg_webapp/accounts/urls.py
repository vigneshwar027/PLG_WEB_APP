from django.urls import path,include
from .import views
urlpatterns = [
    # path('', views.home),
    # path('',views.test,name='login'),
    path('',views.login,name='login'),
    path('manage_product/', views.manage_product, name='manage_product'),
    path('manage_user/', views.manage_user, name='manage_user'),
    path('manage_config/', views.manage_config, name='manage_config'),
    path('price_listing/', views.price_listing, name='price_listing'),
    path('import_to_db/', views.import_to_db, name='import_to_db')

]