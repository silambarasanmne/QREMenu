from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from table.models import Category, FoodItem, SubmittedItem, UserProfile

def qr_menu_access(request, restaurant_id='R001', table_number=12):
    request.session['restaurant_id'] = restaurant_id
    request.session['table_number'] = str(table_number)
    request.session.modified = True
    return redirect('table_home')

def staff_login_view(request):
    return redirect('super_admin')

from table.models import Restaurant
from django.db.models import Sum

def super_admin_view(request):
    restaurants = Restaurant.objects.all().order_by('-created_at')
    total_orders = SubmittedItem.objects.count()
    total_revenue = SubmittedItem.objects.aggregate(total=Sum('total_price'))['total'] or 0.00
    active_count = restaurants.filter(is_active=True).count()

    try:
        host = request.get_host()
    except Exception:
        host = "127.0.0.1:8000"

    restaurants_data = []
    for rest in restaurants:
        qr_url = f"http://{host}/menu/{rest.restaurant_id}/table1/"
        qr_img = f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={qr_url}"
        restaurants_data.append({
            'obj': rest,
            'qr_url': qr_url,
            'qr_img': qr_img,
            'admin_user': f"admin_{rest.restaurant_id.lower()}",
            'kitchen_user': f"kitchen_{rest.restaurant_id.lower()}",
            'waiter_user': f"waiter_{rest.restaurant_id.lower()}",
        })

    context = {
        'restaurants_data': restaurants_data,
        'total_restaurants': restaurants.count(),
        'active_count': active_count,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
    }
    return render(request, 'super_admin.html', context)

@login_required(login_url='/login/')
def onboard_restaurant_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        rest_id = request.POST.get('restaurant_id', '').strip().upper()
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        table_count = int(request.POST.get('table_count', 10))
        logo = request.FILES.get('logo')

        if not rest_id:
            rest_id = f"R{Restaurant.objects.count() + 1:03d}"

        # Create Restaurant
        restaurant, created = Restaurant.objects.get_or_create(
            restaurant_id=rest_id,
            defaults={
                'name': name,
                'phone': phone,
                'address': address,
                'table_count': table_count,
                'logo': logo,
                'is_active': True,
            }
        )

        if not created:
            restaurant.name = name
            restaurant.phone = phone
            restaurant.address = address
            restaurant.table_count = table_count
            if logo:
                restaurant.logo = logo
            restaurant.save()

        # Provision Admin User Account
        admin_uname = f"admin_{rest_id.lower()}"
        admin_user, _ = User.objects.get_or_create(username=admin_uname)
        admin_user.set_password('admin123')
        admin_user.save()
        UserProfile.objects.update_or_create(user=admin_user, defaults={'role': 'RESTAURANT_ADMIN', 'restaurant_id': rest_id})

        # Provision Kitchen User Account
        kitchen_uname = f"kitchen_{rest_id.lower()}"
        kitchen_user, _ = User.objects.get_or_create(username=kitchen_uname)
        kitchen_user.set_password('kitchen123')
        kitchen_user.save()
        UserProfile.objects.update_or_create(user=kitchen_user, defaults={'role': 'KITCHEN', 'restaurant_id': rest_id})

        # Provision Waiter User Account
        waiter_uname = f"waiter_{rest_id.lower()}"
        waiter_user, _ = User.objects.get_or_create(username=waiter_uname)
        waiter_user.set_password('waiter123')
        waiter_user.save()
        UserProfile.objects.update_or_create(user=waiter_user, defaults={'role': 'WAITER', 'restaurant_id': rest_id})

        # Seed starter menu categories and food items if none exist
        cat, _ = Category.objects.get_or_create(name='Chef Specials', restaurant_id=rest_id)
        if not FoodItem.objects.filter(restaurant_id=rest_id).exists():
            FoodItem.objects.create(
                restaurant_id=rest_id,
                name='Signature Special Biriyani',
                category=cat,
                description='Fragrant long-grain rice layered with marinated tender meat and authentic secret spices.',
                price=240.00,
                is_available=True
            )
            FoodItem.objects.create(
                restaurant_id=rest_id,
                name='Crispy Chicken Starters',
                category=cat,
                description='Deep-fried succulent chicken pieces tossed with curry leaves & green chillies.',
                price=180.00,
                is_available=True
            )

        messages.success(request, f"Restaurant '{name}' [{rest_id}] onboarded successfully! Provisioned Admin ({admin_uname}), Kitchen ({kitchen_uname}), and Waiter ({waiter_uname}) accounts.")
        return redirect('restaurant_qr_sheet', restaurant_id=rest_id)

def toggle_restaurant_active_view(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, restaurant_id=restaurant_id)
    restaurant.is_active = not restaurant.is_active
    restaurant.save()
    status_str = "Activated 🟢" if restaurant.is_active else "Disabled 🔴"
    messages.success(request, f"Restaurant '{restaurant.name}' service status changed to {status_str}.")
    return redirect('super_admin')

def delete_restaurant_view(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, restaurant_id=restaurant_id)
    name = restaurant.name
    restaurant.delete()
    messages.success(request, f"Restaurant '{name}' [{restaurant_id}] and tenant records removed.")
    return redirect('super_admin')

def restaurant_qr_sheet_view(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, restaurant_id=restaurant_id)
    tables = list(range(1, restaurant.table_count + 1))
    
    try:
        host = request.get_host()
    except Exception:
        host = "127.0.0.1:8000"

    tables_qr = []
    for t in tables:
        qr_target_url = f"http://{host}/menu/{restaurant.restaurant_id}/table{t}/"
        qr_img_api = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_target_url}"
        tables_qr.append({
            'table_number': t,
            'qr_url': qr_target_url,
            'qr_img': qr_img_api
        })

    context = {
        'restaurant': restaurant,
        'tables_qr': tables_qr,
    }
    return render(request, 'qr_sheet.html', context)

