from datetime import datetime, timedelta
from sqlite3 import IntegrityError
from django.utils import timezone
from decimal import Decimal

from urllib3 import request
from customer.models import *
from pre_designed.models import *
from custom_order.models import *
from reviews.models import *
from tailor.models import *
from dress_order.models import *
from embroidery.models import *
from fabrics.models import *
from favorite_dress.models import *
from favorite_tailor.models import *
from fabrics.models import Fabric
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as auth_logout
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import AuthenticationForm
from functools import wraps
from django.contrib import messages  
from django.db.models import Q, Avg, Count, Sum, F, ExpressionWrapper, DecimalField
from django.core.exceptions import FieldError
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings



def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Check if email exists in database
        try:
            user = User.objects.get(email=email)
            
            # Generate token and uid
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            reset_link = request.build_absolute_uri(
                f'/password-reset-confirm/{uid}/{token}/'
            )
            
            return redirect('password_reset_confirm', uidb64=uid, token=token)
            
        except User.DoesNotExist:
            messages.error(request, 'This email does not exist in the database!')
    
    return render(request, 'auth/password_reset_request.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    
                    # Update session if user is logged in
                    update_session_auth_hash(request, user)
                    
                    messages.success(request, 'Password has been successfully changed!')
                    
                    # Auto login after password reset
                    user = authenticate(username=user.username, password=new_password)
                    if user is not None:
                        login(request, user)
                        return redirect('home')
                    
                else:
                    messages.error(request, 'Not matching passwords!')
            
            return render(request, 'auth/password_reset_confirm.html')
        else:
            messages.error(request, 'Invalid reset link!')
            return redirect('password_reset_request')
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid reset link!')
        return redirect('password_reset_request')
    
def tailor_api(request, tailor_id):
    try:
        tailor = Tailor.objects.select_related('user').get(id=tailor_id)
        data = {
            "success": True,
            "id": tailor.id,
            "name": f"{tailor.user.first_name} {tailor.user.last_name}",
            "business_name": tailor.business_name,
            "business_location": tailor.business_location,
            "profile_picture": tailor.profile_picture.url if tailor.profile_picture else "",
            "rating": tailor.average_rating,
            "expertise": tailor.expertise,
            "price": str(tailor.price),
            "business_description": tailor.business_description,
            "phone": tailor.phone,
            "email": tailor.user.email,
            "services_offered": tailor.services_offered,
        }
        return JsonResponse(data)
    except Tailor.DoesNotExist:
        return JsonResponse({"success": False, "error": "Tailor not found"}, status=404)

def home(request):
    products = PreDesigned.objects.all()
    tailors = Tailor.objects.all()
    embroidery = Embroidery.objects.all()
    fabrics = Fabric.objects.all()
    reviews = Reviews.objects.all()
    favorite_tailor_ids = []
    if request.user.is_authenticated and hasattr(request.user, 'customer'):
        favorite_tailors = FavoriteTailor.objects.filter(user=request.user.customer)
        favorite_tailor_ids = [fav.tailor.id for fav in favorite_tailors]
    return render(request, 'home.html', {'products': products, 
                                         'tailors': tailors, 
                                         'favorite_tailor_ids': favorite_tailor_ids, 
                                         "fabrics": fabrics, 
                                         "embroidery": embroidery,
                                         'reviews': reviews,})

def about(request):
    return render(request, 'about.html')

def terms(request):
    return render(request, 'terms.html') 
   
def privacy(request):
    return render(request, 'privacy.html')

def findTailor(request):
    tailors = Tailor.objects.all()
    products = PreDesigned.objects.all()
    reviews = Reviews.objects.all()
    embroidery = Embroidery.objects.all()
    fabrics = Fabric.objects.all()
    
    # Add ratings directly to tailor objects
    for tailor in tailors:
        tailor_reviews = reviews.filter(tailor=tailor)
        avg_rating = tailor_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        tailor.rating = round(avg_rating, 1)  # Add rating as attribute
    
    favorite_tailor_ids = []
    if request.user.is_authenticated and hasattr(request.user, 'customer'):
        favorite_tailors = FavoriteTailor.objects.filter(user=request.user.customer)
        favorite_tailor_ids = [fav.tailor.id for fav in favorite_tailors]
        
    locations = Tailor.objects.values_list('district', flat=True).distinct()
    locations = [loc for loc in locations if loc]
    
    categories = Tailor._meta.get_field('category').choices
        
    return render(request, 'findTailor.html', {
        'tailors': tailors, 
        'products': products, 
        'reviews': reviews, 
        'embroidery': embroidery, 
        'favorite_tailor_ids': favorite_tailor_ids,
        'fabrics': fabrics,
        'locations': locations,
        'categories': categories,
        # Remove tailor_ratings since we added rating directly to tailor objects
    })

def pre_designed(request):
    products = PreDesigned.objects.all()
    reviews = Reviews.objects.all()
    return render(request, 'pre_designed.html', {'products': products, 'reviews': reviews})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # This should be the email
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')  # Optional remember me functionality

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login the user
            auth_login(request, user)
            
            # Set session expiry based on remember me
            if remember_me:
                # Session will expire after 2 weeks (remember me checked)
                request.session.set_expiry(1209600)  # 2 weeks in seconds
            else:
                # Session will expire when browser is closed (remember me not checked)
                request.session.set_expiry(0)
            
            messages.success(request, "You have successfully logged in!")
            
            # Redirect to appropriate dashboard based on user type
            if hasattr(user, 'tailor'):
                return redirect('tailor_dashboard')
            else:
                return redirect('customer')
        else:
            messages.error(request, "Invalid email or password!")
            return redirect('user_login')
    
    # If GET request, show login form
    return render(request, 'user_login.html')

def signup(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        address = request.POST.get('address')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('user_signup')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect('user_signup')
            
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=full_name.split()[0] if full_name else '',
                last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
            )
            # Ensure Customer exists (signals may have auto-created it)
            customer, _ = Customer.objects.get_or_create(user=user)
            # Explicitly set phone and address provided by signup form
            customer.phone = phone or customer.phone
            customer.address = address or customer.address
            customer.save()
            
            auth_login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('home')  
            
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return redirect('user_signup')
    
    return render(request, 'signup.html')

def logout(request):
    auth_logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('home')

# In your views.py, update the customer function:

def customer(request):
    user = request.user
    customer = Customer.objects.get(user=user)
    products =  PreDesigned.objects.all()
    torder = TOrders.objects.filter(customer=customer).order_by('-order_date')
    dressorder = Order.objects.filter(customer=user).order_by('-order_date')
    favorite_dresses = FavoriteDress.objects.filter(user=customer)
    favorite_tailors = FavoriteTailor.objects.filter(user=customer)

    all_orders = []
    for order in torder:
        if order.deliver is not None:
            status = "Completed"
        else:
            status = "Pending"
        all_orders.append({
            'id': order.id,
            'order_id': f"TORD-{order.id:03d}",
            'garment': order.detailed_description or "Custom Garment",
            'category': "Custom",
            'tailor': order.tailor,
            'delivery_date': order.delivery_date,
            'status': order.status,
            'order_type': "Custom Order",
            'amount': order.get_total_price(),
            'progress': None,  # This is the important field for custom orders
            'timeline': order.status if hasattr(order, 'timeline') else {},
            'order_date': order.order_date if hasattr(order, 'order_date') else None,
            # Custom order specific fields
            'fabric': order.fabrics if hasattr(order, 'fabrics') else '',
            'color': getattr(order, 'color', ''),
            'chest': order.chest,
            'waist': order.waist,
            'hip': order.hip,
            'shoulder': order.shoulder,
            'sleeve': order.sleeve,
            'length': order.length,
            'inseam': order.inseam,
            'neck': order.neck,
            'special_notes': order.special_requests if hasattr(order, 'special_requests') else '',
            # Custom orders 
            'measurements_confirmed': getattr(order, 'measurements_confirmed', None),
            'fabric_selected': getattr(order, 'fabric_selected', None),
            'cutting_started': getattr(order, 'cutting_started', None),
            'stitching_started': getattr(order, 'stitching_started', None),
            'deliver': getattr(order, 'deliver', None),
        })
    
    # Process Pre-designed orders
    for order in dressorder:
        if order.deliver is not None:
            status = "Completed"
        else:
            status = "Pending"
        all_orders.append({
            'id': order.id,
            'order_id': f"DORD-{order.id:03d}",
            'garment': order.product.title if order.product else "Pre-designed Garment",
            'category': order.category or "Pre-designed",
            'tailor': order.tailor,
            'delivery_date': order.delivery_date,
            'status': status,
            'order_type': "Pre-designed",
            'amount': order.get_total_price(),
            'progress': None,
            'timeline': order.status if hasattr(order, 'timeline') else {},
            'order_date': order.order_date if hasattr(order, 'order_date') else None,
            'size': order.size if hasattr(order, 'size') else None,
            # Pre-designed order specific fields
            'fabric': order.product.fabric_type if order.product else '',
            'color': order.product.color if order.product else '',
            'quantity': order.quantity,
            'special_instructions': order.special_instructions if hasattr(order, 'special_instructions') else '',
            # Pre-designed orders 
            'order_confirmed': getattr(order, 'order_confirmed', None),
            'production': getattr(order, 'production', None),
            'quality_check': getattr(order, 'quality_check', None),
            'deliver': getattr(order, 'deliver', None),
        })
    
    # Sort by delivery_date safely
    all_orders.sort(key=lambda x: x['delivery_date'] if x['delivery_date'] else datetime.min, reverse=True)
    
    # Stats
    total_orders = len(all_orders)
    completed_orders = len([order for order in all_orders if order['status'].lower() == 'delivered'])
    pending_orders = len(all_orders) - completed_orders
    favorite_tailors_count = favorite_tailors.count()
    
    return render(request, 'customer.html', {
        'customer': customer,
        'torder': torder,
        'dressorder': dressorder,
        'favorite_dresses': favorite_dresses,
        'favorite_tailors': favorite_tailors,
        'all_orders': all_orders,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'favorite_tailors_count': favorite_tailors_count,
        'products': products
    })
    
    

def updateuser(request):
    return render(request, 'updateuser.html')

def delete_user(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('home')
    return render(request, 'delete_user.html')

@login_required
@csrf_exempt
def update_measurements(request):
    if request.method == 'POST':
        try:
            customer = Customer.objects.get(user=request.user)
            
            # Update measurements from form data
            customer.chest = request.POST.get('chest', '')
            customer.waist = request.POST.get('waist', '')
            customer.hip = request.POST.get('hip', '')
            customer.shoulder = request.POST.get('shoulder', '')
            customer.sleeve = request.POST.get('sleeve', '')
            customer.length = request.POST.get('length', '')
            customer.inseam = request.POST.get('inseam', '')
            customer.neck = request.POST.get('neck', '')
            
            customer.save()
            
            return JsonResponse({
                'success': True,
                'chest': customer.chest,
                'waist': customer.waist,
                'hip': customer.hip,
                'shoulder': customer.shoulder,
                'sleeve': customer.sleeve,
                'length': customer.length,
                'inseam': customer.inseam,
                'neck': customer.neck,
            })
            
        except Customer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Customer profile not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})







