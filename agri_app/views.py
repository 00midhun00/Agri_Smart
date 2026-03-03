from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404

from .forms import AgriRegistrationForm


def home(request):
    return render(request, 'agri_app/home.html')

def register_view(request):
    if request.method == 'POST':
        form = AgriRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = AgriRegistrationForm()
    return render(request, 'agri_app/register.html', {'form': form})


from .models import Notification, NewsUpdate  # Make sure these are imported at the top!


@login_required
def dashboard_redirect(request):
    # Logic to send users to the right place
    if request.user.is_staff or request.user.role == 'Admin':
        return redirect('/admin/')

    elif request.user.role == 'Farmer':
        # 1. Grab the News
        latest_news = NewsUpdate.objects.all().order_by('-created_at')

        # 2. Count the unread notifications for this exact farmer!
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        # 3. Pack them up in the context dictionary
        context = {
            'news': latest_news,
            'unread_count': unread_count,
        }

        # 4. Send the context to the dashboard template
        return render(request, 'agri_app/farmer_dashboard.html', context)

    elif request.user.role == 'Buyer':
        return render(request, 'agri_app/buyer_dashboard.html')

    return redirect('home')

@login_required
def ai_prediction_view(request):
    return render(request, 'agri_app/ai_prediction.html')

@login_required
def rental_view(request):
    return render(request, 'agri_app/rental_list.html')

@login_required
def sell_product_view(request):
    return render(request, 'agri_app/sell_product.html')


from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from .utils import predict_with_cnn, predict_with_gemini
from .models import AIConsultation


@login_required
def ai_prediction_view(request):
    if request.method == 'POST' and request.FILES.get('crop_image'):
        image = request.FILES['crop_image']
        ai_type = request.POST.get('ai_type', 'cnn')

        # 1. Save image temporarily
        fs = FileSystemStorage()
        filename = fs.save(f"uploads/{image.name}", image)
        image_path = fs.path(filename)
        image_url = fs.url(filename)

        # 2. Call the selected AI
        if ai_type == 'gemini':
            prediction_result = predict_with_gemini(image_path)
        else:
            prediction_result = predict_with_cnn(image_path)

        # 3. Process the results
        if prediction_result.get('status') == 'success':
            disease_name = prediction_result['disease']

            # --- EXTRACT PLANT NAMES ---
            if ai_type == 'gemini':
                # Gemini gives us the exact names via the JSON we built
                plant_name = prediction_result.get('plant_name', 'Unknown Plant')
                biological_name = prediction_result.get('biological_name', 'Unknown')
            else:
                # The CNN returns a combined string like "Tomato - Early Blight".
                # This splits it into the Plant Name and Disease Name!
                if ' - ' in disease_name:
                    parts = disease_name.split(' - ', 1)
                    plant_name = parts[0]
                    disease_name = parts[1]
                else:
                    plant_name = "Unknown Plant"
                biological_name = "Scan with Gemini AI for detailed biological data"
            # ---------------------------

            confidence = prediction_result['confidence']
            cures = prediction_result['cures']
            error_message = None

            # Save to history
            AIConsultation.objects.create(
                farmer=request.user,
                image=filename,
                prediction_type=ai_type,
                disease_name=disease_name,
                recommendation=f"NATURAL: {cures['natural']} | CHEMICAL: {cures['chemical']}"
            )
        else:
            plant_name = "N/A"
            biological_name = "N/A"
            disease_name = "Analysis Failed"
            confidence = None
            cures = None
            error_message = prediction_result.get('message', 'An error occurred.')

        # 4. Send ALL the variables to the UI (This is what was missing!)
        context = {
            'plant_name': plant_name,  # <--- Now passing Plant Name
            'biological_name': biological_name,  # <--- Now passing Biological Name
            'disease': disease_name,
            'confidence': confidence,
            'cures': cures,
            'image_url': image_url,
            'error': error_message
        }

        return render(request, 'agri_app/ai_results.html', context)

    return render(request, 'agri_app/ai_prediction.html')

from django.shortcuts import render

from .models import NewsUpdate  # Ensure this import is at the top

from django.shortcuts import render
from .models import NewsUpdate, Notification


@login_required
def farmer_dashboard(request):
    # 1. Get the data from the database for the News
    latest_news = NewsUpdate.objects.all().order_by('-created_at')

    # 2. Count unread notifications for this specific farmer
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    print(f"DEBUG - Logged in as: {request.user.email} (Username: {request.user.username})")
    print(f"DEBUG - Unread count for this user: {unread_count}")
    # 3. Put BOTH pieces of data in the 'context' dictionary
    context = {
        'news': latest_news,
        'unread_count': unread_count,
        'user': request.user
        # (Note: request.user is automatically available in templates, but keeping it here is fine!)
    }

    # 4. Send it to the template
    return render(request, 'agri_app/farmer_dashboard.html', context)


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import NewsUpdate, Notification



