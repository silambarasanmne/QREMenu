"""
URL configuration for emenu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from . import views
from django.conf.urls.static import static
from django.conf import settings


from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('super_admin'), name='home'),
    path('menu/<str:restaurant_id>/table<int:table_number>/', views.qr_menu_access, name='qr_menu_access'),
    path('menu/table<int:table_number>/', views.qr_menu_access, name='qr_menu_access_default'),
    path('login/', views.staff_login_view, name='staff_login'),
    path('super-admin/', views.super_admin_view, name='super_admin'),
    path('super-admin/onboard/', views.onboard_restaurant_view, name='onboard_restaurant'),
    path('super-admin/toggle/<str:restaurant_id>/', views.toggle_restaurant_active_view, name='toggle_restaurant_active'),
    path('super-admin/delete/<str:restaurant_id>/', views.delete_restaurant_view, name='delete_restaurant'),
    path('super-admin/qr/<str:restaurant_id>/', views.restaurant_qr_sheet_view, name='restaurant_qr_sheet'),
    path('admin-menu/', views.menu_management_view, name='menu_management'),
    path('admin-menu/add/', views.add_food_item_view, name='add_food_item_admin'),
    path('admin-menu/edit/<int:item_id>/', views.edit_food_item_view, name='edit_food_item_admin'),
    path('admin-menu/delete/<int:item_id>/', views.delete_food_item_view, name='delete_food_item_admin'),
    path('admin-menu/toggle/<int:item_id>/', views.toggle_food_availability_view, name='toggle_food_availability_admin'),
    path('staff/', include('counter.urls')),
    path('clear_table/<int:table_number>/', views.clear_table_session, name='clear_table'),
    path('<int:id>/', views.table_home, name='table_home'),
    path('generate_qr/', views.generate_qr, name='generate_qr'),
    path('table_home/', views.table_home, name='table_home'),
    path('admin/', admin.site.urls),
    path('counter/', include('counter.urls')),
    path('kitchen/', include('kitchen.urls')),
    path('table/', include('table.urls')),
    path('remove_order_item/', views.remove_order_item, name='remove_order_item'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