#-----------------------------------------------------------------


@login_required
def create_order(request):
    if request.method == 'POST':
        try:
            # Get form data
            product_id = request.POST.get('product_id')
            tailor_id = request.POST.get('tailor_id')
            quantity = int(request.POST.get('quantity', 1))
            price = Decimal(request.POST.get('price', 0))
            size = request.POST.get('size', 'S')
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            special_instructions = request.POST.get('special_instructions', '')
            
            # Validate required fields
            if not all([product_id, tailor_id, full_name, phone, address]):
                messages.error(request, "Please fill in all required fields.")
                return redirect('pre_designed')
            
            # Validate quantity and price
            if quantity <= 0:
                messages.error(request, "Quantity must be at least 1.")
                return redirect('pre_designed')
            
            if price <= 0:
                messages.error(request, "Invalid price.")
                return redirect('pre_designed')
            
            # Get objects with error handling
            try:
                product = PreDesigned.objects.get(id=product_id)
                tailor = Tailor.objects.get(id=tailor_id)
            except PreDesigned.DoesNotExist:
                messages.error(request, "Selected product does not exist.")
                return redirect('pre_designed')
            except Tailor.DoesNotExist:
                messages.error(request, "Selected tailor does not exist.")
                return redirect('pre_designed')
            
            # Create the order
            order = Order.objects.create(
                customer=request.user,
                tailor=tailor,
                product=product,
                quantity=quantity,
                price=price,
                address=address,
                number=phone,
                size=size,
                category=product.category,
                special_instructions=special_instructions,
                delivery_date=timezone.now() + timedelta(days=10)  # 10 days from now
            )
            
            messages.success(request, f"Order placed successfully! Your order ID is #{order.id}")
            return redirect('customer')
            
        except ValueError as e:
            messages.error(request, f"Invalid input: {str(e)}")
            return redirect('pre_designed')
        except Exception as e:
            messages.error(request, f"Error creating order: {str(e)}")
            return redirect('pre_designed')
    
    # If not POST request, redirect to pre_designed page
    return redirect('pre_designed')
    


#----------------------------------------------------------------


def tailor_signup(request):
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        business_name = request.POST.get('business_name')
        category = request.POST.get('specialization')
        expertise = request.POST.get('experience')
        business_location = request.POST.get('business_location')
        nid_number = request.POST.get('nid_number')
        profile_picture = request.FILES.get('profile_picture')
        tailor_about = request.POST.get('tailor_about')
        business_description = request.POST.get('business_description')
        price = request.POST.get('price', 0.0)
        district = request.POST.get('district')
        service_offered = request.POST.get('service_offered')
        
        # Validate passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('user_signup')
            
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect('user_signup')
            
        try:
            # Create User
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=full_name.split()[0] if full_name else '',
                last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
            )
            # Ensure Customer exists and explicitly set phone/address/profile_picture
            customer, _ = Customer.objects.get_or_create(user=user)
            # preferentially use provided values; do not leave None
            customer.phone = phone or (customer.phone or '')
            customer.address = business_location or (customer.address or '')
            if profile_picture:
                customer.profile_picture = profile_picture
            customer.save()
            
            # Normalize expertise/category from multiple possible form names
            exp_val = (expertise or request.POST.get('expertise') or request.POST.get('experience') or '').strip()
            cat_val = (category or request.POST.get('category') or request.POST.get('specialization') or '').strip()

            tailor = Tailor.objects.create(
                user=user,
                business_name=business_name,
                business_location=business_location,
                phone=phone,
                NID=nid_number,
                profile_picture=profile_picture,
                services_offered=service_offered,
                expertise=exp_val,
                category=cat_val,
                average_rating=0.0,
                is_available=True,
                tailor_about=tailor_about,
                business_description=business_description,
                price=price,
                district=district
            )
            # Defensive save in case of model/field mismatches
            try:
                if exp_val and getattr(tailor, 'expertise', None) != exp_val:
                    tailor.expertise = exp_val
                if cat_val and getattr(tailor, 'category', None) != cat_val:
                    tailor.category = cat_val
                if profile_picture and getattr(tailor, 'profile_picture', None) != profile_picture:
                    tailor.profile_picture = profile_picture
                tailor.save()
            except Exception as _e:
                # keep silent; enable logging if you need to debug
                print("Warning: unable to force-save some Tailor fields:", str(_e))

            
            
            from django.contrib.auth import login as auth_login
            from django.contrib.auth.backends import ModelBackend
            
            # Use the default authentication backend
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            messages.success(request, "Tailor account created successfully!")
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return redirect('user_signup')
    
    return render(request, 'signup.html')