@login_required
def post_news_view(request):
    if request.method == 'POST':
        # Added request.FILES to capture the image!
        form = NewsUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            messages.success(request, "News broadcasted successfully!")
            return redirect('dashboard')
    else:
        form = NewsUpdateForm()
    return render(request, 'agri_app/post_news.html', {'form': form})


@login_required
def edit_news_view(request, news_id):
    news_item = get_object_or_404(NewsUpdate, id=news_id)

    # Security: Only the exact author can edit this post
    if request.user != news_item.author:
        messages.error(request, "You cannot edit someone else's news.")
        return redirect('dashboard')

    if request.method == 'POST':
        # Don't forget request.FILES here too, in case they change the image!
        form = NewsUpdateForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            form.save()
            messages.success(request, "News updated successfully!")
            return redirect('dashboard')
    else:
        form = NewsUpdateForm(instance=news_item)

    # We can reuse the post_news.html template for editing!
    return render(request, 'agri_app/post_news.html', {'form': form})


@login_required
def delete_news_view(request, news_id):
    news_item = get_object_or_404(NewsUpdate, id=news_id)

    # Security: Only the exact author can delete this post
    if request.user == news_item.author:
        news_item.delete()
        messages.success(request, "News deleted successfully.")

    return redirect('dashboard')
@login_required
def checkout_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    requested_qty = int(request.GET.get('qty', 1))

    if requested_qty > product.remaining_stock:
        messages.error(request, "Not enough stock available!")
        return redirect('market_list')

    total_price = product.price_per_unit * requested_qty

    context = {
        'product': product,
        'qty': requested_qty,
        'total_price': total_price
    }
    return render(request, 'agri_app/checkout.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProductForm


@login_required
def sell_product_view(request):
    if request.method == 'POST':
        # request.FILES is required to grab the uploaded image!
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            # commit=False pauses the save so we can add the farmer ID
            product = form.save(commit=False)
            product.farmer = request.user
            product.save()  # THIS saves it to the table

            messages.success(request, "Crop successfully listed on the market!")
            return redirect('dashboard')  # Redirects to dashboard after saving
        else:
            # If it fails, print the exact error to the terminal
            print("FORM FAILED VALIDATION:", form.errors)
    else:
        # If it's a GET request (just visiting the page), show an empty form
        form = ProductForm()

    # The dictionary {'form': form} is what makes the fields appear in HTML
    return render(request, 'agri_app/sell_product.html', {'form': form})


from django.shortcuts import get_object_or_404
from .models import Product, Review


@login_required
def market_list_view(request):
    # Fetch all available products, newest first
    products = Product.objects.filter(is_available=True).order_by('-created_at')
    return render(request, 'agri_app/market_list.html', {'products': products})


@login_required
def add_review_view(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '')

        # Save the new review
        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )
        messages.success(request, "Your review has been added!")
    return redirect('market_list')


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Product, Notification