from django.http import JsonResponse

def menu_management_view(request):
    rest_id = request.GET.get('restaurant_id') or 'R001'
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'RESTAURANT_ADMIN', 'restaurant_id': rest_id})
        rest_id = profile.restaurant_id
    else:
        profile = None
    
    categories = Category.objects.filter(restaurant_id=rest_id)
    food_items = FoodItem.objects.filter(restaurant_id=rest_id).order_by('category', 'display_order', 'id')

    context = {
        'restaurant_id': rest_id,
        'categories': categories,
        'food_items': food_items,
        'profile': profile,
    }
    return render(request, 'admin_menu.html', context)

def add_food_item_view(request):
    if request.method == 'POST':
        rest_id = request.POST.get('restaurant_id') or 'R001'
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            rest_id = request.user.profile.restaurant_id

        category_id = request.POST.get('category_id')
        new_category_name = request.POST.get('new_category_name', '').strip()
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        is_available = request.POST.get('is_available') == 'on'
        image = request.FILES.get('image')

        if new_category_name:
            category, _ = Category.objects.get_or_create(name=new_category_name, restaurant_id=rest_id)
        else:
            category = get_object_or_404(Category, id=category_id, restaurant_id=rest_id)

        FoodItem.objects.create(
            restaurant_id=rest_id,
            name=name,
            category=category,
            description=description,
            price=price,
            is_available=is_available,
            image=image
        )
        messages.success(request, f"Dish '{name}' added successfully to E-Menu.")
        return redirect('menu_management')

def edit_food_item_view(request, item_id):
    rest_id = request.POST.get('restaurant_id') or request.GET.get('restaurant_id') or 'R001'
    item = get_object_or_404(FoodItem, id=item_id)

    if request.method == 'POST':
        item.name = request.POST.get('name', item.name)
        item.description = request.POST.get('description', item.description)
        item.price = request.POST.get('price', item.price)
        item.is_available = request.POST.get('is_available') == 'on'
        
        category_id = request.POST.get('category_id')
        if category_id:
            item.category = get_object_or_404(Category, id=category_id)

        if request.FILES.get('image'):
            item.image = request.FILES.get('image')

        item.save()
        messages.success(request, f"Dish '{item.name}' updated successfully.")
        return redirect('menu_management')

def delete_food_item_view(request, item_id):
    item = get_object_or_404(FoodItem, id=item_id)
    name = item.name
    item.delete()
    messages.success(request, f"Dish '{name}' removed from menu.")
    return redirect('menu_management')

def toggle_food_availability_view(request, item_id):
    item = get_object_or_404(FoodItem, id=item_id)
    item.is_available = not item.is_available
    item.save()
    return JsonResponse({'success': True, 'is_available': item.is_available, 'item_name': item.name})

def set_table_number(request):

    if request.method == "POST":
        table_number = request.POST.get("table_number")
        request.session["table_number"] = table_number
        request.session.modified = True
        return redirect("menu")   # after setting, go to menu
    return render(request, "enter_table.html")

def home(request):
    return render(request, 'home.html')

def menu_view(request):
    # check if session has table number
    table_number = request.session.get("table_number")

    # if not present → force customer to enter again
    if not table_number:
        return redirect("enter_table_number")   # name of your URL/view for entering table no.

    # else, continue as normal
    return render(request, "menu.html", {
        "table_number": table_number
    })
# def table_home(request):
#     # assign table number to session only if not already set
#     if "table_number" not in request.session:
#         request.session["table_number"] = request.GET.get("table", None)
#     return render(request, "table_home.html")

def clear_table_session(request, table_number):
    """Clear session when counter marks bill as done"""
    if request.session.get("table_number") == str(table_number):
        del request.session["table_number"]
    return redirect("home")


def table_home(request, id=None):
    categories = Category.objects.all()
    table_number = request.session.get('table_number', None) 

    if "table_number" not in request.session:
        request.session["table_number"] = request.GET.get("table", None)
        table_number = request.session.get('table_number', None)

    if id:  # if a category ID is provided in the URL
        selected_category = get_object_or_404(Category, id=id)
    else:  # otherwise, show the first category by default
        selected_category = categories.first()

    # Get the food items for the selected category
    food_items = FoodItem.objects.filter(category=selected_category)

    context = {
        'categories': categories,
        'selected_category': selected_category,
        'food_items': food_items,
        'table_number': table_number
    }


    if request.method == 'POST':
        # Get the table number from the submitted form data
        table_number = request.POST.get('table_number')
        
        # Store the table number in the user's session
        request.session['table_number'] = table_number  # This allows you to access it later

        # Save the submitted item in the database
        SubmittedItem.objects.create(tableNumber=table_number, )  # Save other necessary fields
        print(f"Current Table Number: {table_number}")
    return render(request, 'table_home.html', context)


# Import necessary modules
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import redirect

# Function to generate QR code
def generate_qr(request):
    # URL for the table_home page
    table_home_url = request.build_absolute_uri('/table_home/')
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(table_home_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)
    
    # Return QR image as HTTP response
    return HttpResponse(buffer, content_type='image/png')



def remove_order_item(request, order_id):
    order = get_object_or_404(SubmittedItem, id=order_id)
    order.delete()
    return redirect('kitchen_home')  