def tailor_dashboard(request):
    user = request.user
    
    # Get tailor profile
    try:
        tailor = Tailor.objects.get(user=user)
    except Tailor.DoesNotExist:
        return render(request, 'error.html', {'error': 'Tailor profile not found'})
    
    # Get fabrics for this tailor
    fabrics = Fabric.objects.filter(tailor=tailor)

    # Get all orders assigned to this tailor (from other customers)
    custom_orders = TOrders.objects.filter(tailor=tailor).order_by('-order_date')
    pre_designed_orders = Order.objects.filter(tailor=tailor).order_by('-order_date')

    tailor_as_customer = Customer.objects.filter(user=user).first()
    my_own_orders = []

    if tailor_as_customer:
        # Custom orders where tailor is the customer
        my_custom_orders = TOrders.objects.filter(customer=tailor_as_customer).order_by('-order_date')
        
        for order in my_custom_orders:
            # Determine status
            if hasattr(order, 'deliver') and order.deliver is not None:
                status = "Completed"
            elif hasattr(order, 'status') and order.status:
                status = order.status
            else:
                status = "Pending"
            
            # METHOD 1: Check if order has direct embroidery ForeignKey
            selected_embroidery_info = []
            if hasattr(order, 'embroidery') and order.embroidery:
                try:
                    embroidery_obj = order.embroidery
                    design_image_url = ""
                    if embroidery_obj.design_image and hasattr(embroidery_obj.design_image, 'url'):
                        design_image_url = request.build_absolute_uri(embroidery_obj.design_image.url)
                    
                    selected_embroidery_info.append({
                        'id': embroidery_obj.id,
                        'title': embroidery_obj.title,
                        'description': embroidery_obj.description,
                        'design_image': design_image_url,
                        'fabric_type': embroidery_obj.fabric_type,
                        'thread_type': embroidery_obj.thread_type,
                        'color': embroidery_obj.color,
                        'complexity_level': embroidery_obj.complexity_level,
                        'price': str(embroidery_obj.price),
                        'estimated_time': str(embroidery_obj.estimated_time) if embroidery_obj.estimated_time else None,
                    })
                except Exception as e:
                    print(f"Error getting direct embroidery info: {str(e)}")
            
            # METHOD 2: If no direct ForeignKey, try selected_embroidery_info field
            if not selected_embroidery_info:
                try:
                    if hasattr(order, 'selected_embroidery_info') and order.selected_embroidery_info:
                        if isinstance(order.selected_embroidery_info, str):
                            selected_embroidery_info = json.loads(order.selected_embroidery_info)
                        else:
                            selected_embroidery_info = order.selected_embroidery_info
                        
                        # Process embroidery images to include full URLs
                        for emb in selected_embroidery_info:
                            if isinstance(emb, dict) and emb.get('design_image'):
                                if not emb['design_image'].startswith(('http://', 'https://')):
                                    # This is a relative path, build full URL
                                    try:
                                        emb['design_image'] = request.build_absolute_uri(emb['design_image'])
                                    except:
                                        pass
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"Error parsing selected_embroidery_info: {str(e)}")
                    selected_embroidery_info = []
            
            # Get fabric info safely - Handle both string and object WITH IMAGE URL
            fabric_info = {}
            fabric_name = ""
            fabric_length_needed = ""
            if hasattr(order, 'fabrics'):
                if isinstance(order.fabrics, str):
                    fabric_name = order.fabrics
                elif order.fabrics and hasattr(order.fabrics, 'name'):
                    fabric_name = order.fabrics.name
                    try:
                        fabric_image_url = ""
                        if order.fabrics.image and hasattr(order.fabrics.image, 'url'):
                            fabric_image_url = request.build_absolute_uri(order.fabrics.image.url)
                        
                        fabric_info = {
                            'name': order.fabrics.name if order.fabrics.name else '',
                            'type': getattr(order.fabrics, 'fabric_type', ''),
                            'color': getattr(order.fabrics, 'color', ''),
                            'pattern': getattr(order.fabrics, 'pattern', ''),
                            'texture': getattr(order.fabrics, 'texture', ''),
                            'width': str(getattr(order.fabrics, 'width', 0)),
                            'price_per_meter': str(getattr(order.fabrics, 'price_per_meter', 0)),
                            'length_needed': str(getattr(order, 'meter', 0)),
                            'image_url': fabric_image_url,
                            'description': getattr(order.fabrics, 'description', '')
                        }
                        fabric_length_needed = str(getattr(order, 'meter', 0))
                    except Exception as e:
                        print(f"Error getting fabric info: {str(e)}")
                        fabric_info = {}
            
            # Get garment type and occasion
            garment_type = getattr(order, 'garment_type', '')
            occasion = getattr(order, 'occasion', '')
            
            my_own_orders.append({
                'id': order.id,
                'order_id': f"TORD-{order.id:03d}",
                'garment': getattr(order, 'detailed_description', "Custom Garment"),
                'garment_type': garment_type,
                'occasion': occasion,
                'category': getattr(order.occasion, 'category', "Custom") if hasattr(order, 'occasion') and order.occasion else "Custom",
                'tailor': order.tailor,
                'delivery_date': getattr(order, 'delivery_date', None),
                'status': status,
                'order_type': "Custom Order",
                'amount': order.get_total_price() if hasattr(order, 'get_total_price') else getattr(order, 'price', 0),
                'progress': None,
                'order_date': getattr(order, 'order_date', None),
                'tailor': order.tailor,
                'fabric': fabric_name,
                'fabric_length_needed': fabric_length_needed,
                'color': order.fabrics.color if hasattr(order.fabrics, 'color') else '',
                'chest': getattr(order, 'chest', ''),
                'waist': getattr(order, 'waist', ''),
                'hip': getattr(order, 'hip', ''),
                'shoulder': getattr(order, 'shoulder', ''),
                'sleeve': getattr(order, 'sleeve', ''),
                'neck': getattr(order, 'neck', ''),
                'length': getattr(order, 'length', ''),
                'inseam': getattr(order, 'inseam', ''),
                'special_notes': getattr(order, 'special_requests', ''),
                'inspiration': getattr(order, 'inspiration', ''),
                'contact_number': getattr(order, 'contact_number', ''),
                'address': getattr(order, 'address', ''),
                'gender': getattr(order, 'gender', ''),
                'measurements_confirmed': getattr(order, 'measurements_confirmed', None),
                'fabric_selected': getattr(order, 'fabric_selected', None),
                'cutting_started': getattr(order, 'cutting_started', None),
                'stitching_started': getattr(order, 'stitching_started', None),
                'deliver': getattr(order, 'deliver', None),
                'is_my_order': True,
                'is_own_order': True,
                'selected_embroidery_info': json.dumps(selected_embroidery_info),   
                'selected_fabric_info': json.dumps(fabric_info),
                'embroidery_total_price': str(getattr(order, 'embroidery_total_price', 0)),
                'fabric_total_price': str(getattr(order, 'fabric_total_price', 0)),
                'measurements_confirmed': getattr(order, 'measurements_confirmed', None),
            })
        
        # Pre-designed orders where tailor is the customer
        my_pre_designed_orders = Order.objects.filter(customer=user).order_by('-order_date')
        
        for order in my_pre_designed_orders:
            # Determine status
            if hasattr(order, 'deliver') and order.deliver is not None:
                status = "Completed"
            elif hasattr(order, 'status') and order.status:
                status = order.status
            else:
                status = "Pending"
            
            my_own_orders.append({
                'id': order.id,
                'order_id': f"DORD-{order.id:03d}",
                'garment': order.product.title if hasattr(order, 'product') and order.product else "Pre-designed Garment",
                'category': getattr(order, 'category', "Pre-designed"),
                'garment_type': order.product.category if hasattr(order, 'product') and order.product else '',
                'tailor': order.tailor,
                'delivery_date': getattr(order, 'delivery_date', None),
                'status': status,
                'order_type': "Pre-designed",
                'amount': order.get_total_price() if hasattr(order, 'get_total_price') else getattr(order, 'price', 0),
                'progress': None,
                'order_date': getattr(order, 'order_date', None),
                'tailor': order.tailor,
                'size': getattr(order, 'size', None),
                'fabric': order.product.fabric_type if hasattr(order, 'product') and order.product else '',
                'color': order.product.color if hasattr(order, 'product') and order.product else '',
                'quantity': getattr(order, 'quantity', 1),
                'special_instructions': getattr(order, 'special_instructions', ''),
                'order_confirmed': getattr(order, 'order_confirmed', None),
                'production': getattr(order, 'production', None),
                'quality_check': getattr(order, 'quality_check', None),
                'deliver': getattr(order, 'deliver', None),
                'is_my_order': True,
                'is_own_order': True,
            })
        
        # Sort own orders by delivery date
        my_own_orders.sort(key=lambda x: x['delivery_date'] if x['delivery_date'] else datetime.min, reverse=True)
        # Get tailor's products and services
    products = PreDesigned.objects.filter(tailor=tailor)
    embroidery_services = Embroidery.objects.filter(tailor=tailor)

    # Get reviews for this tailor
    try:
        reviews = Reviews.objects.filter(tailor=tailor).order_by('-timestamp')
    except:
        try:
            reviews = Reviews.objects.filter(tailor=tailor).order_by('-created_at')
        except:
            reviews = Reviews.objects.filter(tailor=tailor).order_by('-id')

    # Calculate statistics
    active_orders = custom_orders.filter(status__in=['pending', 'processing', 'in_progress']).count() + \
                    pre_designed_orders.filter(status__in=['pending', 'processing', 'in_progress']).count()

    completed_orders = custom_orders.filter(status__in=['completed', 'delivered', 'finished']).count() + \
                       pre_designed_orders.filter(status__in=['completed', 'delivered', 'finished']).count()

    # Calculate average rating
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    # Current month/year for monthly aggregates
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Calculate earnings
    monthly_earnings_pre = pre_designed_orders.filter(
        status__in=['completed', 'delivered'],
        delivery_date__month=current_month,
        delivery_date__year=current_year
    ).aggregate(
        total=Sum(ExpressionWrapper(
            F('price') * F('quantity'), 
            output_field=DecimalField()
        ))
    )['total'] or 0

    monthly_earnings_custom = custom_orders.filter(
        status__in=['completed', 'delivered'],
        delivery_date__month=current_month,
        delivery_date__year=current_year
    ).aggregate(total=Sum('price'))['total'] or 0

    monthly_earnings = monthly_earnings_pre + monthly_earnings_custom

    # Total earnings (all time)
    total_earnings_pre = pre_designed_orders.filter(
        status__in=['completed', 'delivered']
    ).aggregate(
        total=Sum(ExpressionWrapper(
            F('price') * F('quantity'), 
            output_field=DecimalField()
        ))
    )['total'] or 0

    total_earnings_custom = custom_orders.filter(
        status__in=['completed', 'delivered']
    ).aggregate(total=Sum('price'))['total'] or 0

    total_earnings = total_earnings_pre + total_earnings_custom

    # Pending payments
    pending_payments_pre = pre_designed_orders.filter(
        status__in=['pending', 'processing', 'in_progress']
    ).aggregate(
        total=Sum(ExpressionWrapper(
            F('price') * F('quantity'), 
            output_field=DecimalField()
        ))
    )['total'] or 0

    pending_payments_custom = custom_orders.filter(
        status__in=['pending', 'processing', 'in_progress']
    ).aggregate(total=Sum('price'))['total'] or 0

    pending_payments = pending_payments_pre + pending_payments_custom

    # Recent transactions (last 10 delivered)
    recent_transactions = []
    
    for o in pre_designed_orders.filter(status__in=['completed', 'delivered'])[:10]:
        amount = (o.price * o.quantity) if hasattr(o, 'price') and hasattr(o, 'quantity') else getattr(o, 'price', 0)
        recent_transactions.append({
            'date': o.delivery_date,
            'order_id': f"DORD-{o.id:03d}",
            'amount': amount,
            'status': 'Completed',
        })

    for o in custom_orders.filter(status__in=['completed', 'delivered'])[:10]:
        amount = getattr(o, 'price', 0)
        recent_transactions.append({
            'date': o.delivery_date,
            'order_id': f"TORD-{o.id:03d}",
            'amount': amount,
            'status': 'Completed',
        })

    recent_transactions.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)

    # Combine all customer orders for display (orders from other customers)
    all_customer_orders = []

    for o in custom_orders:
        # Get embroidery info directly through ForeignKey
        selected_embroidery_info = []
        if o.embroidery:
            try:
                embroidery_obj = o.embroidery
                selected_embroidery_info.append({
                    'id': embroidery_obj.id,
                    'title': embroidery_obj.title,
                    'description': embroidery_obj.description,
                    'design_image': embroidery_obj.design_image.url if embroidery_obj.design_image else None,
                    'fabric_type': embroidery_obj.fabric_type,
                    'thread_type': embroidery_obj.thread_type,
                    'color': embroidery_obj.color,
                    'complexity_level': embroidery_obj.complexity_level,
                    'price': str(embroidery_obj.price),
                    'estimated_time': str(embroidery_obj.estimated_time) if embroidery_obj.estimated_time else None,
                })
            except Exception as e:
                print(f"Error getting embroidery info: {str(e)}")

        # Get fabric info directly through ForeignKey
        fabric_info = {}
        fabric_name = ""
        fabric_length_needed = ""
        fabric_image_url = ""

        if o.fabrics:
            try:
                fabric_obj = o.fabrics
                fabric_name = fabric_obj.name
                
                fabric_info = {
                    'id': fabric_obj.id,
                    'name': fabric_obj.name,
                    'description': getattr(fabric_obj, 'description', ''),
                    'type': getattr(fabric_obj, 'fabric_type', ''),
                    'color': getattr(fabric_obj, 'color', ''),
                    'pattern': getattr(fabric_obj, 'pattern', ''),
                    'texture': getattr(fabric_obj, 'texture', ''),
                    'width': str(getattr(fabric_obj, 'width', 0)),
                    'length_available': str(getattr(fabric_obj, 'length_available', 0)),
                    'price_per_meter': str(getattr(fabric_obj, 'price_per_meter', 0)),
                    'length_needed': str(getattr(o, 'meter', 0)),
                    'image_url': request.build_absolute_uri(fabric_obj.image.url) if fabric_obj.image and hasattr(fabric_obj.image, 'url') else None,
                    'is_available': getattr(fabric_obj, 'is_available', True)
                }
                fabric_length_needed = str(getattr(o, 'meter', 0))
                
                if fabric_obj.image and hasattr(fabric_obj.image, 'url'):
                    fabric_image_url = request.build_absolute_uri(fabric_obj.image.url)
                
            except Exception as e:
                print(f"Error getting fabric info: {str(e)}")

        # Get customer info safely
        customer_info = {}
        if o.customer:
            try:
                customer_info = {
                    'id': o.customer.id,
                    'first_name': o.customer.user.first_name if o.customer.user else "Unknown",
                    'last_name': o.customer.user.last_name if o.customer.user else "Customer",
                    'email': o.customer.user.email if o.customer.user else "",
                    'phone': getattr(o.customer, 'phone', ''),
                    'address': getattr(o.customer, 'address', '')
                }
            except Exception:
                customer_info = {
                    'id': '',
                    'first_name': 'Unknown',
                    'last_name': 'Customer',
                    'email': '',
                    'phone': '',
                    'address': ''
                }
        else:
            customer_info = {
                'id': '',
                'first_name': 'Unknown',
                'last_name': 'Customer',
                'email': '',
                'phone': '',
                'address': ''
            }
        
        # Add to all_customer_orders list
        all_customer_orders.append({
            'id': o.id,
            'order_id': f"TORD-{o.id:03d}",
            'category': getattr(o, 'category', "Custom"),
            'customer': customer_info,
            'delivery_date': getattr(o, 'delivery_date', None),
            'status': getattr(o, 'status', "In Progress"),
            'order_type': "Custom Order",
            'amount': o.get_total_price() if hasattr(o, 'get_total_price') else getattr(o, 'price', 0),
            'order_date': getattr(o, 'order_date', None),
            'tailor': o.tailor,
            'fabric': fabric_name,
            'fabric_length_needed': fabric_length_needed,
            'color': getattr(o, 'color', ''),
            'chest': getattr(o, 'chest', ''),
            'waist': getattr(o, 'waist', ''),
            'hip': getattr(o, 'hip', ''),
            'shoulder': getattr(o, 'shoulder', ''),
            'sleeve': getattr(o, 'sleeve', ''),
            'length': getattr(o, 'length', ''),
            'inseam': getattr(o, 'inseam', ''),
            'neck': getattr(o, 'neck', ''),
            'special_notes': getattr(o, 'special_requests', ''),
            'inspiration': getattr(o, 'inspiration', ''),
            'garment': getattr(o, 'detailed_description', "Custom Garment"),
            'garment_type': getattr(o, 'garment_type', ''),
            'occasion': getattr(o, 'occasion', ''),
            'contact_number': getattr(o, 'contact_number', ''),
            'address': getattr(o, 'address', ''),
            'gender': getattr(o, 'gender', ''),
            'measurements_confirmed': getattr(o, 'measurements_confirmed', None),
            'fabric_selected': getattr(o, 'fabric_selected', None),
            'cutting_started': getattr(o, 'cutting_started', None),
            'stitching_started': getattr(o, 'stitching_started', None),
            'deliver': getattr(o, 'deliver', None),
            'is_my_order': False,
            'is_own_order': False,
            'selected_embroidery_info': json.dumps(selected_embroidery_info), 
            'selected_fabric_info': json.dumps(fabric_info),                 
            'embroidery_total_price': str(getattr(o, 'embroidery_total_price', 0)),
            'fabric_total_price': str(getattr(o, 'fabric_total_price', 0)),
        })

    for o in pre_designed_orders:
        # Get customer info safely
        customer_info = {}
        if hasattr(o, 'customer'):
            try:
                if hasattr(o.customer, 'user'):
                    customer_info = {
                        'id': o.customer.id,
                        'first_name': o.customer.user.first_name,
                        'last_name': o.customer.user.last_name,
                        'email': o.customer.user.email,
                        'phone': getattr(o.customer, 'phone', ''),
                        'address': getattr(o.customer, 'address', '')
                    }
                else:
                    customer_info = {
                        'id': o.customer.id,
                        'first_name': getattr(o.customer, 'first_name', 'Unknown'),
                        'last_name': getattr(o.customer, 'last_name', 'Customer'),
                        'email': getattr(o.customer, 'email', ''),
                        'phone': getattr(o.customer, 'phone', ''),
                        'address': getattr(o.customer, 'address', '')
                    }
            except Exception:
                customer_info = {
                    'id': '',
                    'first_name': 'Unknown',
                    'last_name': 'Customer',
                    'email': '',
                    'phone': '',
                    'address': ''
                }
        else:
            customer_info = {
                'id': '',
                'first_name': 'Unknown',
                'last_name': 'Customer',
                'email': '',
                'phone': '',
                'address': ''
            }
        
        # CHANGED: Use append instead of all_custom_order.append
        all_customer_orders.append({
            'id': o.id,
            'order_id': f"DORD-{o.id:03d}",
            'garment': o.product.title if hasattr(o, 'product') and o.product else "Pre-designed Garment",
            'category': getattr(o, 'category', "Pre-designed"),
            'customer': customer_info,
            'delivery_date': getattr(o, 'delivery_date', None),
            'status': getattr(o, 'status', "In Progress"),
            'order_type': "Pre-designed",
            'amount': o.get_total_price() if hasattr(o, 'get_total_price') else getattr(o, 'price', 0),
            'order_date': getattr(o, 'order_date', None),
            'size': getattr(o, 'size', None),
            'tailor': o.tailor,
            'fabric': o.product.fabric_type if hasattr(o, 'product') and o.product else '',
            'color': o.product.color if hasattr(o, 'product') and o.product else '',
            'quantity': getattr(o, 'quantity', 1),
            'special_instructions': getattr(o, 'special_instructions', ''),
            'order_confirmed': getattr(o, 'order_confirmed', None),
            'production': getattr(o, 'production', None),
            'quality_check': getattr(o, 'quality_check', None),
            'deliver': getattr(o, 'deliver', None),
            'is_my_order': False,
            'is_own_order': False,
        })

    # Sort all orders by delivery date
    all_customer_orders.sort(key=lambda x: x['delivery_date'] if x['delivery_date'] else datetime.min, reverse=True)

    # Combine all orders for general display
    all_orders = my_own_orders + all_customer_orders
    all_orders.sort(key=lambda x: x['delivery_date'] if x['delivery_date'] else datetime.min, reverse=True)

    return render(request, 'tailor.html', {
        'tailor': tailor,
        'custom_orders': custom_orders,
        'pre_designed_orders': pre_designed_orders,
        'all_orders': all_orders,
        'my_own_orders': my_own_orders,
        'all_customer_orders': all_customer_orders,
        'products': products,
        'embroidery_services': embroidery_services,
        'reviews': reviews,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'average_rating': round(average_rating, 1),
        'monthly_earnings': monthly_earnings,
        'total_earnings': total_earnings,
        'pending_payments': pending_payments,
        'recent_transactions': recent_transactions[:5],
        
        # Additional stats
        'my_orders_count': len(my_own_orders),
        'customer_orders_count': len(all_customer_orders),
        'total_orders_count': len(all_orders),
        'fabrics': fabrics,
    }) 
    
    
