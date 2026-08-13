
from django.http import HttpResponse
# from django.contrib import redirects
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages


from table.models import SubmittedItem

import logging

from django.shortcuts import get_object_or_404, redirect
from table.models import orders
logger = logging.getLogger(__name__)
from table.models import SubmittedItem
from collections import defaultdict

from django.db.models import Sum
from kitchen.views import kitchen_home

#   

# in counter/views.py

# def mark_as_done(request, table_number):
#     # your existing logic to mark order as done
#     # ...

#     # clear session so new customer can order
#     if "table_number" in request.session and request.session["table_number"] == str(table_number):
#         del request.session["table_number"]

#     messages.success(request, f"Table {table_number} cleared!")
#     return redirect("/counter/tableList1/?tab=all")

def mark_as_done(request, table_number):
    # Clear order data for that table
    if f"order_{table_number}" in request.session:
        del request.session[f"order_{table_number}"]

    # Clear table number itself from session
    if "table_number" in request.session:
        del request.session["table_number"]

    request.session.modified = True  # make sure changes are saved
    
    return redirect("home")  # or wherever you want to redirect

def mark_served(request, table_number):
    if request.method == 'POST':
        SubmittedItem.objects.filter(tableNumber=table_number, status='ready').update(status='served')
        return redirect('counter_home')

def counter_home(request):
    active_items = SubmittedItem.objects.filter(status__in=['pending', 'confirmed', 'ready', 'served']).order_by('tableNumber', 'order_round', 'id')

    orders_by_table = {}
    table_totals = {}
    ready_orders_by_table = {}
    table_rounds_info = {}

    # Table Status Grid (Tables 1-15)
    tables_status = {}
    for t in range(1, 16):
        tables_status[t] = 'available'

    for order in active_items:
        t_num = order.tableNumber
        if order.status in ['pending', 'confirmed', 'ready', 'served']:
            tables_status[t_num] = 'occupied'
        if order.status == 'ready':
            tables_status[t_num] = 'ready_to_serve'

        if t_num not in orders_by_table:
            orders_by_table[t_num] = {}
            table_totals[t_num] = 0
            table_rounds_info[t_num] = {'max_round': 1, 'has_addons': False, 'rounds': {}}

        round_num = getattr(order, 'order_round', 1) or 1
        if round_num > table_rounds_info[t_num]['max_round']:
            table_rounds_info[t_num]['max_round'] = round_num
            table_rounds_info[t_num]['has_addons'] = True

        if round_num not in table_rounds_info[t_num]['rounds']:
            table_rounds_info[t_num]['rounds'][round_num] = []

        total_item_price = order.quantity * order.price
        table_rounds_info[t_num]['rounds'][round_num].append({
            'name': order.name,
            'quantity': order.quantity,
            'price': order.price,
            'total_price': total_item_price,
            'status': order.status,
            'status_display': order.get_status_display(),
            'round': round_num
        })

        item_name = order.name
        if item_name in orders_by_table[t_num]:
            orders_by_table[t_num][item_name]['quantity'] += order.quantity
            orders_by_table[t_num][item_name]['total_price'] += total_item_price
        else:
            orders_by_table[t_num][item_name] = {
                'quantity': order.quantity,
                'price': order.price,
                'total_price': total_item_price
            }
        table_totals[t_num] += total_item_price

        if order.status == 'ready':
            if t_num not in ready_orders_by_table:
                ready_orders_by_table[t_num] = []
            ready_orders_by_table[t_num].append(order)

    context = {
        'confirmed_orders': orders_by_table,
        'table_totals': table_totals,
        'ready_orders': ready_orders_by_table,
        'tables_status': tables_status,
        'table_rounds_info': table_rounds_info,
    }

    return render(request, 'counter/counter_home.html', context)





def login_view(request):
    return redirect('super_admin')

def logout_view(request):
    return redirect('super_admin')







def menu(request):
    return render(request,'counter/menu.html')