@login_required
def buy_product_view(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        qty_requested = int(request.POST.get('qty', 1))

        if qty_requested <= product.quantity_available:
            # 1. Reduce the stock
            product.quantity_available -= qty_requested
            product.save()

            # 2. Grab the Buyer's contact info safely
            # (If the user hasn't filled it out, it defaults to "Not provided")
            buyer_phone = getattr(request.user, 'phone_number', '') or "Not provided"
            buyer_address = getattr(request.user, 'address', '') or "Not provided"

            # 3. Notify the Farmer with the buyer's contact details!
            Notification.objects.create(
                user=product.farmer,
                message=f"New Order! {request.user.full_name} bought {qty_requested} unit(s) of {product.crop_name}. Phone: {buyer_phone} | Address: {buyer_address}"
            )

            messages.success(request,
                             f"You successfully purchased {qty_requested} {product.crop_name}! The farmer has been notified with your contact details.")
            messages.success(request,
                             "Success! Your order has been placed. The farmer has received your details and will contact you soon!")
        else:
            messages.error(request, "Sorry, not enough stock available.")

    return redirect('market_list')

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product


@login_required
def delete_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # SECURITY CHECK: Make sure the logged-in user is the owner
    if request.user == product.farmer:
        product_name = product.crop_name
        product.delete()  # This removes it from the database
        messages.success(request, f"Your listing for '{product_name}' has been successfully deleted.")
    else:
        messages.error(request, "Security Alert: You are not authorized to delete this product.")

    # Redirect back to the marketplace after deleting
    return redirect('market_list')

from .models import Equipment

@login_required
def rental_view(request):
    # Fetch all equipment to display in the grid
    equipments = Equipment.objects.all().order_by('-created_at')
    return render(request, 'agri_app/rental_list.html', {'equipments': equipments})

@login_required
def toggle_equipment_status(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)
    # Security: Only the owner can change the status
    if request.user == equipment.owner:
        equipment.is_available = not equipment.is_available # Flips True to False, or False to True
        equipment.save()
        messages.success(request, f"Status updated for {equipment.name}.")
    return redirect('rental_list')

@login_required
def delete_equipment(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)
    # Security: Only the owner can delete
    if request.user == equipment.owner:
        equipment.delete()
        messages.success(request, "Equipment listing deleted.")
    return redirect('rental_list')


from .forms import EquipmentForm

from .models import EquipmentReview, Notification  # Ensure Notification is imported

from .forms import EquipmentForm  # Make sure this is imported at the top!


@login_required
def add_equipment_view(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.owner = request.user
            equipment.save()
            messages.success(request, "Your equipment has been listed for rent!")
            return redirect('rental_list')
    else:
        form = EquipmentForm()

    return render(request, 'agri_app/add_equipment.html', {'form': form})


@login_required
def add_equipment_review_view(request, equipment_id):
    if request.method == 'POST':
        equipment = get_object_or_404(Equipment, id=equipment_id)
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '')

        # Save the new equipment review
        EquipmentReview.objects.create(
            equipment=equipment,
            user=request.user,
            rating=rating,
            comment=comment
        )
        messages.success(request, "Your equipment review has been posted!")
    return redirect('rental_list')

# --- PASTE THIS AT THE BOTTOM OF VIEWS.PY ---

@login_required
def rent_equipment_view(request, equipment_id):
    if request.method == 'POST':
        equipment = get_object_or_404(Equipment, id=equipment_id)

        if equipment.is_available:
            # 1. Mark the equipment as occupied (rented out)
            equipment.is_available = False
            equipment.save()

            # 2. Grab the Renter's contact info safely
            # If the user hasn't filled it out, it defaults to "Not provided"
            renter_phone = getattr(request.user, 'phone_number', '') or "Not provided"
            renter_address = getattr(request.user, 'address', '') or "Not provided"

            # 3. Notify the Owner with the buyer's contact details!
            Notification.objects.create(
                user=equipment.owner,
                message=f"Rental Request! {request.user.full_name} wants to rent your {equipment.name}. Phone: {renter_phone} | Address: {renter_address}"
            )

            messages.success(request, f"You successfully rented the {equipment.name}! The owner has been notified.")
            messages.success(request,
                             "Success! You have booked this equipment. The owner will contact you soon at your provided phone number.")
        else:
            messages.error(request, "Sorry, this equipment was just rented by someone else.")

    return redirect('rental_list')


from .models import Notification


@login_required
def notifications_view(request):
    # Fetch all notifications for the logged-in user, newest first
    alerts = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Mark them all as read once the user opens this page
    alerts.update(is_read=True)

    return render(request, 'agri_app/notifications.html', {'alerts': alerts})

@login_required
def buyer_dashboard(request):
    return render(request, 'agri_app/buyer_dashboard.html')


from .models import NewsUpdate


@login_required
def news_list_view(request):
    # This grabs all news to display on the dedicated news page
    news_items = NewsUpdate.objects.all().order_by('-created_at')
    return render(request, 'agri_app/news_list.html', {'news_items': news_items})

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import NewsUpdate
from .forms import NewsUpdateForm

# 1. THE NEW SHARED FEED
@login_required
def news_list_view(request):
    latest_news = NewsUpdate.objects.all().order_by('-created_at')
    return render(request, 'agri_app/news_list.html', {'news': latest_news})

# 2. POST NEWS (Redirects to the feed now)
@login_required
def post_news_view(request):
    if request.method == 'POST':
        form = NewsUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            messages.success(request, "News broadcasted successfully!")
            return redirect('news_list') # Changed this!
    else:
        form = NewsUpdateForm()
    return render(request, 'agri_app/post_news.html', {'form': form})

# 3. EDIT NEWS (Redirects to the feed now)
@login_required
def edit_news_view(request, news_id):
    news_item = get_object_or_404(NewsUpdate, id=news_id)
    if request.user != news_item.author:
        return redirect('news_list')

    if request.method == 'POST':
        form = NewsUpdateForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            form.save()
            return redirect('news_list') # Changed this!
    else:
        form = NewsUpdateForm(instance=news_item)
    return render(request, 'agri_app/post_news.html', {'form': form})

# 4. DELETE NEWS (Redirects to the feed now)
@login_required
def delete_news_view(request, news_id):
    news_item = get_object_or_404(NewsUpdate, id=news_id)
    if request.user == news_item.author:
        news_item.delete()
    return redirect('news_list') # Changed this!