@login_required
@csrf_exempt
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            order_type = data.get('order_type')  # 'custom' or 'dress'
            new_status = data.get('new_status')
            
            if not all([order_id, order_type, new_status]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            # Validate status choices against your model
            valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'canceled']
            if new_status not in valid_statuses:
                return JsonResponse({'success': False, 'error': 'Invalid status'})
            
            # Update order based on type
            if order_type == 'custom':
                order = TOrders.objects.get(id=order_id, tailor__user=request.user)
            else:  # dress order (pre-designed)
                order = Order.objects.get(id=order_id, tailor__user=request.user)
            
            # Simply update the status field
            order.status = new_status
            order.save()
            
            return JsonResponse({'success': True, 'message': 'Status updated successfully'})
            
        except (TOrders.DoesNotExist, Order.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Order not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



@login_required
@csrf_exempt
def update_timeline_date(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            order_type = data.get('order_type')  # 'custom' or 'dress'
            timeline_field = data.get('timeline_field')  # e.g., 'measurements_confirmed'
            
            if not all([order_id, order_type, timeline_field]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            # Validate timeline field
            valid_custom_fields = ['measurements_confirmed', 'fabric_selected', 'cutting_started', 'stitching_started', 'deliver']
            valid_dress_fields = ['order_confirmed', 'production', 'quality_check', 'deliver']
            
            if order_type == 'custom':
                if timeline_field not in valid_custom_fields:
                    return JsonResponse({'success': False, 'error': 'Invalid timeline field for custom order'})
                order = TOrders.objects.get(id=order_id, tailor__user=request.user)
            else:  # dress order (pre-designed)
                if timeline_field not in valid_dress_fields:
                    return JsonResponse({'success': False, 'error': 'Invalid timeline field for pre-designed order'})
                order = Order.objects.get(id=order_id, tailor__user=request.user)
            
            # Update the timeline field with today's date - FIXED IMPORT
            today = timezone.now().date()
            setattr(order, timeline_field, today)
            order.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'{timeline_field.replace("_", " ").title()} updated successfully',
                'date': today.isoformat()
            })
            
        except (TOrders.DoesNotExist, Order.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Order not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
    

@login_required
@csrf_exempt
def tailor_update_measurements(request):
    if request.method == 'POST':
        try:
            tailor = Tailor.objects.get(user=request.user)
            
            # Update measurements from form data
            tailor.Chest = request.POST.get('chest', '')
            tailor.waist = request.POST.get('waist', '')
            tailor.hip = request.POST.get('hip', '')
            tailor.shoulder = request.POST.get('shoulder', '')
            tailor.sleeve = request.POST.get('sleeve', '')
            tailor.length = request.POST.get('length', '')
            tailor.inseam = request.POST.get('inseam', '')
            tailor.neck = request.POST.get('neck', '')
            
            tailor.save()
            
            return JsonResponse({
                'success': True,
                'chest': tailor.Chest,
                'waist': tailor.waist,
                'hip': tailor.hip,
                'shoulder': tailor.shoulder,
                'sleeve': tailor.sleeve,
                'length': tailor.length,
                'inseam': tailor.inseam,
                'neck': tailor.neck,
            })
            
        except Tailor.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tailor profile not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def tailor_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # This should be the email
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has a tailor profile
            if hasattr(user, 'tailor'):
                auth_login(request, user)
                
                # Set session expiry based on remember me
                if remember_me:
                    # Session will expire after 2 weeks (remember me checked)
                    request.session.set_expiry(1209600)  # 2 weeks in seconds
                else:
                    # Session will expire when browser is closed (remember me not checked)
                    request.session.set_expiry(0)
                
                messages.success(request, "You have successfully logged in as a tailor!")
                return redirect('tailor_dashboard')
            else:
                messages.error(request, "This account is not registered as a tailor!")
                return redirect('user_login')
        else:
            messages.error(request, "Invalid email or password!")
            return redirect('user_login')
    
    return render(request, 'user_login.html')

def tailor_details(request):
    return render(request, 'tailor_details.html')

def updatetailor(request):
    return render(request, 'updatetailor.html')

def deletetailor(request):
    if request.method == 'POST':
        tailor = request.user.tailor
        tailor.delete()
        messages.success(request, "Your tailor account has been deleted successfully.")
        return redirect('home')
    return render(request, 'deletetailor.html')





#-----------------------------------------




@login_required
@require_POST
def createreviews(request):
    try:
        # Get form data
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment', '')
        product_id = request.POST.get('product_id')
        tailor_id = request.POST.get('tailor_id')

        # Validate required fields
        if not rating:
            return JsonResponse({'success': False, 'error': 'Rating is required'})

        # Get customer from logged in user
        customer = request.user.customer

        # Create review with basic info
        review = Reviews(
            customer=customer,
            rating=rating,
            comment=comment if comment else None
        )

        if product_id:
            product = get_object_or_404(PreDesigned, id=product_id)
            review.product = product
        elif tailor_id:
            tailor = get_object_or_404(Tailor, id=tailor_id)
            review.tailor = tailor
            review.product = None
        else:
            return JsonResponse({'success': False, 'error': 'Either product or tailor is required'})

        review.save()

        return redirect('pre_designed')

    except IntegrityError:
        return JsonResponse({'success': False, 'error': 'You have already reviewed this product'})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})

    