def tableList1(request):
    tab=request.GET.get('tab','recent')
    table_numbers =range(1,16)  # Example: Replace with your logic to get table numbers
    if tab == 'all':
        template_name = 'counter/tableList.html'
        context = {'table_numbers': table_numbers}
    else:
        template_name = 'counter/counter_home.html'
        context = {'table_numbers': table_numbers}

    return render(request, template_name, context)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def get_table_receipt(request, table_number):
    # print(f"Table number requested: {table_number}")
    receipt_data = {
        "1": {
            "customer_name": "John Doe",
            "order_no": "1",
            "date": "15th September 2024",
            "items": [
                {"item": "Grilled Chicken", "qty": 2, "price": "$10.00", "total": "$20.00"},
                {"item": "French Fries", "qty": 1, "price": "$05.00", "total": "$05.00"},
                {"item": "Soda", "qty": 2, "price": "$03.00", "total": "$06.00"},
            ],
            "subtotal": "$31.00",
            "tax": "$2.48",
            "total": "$33.48"
        },
        "2": {
            "customer_name": "Jane Smith",
            "order_no": "789012",
            "date": "16th September 2024",
            "items": [
                {"item": "Burger", "qty": 1, "price": "$8.00", "total": "$8.00"},
                {"item": "Salad", "qty": 1, "price": "$6.00", "total": "$6.00"},
                {"item": "Juice", "qty": 1, "price": "$4.00", "total": "$4.00"},
            ],
            "subtotal": "$18.00",
            "tax": "$1.44",
            "total": "$19.44"
        }
        # Add more table numbers as needed
    }

    # Fetch data based on table_number or return an error if not found
    data = receipt_data.get(str(table_number), {
        "error": "No data found for this table number."
    })

    return JsonResponse(data)




from .models import SubmittedItem

def generate_bill(request, table_number):
    # Get all confirmed items for the specific table
    confirmed_items = SubmittedItem.objects.filter(tableNumber=table_number, status='confirmed')

    # Dictionary to store item names and their aggregated quantity and total price
    order_summary = defaultdict(lambda: {'quantity': 0, 'total_price': 0})

    # Aggregate items by name
    for item in confirmed_items:
        if item.name in order_summary:
            order_summary[item.name]['quantity'] += item.quantity
            order_summary[item.name]['total_price'] += item.total_price
        else:
            order_summary[item.name]['quantity'] = item.quantity
            order_summary[item.name]['total_price'] = item.total_price

    # Prepare data to return as JSON
    orders = [
        {
            'item_name': item_name,
            'quantity': details['quantity'],
            'price': details['total_price'] / details['quantity'],  # Average price per item
            'total_price': details['total_price']
        }
        for item_name, details in order_summary.items()
    ]

    # Calculate total bill amount
    total_amount = sum(item['total_price'] for item in orders)

    # Return the response as JSON
    data = {
        'orders': orders,
        'total_amount': total_amount
    }

    return JsonResponse(data)

from django.shortcuts import render
from .models import SubmittedItem

def recent_tables_view(request):
    # Get the recent submitted items (bills) sorted by creation time
    recent_tables = SubmittedItem.objects.filter(status='confirmed').order_by('-created_at')[:10]  # Get the last 10 confirmed orders

    context = {
        'recent_tables': recent_tables,
    }
    return render(request, 'counter/counter_home.html', context)
def generate_bill_view(request, table_number):
    # Fetch the submitted items for the specific table number
    submitted_items = SubmittedItem.objects.filter(tableNumber=table_number, status='confirmed')
    
    context = {
        'submitted_items': submitted_items,
        'table_number': table_number,
    }
    return render(request, 'counter/bill_view.html', context)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def delete_table_orders(request, table_number):
    items = SubmittedItem.objects.filter(tableNumber=table_number)
    count = items.count()
    items.delete()
    return JsonResponse({
        'status': 'success',
        'message': f'Table #{table_number} payment settled successfully! ({count} items processed)'
    }, status=200)