@login_required
@require_POST
def deletereviews(request):
    try:
        review_id = request.POST.get('review_id')
        
        if not review_id:
            return JsonResponse({'success': False, 'error': 'Review ID is required'})

        # Get review and check ownership
        review = get_object_or_404(Reviews, id=review_id)
        
        # Check if the current user is the owner of the review
        if review.customer.user != request.user:
            return JsonResponse({'success': False, 'error': 'You are not authorized to delete this review'})

        # Delete review
        review.delete()

        return JsonResponse({'success': True, 'message': 'Review deleted successfully'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred while deleting review'})

@login_required
@require_POST
def updatereviews(request):
    try:
        review_id = request.POST.get('review_id')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')

        if not review_id:
            return JsonResponse({'success': False, 'error': 'Review ID is required'})

        # Get review and check ownership
        review = get_object_or_404(Reviews, id=review_id)
        
        # Check if the current user is the owner of the review
        if review.customer.user != request.user:
            return JsonResponse({'success': False, 'error': 'You are not authorized to update this review'})

        # Update fields
        if rating:
            review.rating = int(rating)
        
        review.comment = comment if comment else None

        # Save changes
        review.save()

        return JsonResponse({'success': True, 'message': 'Review updated successfully'})

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred while updating review'})

#-----------------------------------------

@login_required
def addDress(request):
    if request.method == 'POST':
        try:
            # Debugging: Check if request is reaching here
            print("AddDress POST request received")
            print("POST data:", request.POST)
            print("FILES:", request.FILES)
            
            # Get the current tailor
            tailor = Tailor.objects.get(user=request.user)
            print("Tailor found:", tailor)
            
            # Create the PreDesigned object
            dress = PreDesigned.objects.create(
                tailor=tailor,
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                availability=int(request.POST.get('availability', 0)),
                price=Decimal(request.POST.get('price', 0.0)),
                category=request.POST.get('category', ''),
                fabric_type=request.POST.get('fabric_type', ''),
                thread_type=request.POST.get('thread_type', ''),
                color=request.POST.get('color', ''),
                gender=request.POST.get('gender', '')
            )
            
            # Handle estimated time
            estimated_time = request.POST.get('estimated_time')
            if estimated_time and estimated_time.isdigit():
                dress.estimated_time = timedelta(hours=int(estimated_time))
            
            dress.save()
            print("Dress object created:", dress.id)
            
            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            print("Images received:", len(images))
            
            for image in images:
                Image.objects.create(predesigned=dress, image=image)
                print("Image saved:", image.name)
            
            messages.success(request, "Dress added successfully!")
            return redirect('tailor_dashboard')
            
        except Exception as e:
            print("Error in addDress:", str(e))
            messages.error(request, f"Error adding dress: {str(e)}")
            return redirect('tailor_dashboard')  # Redirect back to dashboard
    
    # If GET request, this shouldn't happen from modal
    messages.error(request, "Invalid request method")
    return redirect('tailor_dashboard')

@login_required
def edit_dress(request, product_id):
    try:
        # Get the dress object and verify ownership
        dress = PreDesigned.objects.get(id=product_id, tailor__user=request.user)
        
        if request.method == 'POST':
            try:
                # Debugging: Check if request is reaching here
                print("EditDress POST request received")
                print("POST data:", request.POST)
                print("FILES:", request.FILES)
                
                # Update the dress fields
                dress.title = request.POST.get('title', dress.title)
                dress.description = request.POST.get('description', dress.description)
                dress.availability = int(request.POST.get('availability', dress.availability))
                dress.price = Decimal(request.POST.get('price', dress.price))
                dress.category = request.POST.get('category', dress.category)
                dress.fabric_type = request.POST.get('fabric_type', dress.fabric_type)
                dress.thread_type = request.POST.get('thread_type', dress.thread_type)
                dress.color = request.POST.get('color', dress.color)
                dress.gender = request.POST.get('gender', dress.gender)
                
                # Handle estimated time
                estimated_time = request.POST.get('estimated_time')
                if estimated_time and estimated_time.isdigit():
                    dress.estimated_time = timedelta(hours=int(estimated_time))
                
                dress.save()
                print("Dress object updated:", dress.id)
                
                # Handle new image uploads
                images = request.FILES.getlist('images')
                print("New images received:", len(images))
                
                if images:
                    # Option 1: Delete existing images and add new ones
                    # dress.images.all().delete()
                    
                    # Option 2: Add new images without deleting existing ones
                    for image in images:
                        Image.objects.create(predesigned=dress, image=image)
                        print("New image saved:", image.name)
                
                messages.success(request, "Dress updated successfully!")
                return redirect('tailor_dashboard')
                
            except Exception as e:
                print("Error in edit_dress:", str(e))
                messages.error(request, f"Error updating dress: {str(e)}")
                return redirect('tailor_dashboard')
        
        # If GET request, render edit form with existing data
        context = {
            'dress': dress,
            'categories': PreDesigned.CATEGORY_CHOICES,  # If you have choices defined
            'genders': PreDesigned.GENDER_CHOICES,      # If you have choices defined
        }
        return render(request, 'edit_dress.html', context)
        
    except PreDesigned.DoesNotExist:
        messages.error(request, "Dress not found or you don't have permission to edit it.")
        return redirect('tailor_dashboard')
    except Exception as e:
        print("Error in edit_dress:", str(e))
        messages.error(request, "An error occurred while accessing the dress.")
        return redirect('tailor_dashboard')
    
@login_required
def delete_dress(request, product_id):
    """Delete entire dress"""
    try:
        dress = PreDesigned.objects.get(id=product_id, tailor__user=request.user)
        dress.delete()
        messages.success(request, "Dress deleted successfully!")
    except PreDesigned.DoesNotExist:
        messages.error(request, "Dress not found.")
    
    return redirect('tailor_dashboard')    
    

@login_required
def get_dress_details(request, product_id):
    try:
        # Get the product
        product = PreDesigned.objects.get(id=product_id)
        
        # Check if the current user owns this product
        if product.tailor.user != request.user:
            return JsonResponse({'success': False, 'error': 'You do not have permission to view this product.'})
        
        # Get all images for this product
        images = [request.build_absolute_uri(image.image.url) for image in product.images.all()]
        
        # Prepare response data
        data = {
            'success': True,
            'product': {
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'price': str(product.price),
                'category': product.category,
                'availability': product.availability,
                'fabric_type': product.fabric_type,
                'thread_type': product.thread_type,
                'color': product.color,
                'estimated_time': str(product.estimated_time) if product.estimated_time else None,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat(),
            },
            'images': images
        }
        
        return JsonResponse(data)
        
    except PreDesigned.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    
#-----------------------------------------




def calculate_working_days(start_date, days):
    """Calculate working days (excluding weekends)"""
    current_date = start_date
    working_days_added = 0
    
    while working_days_added < days:
        current_date += timedelta(days=1)
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5:
            working_days_added += 1
    
    return current_date

@login_required
def create_custom_orders(request, tailor_id):
    if request.method == 'POST':
        try:
            # Get the customer and tailor
            customer = Customer.objects.get(user=request.user)
            tailor = Tailor.objects.get(id=tailor_id)
            
            # Get form data
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            address = request.POST.get('address')
            gender = request.POST.get('gender')
            garment_type = request.POST.get('garment_type')
            
            # Handle multiple occasions (checkboxes)
            occasion_list = request.POST.getlist('occasion')
            occasion = ', '.join(occasion_list) if occasion_list else ''
            
            # Measurements
            chest = request.POST.get('chest')
            waist = request.POST.get('waist')
            hips = request.POST.get('hips')
            sleeve_length = request.POST.get('sleeve_length')
            garment_length = request.POST.get('length')
            shoulder_width = request.POST.get('shoulder_width')
            neck_circumference = request.POST.get('neck')
            inseam_length = request.POST.get('inseam')

            # Design preferences
            design_inspiration = request.POST.get('design_inspiration')
            description = request.POST.get('description')
            special_request = request.POST.get('special_request', '')
            
            # Handle embroidery selection
            embroidery_total_price = Decimal(request.POST.get('embroidery_total_price', 0))
            selected_embroidery_ids = request.POST.get('selected_embroidery_ids', '')
            
            # Handle fabric selection - FIXED
            selected_fabric_id = request.POST.get('selected_fabric_id')
            fabric_length_needed = Decimal(request.POST.get('fabric_length_needed', 0))
            selected_fabric = None
            fabric_total_price = Decimal(0)
            
            if selected_fabric_id and selected_fabric_id != '':
                try:
                    selected_fabric = Fabric.objects.get(id=selected_fabric_id)
                    fabric_total_price = selected_fabric.price_per_meter * fabric_length_needed
                except Fabric.DoesNotExist:
                    fabric_total_price = Decimal(0)
                    selected_fabric = None
            
            # Calculate total price
            base_price = tailor.price if tailor.price else Decimal(0)
            total_price = base_price + embroidery_total_price + fabric_total_price
            
            # Calculate delivery date (21 working days from now)
            delivery_date = calculate_working_days(datetime.now().date(), 21)
            
            # Create the custom order - FIXED: Use correct field names
            custom_order = TOrders.objects.create(
                customer=customer,
                tailor=tailor,
                fabrics=selected_fabric,  # Link the selected fabric object
                meter=fabric_length_needed,  # Store the length needed
                
                # Contact information
                address=address,
                contact_number=phone,
                gender=gender,
                
                # Order details
                occasion=occasion,
                garment_type=garment_type,
                
                # Design preferences
                inspiration=design_inspiration,
                detailed_description=description,
                special_requests=special_request,
                delivery_date=delivery_date,
                price=total_price,  # Now includes embroidery and fabric prices
                
                # Measurements
                chest=chest,
                waist=waist,
                hip=hips,
                shoulder=shoulder_width,
                sleeve=sleeve_length,
                neck=neck_circumference,
                length=garment_length,
                inseam=inseam_length,
                
                # Set initial status
                status='pending',
            )
            
            # Handle multiple embroidery designs - FIXED
            if selected_embroidery_ids:
                embroidery_id_list = [int(id) for id in selected_embroidery_ids.split(',') if id.strip()]
                if embroidery_id_list:
                    # For single embroidery, link directly
                    if len(embroidery_id_list) == 1:
                        try:
                            embroidery = Embroidery.objects.get(id=embroidery_id_list[0])
                            custom_order.embroidery = embroidery
                            custom_order.save()
                        except Embroidery.DoesNotExist:
                            pass
                    # For multiple embroideries, store as JSON
                    else:
                        selected_embroideries = Embroidery.objects.filter(id__in=embroidery_id_list)
                        # Store as JSON string in a text field (you might need to add this field to TOrders)
                        embroidery_info = [
                            {'id': emb.id, 'title': emb.title, 'price': str(emb.price)}
                            for emb in selected_embroideries
                        ]
                        # If you have a field for storing multiple embroidery info
                        if hasattr(custom_order, 'selected_embroidery_info'):
                            custom_order.selected_embroidery_info = json.dumps(embroidery_info)
                            custom_order.embroidery_total_price = embroidery_total_price
                            custom_order.save()
            
            messages.success(request, f"Custom order placed successfully! Your order ID is TORD-{custom_order.id:03d}. Total price: ৳{total_price}")
            return redirect('findTailor')
            
        except Customer.DoesNotExist:
            messages.error(request, "Customer profile not found.")
            return redirect('findTailor')
        except Tailor.DoesNotExist:
            messages.error(request, "Selected tailor does not exist.")
            return redirect('findTailor')
        except Exception as e:
            messages.error(request, f"Error creating custom order: {str(e)}")
            return redirect('findTailor')
    
    # If GET request, redirect back to findTailor page
    return redirect('findTailor')
        
        
        
        
def delete_custom_orders(request):
    return render(request, 'delete_custom_orders.html')

def update_custom_orders(request):
    return render(request, 'update_custom_orders.html')



#-----------------------------------------

@login_required
def addEmbroidery(request):
    if request.method == 'POST':
        try:
            # Get the current tailor
            tailor = Tailor.objects.get(user=request.user)
            
            # Create the Embroidery object
            embroidery = Embroidery.objects.create(
                tailor=tailor,
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                price=request.POST.get('price', 0.0),
                fabric_type=request.POST.get('fabric_type', ''),
                thread_type=request.POST.get('thread_type', ''),
                color=request.POST.get('color', ''),
                complexity_level=request.POST.get('complexity_level', 'simple'),
            )
            
            # Handle estimated time (convert hours to timedelta)
            estimated_time_hours = request.POST.get('estimated_time')
            if estimated_time_hours:
                embroidery.estimated_time = timedelta(hours=int(estimated_time_hours))
            
            # Handle image upload
            design_image = request.FILES.get('design_image')
            if design_image:
                embroidery.design_image = design_image
            
            embroidery.save()
            
            messages.success(request, "Embroidery design added successfully!")
            return redirect('tailor_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error adding embroidery design: {str(e)}")
            return redirect('addEmbroidery')
    
    # If GET request, show the form
    return render(request, 'addEmbroidery.html')  

@login_required
def edit_embroidery(request, embroidery_id):
    try:
        # Get the embroidery object and verify ownership
        embroidery = Embroidery.objects.get(id=embroidery_id, tailor__user=request.user)
        
        if request.method == 'POST':
            try:
                # Update the embroidery object with new data
                embroidery.title = request.POST.get('title', embroidery.title)
                embroidery.description = request.POST.get('description', embroidery.description)
                embroidery.price = request.POST.get('price', embroidery.price)
                embroidery.fabric_type = request.POST.get('fabric_type', embroidery.fabric_type)
                embroidery.thread_type = request.POST.get('thread_type', embroidery.thread_type)
                embroidery.color = request.POST.get('color', embroidery.color)
                embroidery.complexity_level = request.POST.get('complexity_level', embroidery.complexity_level)
                
                # Handle estimated time update
                estimated_time_hours = request.POST.get('estimated_time')
                if estimated_time_hours:
                    embroidery.estimated_time = timedelta(hours=int(estimated_time_hours))
                
                # Handle image update
                design_image = request.FILES.get('design_image')
                if design_image:
                    embroidery.design_image = design_image
                
                embroidery.save()
                
                messages.success(request, "Embroidery design updated successfully!")
                return redirect('tailor_dashboard')
                
            except Exception as e:
                messages.error(request, f"Error updating embroidery design: {str(e)}")
                return redirect('edit_embroidery', embroidery_id=embroidery_id)
        
        # If GET request, show the form with existing data
        context = {
            'embroidery': embroidery
        }
        return render(request, 'edit_embroidery.html', context)
        
    except Embroidery.DoesNotExist:
        messages.error(request, "Embroidery design not found or you don't have permission to edit it.")
        return redirect('tailor_dashboard')

@login_required
def delete_embroidery(request, embroidery_id):
    try:
        # Get the embroidery object and verify ownership
        embroidery = Embroidery.objects.get(id=embroidery_id, tailor__user=request.user)
        
        if request.method == 'POST':
            embroidery.delete()
            messages.success(request, "Embroidery design deleted successfully!")
            return redirect('tailor_dashboard')
        
        # If GET request, show confirmation page
        context = {
            'embroidery': embroidery
        }
        return render(request, 'confirm_delete_embroidery.html', context)
        
    except Embroidery.DoesNotExist:
        messages.error(request, "Embroidery design not found or you don't have permission to delete it.")
        return redirect('tailor_dashboard')    
    

@login_required
def get_embroidery_details(request, embroidery_id):
    try:
        embroidery = Embroidery.objects.get(id=embroidery_id, tailor__user=request.user)
        
        data = {
            'success': True,
            'embroidery': {
                'id': embroidery.id,
                'title': embroidery.title,
                'description': embroidery.description,
                'price': float(embroidery.price),
                'fabric_type': embroidery.fabric_type,
                'thread_type': embroidery.thread_type,
                'color': embroidery.color,
                'complexity_level': embroidery.complexity_level,
                'estimated_time': embroidery.estimated_time.total_seconds() if embroidery.estimated_time else None,
                'design_image': embroidery.design_image.url if embroidery.design_image else None,
                'created_at': embroidery.created_at.isoformat(),
                'updated_at': embroidery.updated_at.isoformat(),
            }
        }
        return JsonResponse(data)
        
    except Embroidery.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Embroidery design not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    
    
@require_POST
@login_required
def toggle_favorite(request, tailor_id):
    try:
        tailor = Tailor.objects.get(id=tailor_id)
        customer = request.user.customer
        
        # Check if already favorited
        try:
            favorite = FavoriteTailor.objects.get(user=customer, tailor=tailor)
            # If it exists, remove it (toggle off)
            favorite.delete()
            return JsonResponse({'status': 'removed', 'tailor_id': tailor_id})
        except FavoriteTailor.DoesNotExist:
            # If it doesn't exist, create it (toggle on)
            FavoriteTailor.objects.create(user=customer, tailor=tailor)
            return JsonResponse({'status': 'added', 'tailor_id': tailor_id})
            
    except Tailor.DoesNotExist:
        return JsonResponse({'error': 'Tailor not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def favorite_tailors(request):
    if not request.user.is_authenticated:
        # Redirect to login or show empty state
        return render(request, 'favorites.html', {'favorites': []})
    
    favorites = FavoriteTailor.objects.filter(user=request.user.customer).select_related('tailor')
    return render(request, 'favorites.html', {'favorites': favorites})    

# Fabric ট্যাবের জন্য ভিউ
def fabric_tab(request):
    # আপনার existing context এর সাথে fabrics যোগ করুন
    context = {
        # ... আপনার existing context
        'fabrics': Fabric.objects.filter(tailor=request.user.tailor) if hasattr(request.user, 'tailor') else []
    }
    return render(request, 'tailor.html', context)

# Fabric ডিটেইলস AJAX ভিউ
def get_fabric_details(request, fabric_id):
    try:
        fabric = get_object_or_404(Fabric, id=fabric_id)
        
        # Check if the fabric belongs to the current tailor
        if hasattr(request.user, 'tailor') and fabric.tailor != request.user.tailor:
            return JsonResponse({'success': False, 'error': 'Access denied'})
        
        fabric_data = {
            'id': fabric.id,
            'name': fabric.name,
            'description': fabric.description,
            'fabric_type': fabric.fabric_type,
            'color': fabric.color,
            'pattern': fabric.pattern,
            'texture': fabric.texture,
            'width': str(fabric.width),
            'length_available': str(fabric.length_available),
            'price_per_meter': str(fabric.price_per_meter),
            'image': fabric.image.url if fabric.image else None,
            'is_available': fabric.is_available,
            'created_at': fabric.created_at.isoformat(),
            'updated_at': fabric.updated_at.isoformat(),
        }
        
        return JsonResponse({'success': True, 'fabric': fabric_data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Add Fabric ভিউ
@csrf_exempt
@require_http_methods(["POST"])
def add_fabric(request):
    try:
        if not hasattr(request.user, 'tailor'):
            return JsonResponse({'success': False, 'error': 'Tailor profile not found'})
        
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        fabric_type = request.POST.get('fabric_type', 'cotton')
        color = request.POST.get('color', '')
        pattern = request.POST.get('pattern', 'plain')
        texture = request.POST.get('texture', '')
        width = request.POST.get('width', 0)
        length_available = request.POST.get('length_available', 0)
        price_per_meter = request.POST.get('price_per_meter', 0)
        
        # Create fabric object
        fabric = Fabric(
            tailor=request.user.tailor,
            name=name,
            description=description,
            fabric_type=fabric_type,
            color=color,
            pattern=pattern,
            texture=texture,
            width=width,
            length_available=length_available,
            price_per_meter=price_per_meter,
        )
        
        # Handle image upload
        if 'image' in request.FILES:
            fabric.image = request.FILES['image']
        
        fabric.save()
        
        # ✅ এই লাইনটি যোগ করুন - সফল রেস্পন্স
        messages.success(request, 'Fabric added successfully!')
        return redirect('tailor_dashboard')  # একই পেজে রিডাইরেক্ট
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

# Edit Fabric ভিউ
@csrf_exempt
@require_http_methods(["POST"])
def edit_fabric(request, fabric_id):
    try:
        if not hasattr(request.user, 'tailor'):
            return JsonResponse({'success': False, 'error': 'Tailor profile not found'})
        
        # ফ্যাব্রিকটি exists কিনা এবং ইউজারের属于自己的 কিনা চেক করুন
        try:
            fabric = Fabric.objects.get(id=fabric_id, tailor=request.user.tailor)
        except Fabric.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Fabric not found'})
        
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        fabric_type = request.POST.get('fabric_type', 'cotton')
        color = request.POST.get('color', '')
        pattern = request.POST.get('pattern', 'plain')
        texture = request.POST.get('texture', '')
        width = request.POST.get('width', 0)
        length_available = request.POST.get('length_available', 0)
        price_per_meter = request.POST.get('price_per_meter', 0)
        
        # Update fabric object
        fabric.name = name
        fabric.description = description
        fabric.fabric_type = fabric_type
        fabric.color = color
        fabric.pattern = pattern
        fabric.texture = texture
        fabric.width = width
        fabric.length_available = length_available
        fabric.price_per_meter = price_per_meter
        
        # Handle image upload
        if 'image' in request.FILES:
            fabric.image = request.FILES['image']
        
        fabric.save()
        
        messages.success(request, 'Fabric updated successfully!')
        return redirect('tailor_dashboard')
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

# Delete Fabric ভিউ
@csrf_exempt
@require_http_methods(["POST"])
def delete_fabric(request, fabric_id):
    try:
        if not hasattr(request.user, 'tailor'):
            return JsonResponse({'success': False, 'error': 'Tailor profile not found'})
        
        # ফ্যাব্রিকটি exists কিনা এবং ইউজারের属于自己的 কিনা চেক করুন
        try:
            fabric = Fabric.objects.get(id=fabric_id, tailor=request.user.tailor)
        except Fabric.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Fabric not found'})
        
        # ফ্যাব্রিক ডিলিট করুন
        fabric.delete()
        
        messages.success(request, 'Fabric deleted successfully!')
        return redirect('tailor_dashboard')
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    
    
    
def get_order_details(request, order_id):
    try:
        # Extract the numeric ID and type from order_id
        if order_id.startswith('TORD-'):
            numeric_id = order_id.replace('TORD-', '')
            order = TOrders.objects.get(id=numeric_id)
            order_type = "Custom Order"
        elif order_id.startswith('DORD-'):
            numeric_id = order_id.replace('DORD-', '')
            order = Order.objects.get(id=numeric_id)
            order_type = "Pre-designed"
        else:
            return JsonResponse({'success': False, 'error': 'Invalid order ID format'})
        
        # Prepare order data
        order_data = {
            'order_id': order_id,
            'status': getattr(order, 'status', 'Pending'),
            'garment': getattr(order, 'detailed_description', 'Custom Garment'),
            'category': getattr(order, 'category', 'Custom'),
            'date': getattr(order, 'order_date', None),
            'amount': str(getattr(order, 'price', 0)),
            'delivery_date': getattr(order, 'delivery_date', None),
            'order_type': order_type,
            # Add other fields as needed...
        }
        
        return JsonResponse({'success': True, 'order': order_data})
        
    except (TOrders.DoesNotExist, Order.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Order not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})    