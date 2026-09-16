from django.shortcuts import render,get_object_or_404,redirect
from .models import Product, Category,Wishlist,Review,Coupon,ProductVariant,CategoryOffer
from order.models import Order, OrderItem
from .cart import Cart
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import razorpay
import json
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.cache import never_cache
from django.db.models import Q
from .forms import ReviewForm
from django.db.models import Avg
from django.contrib import messages
from django.db.models import Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from .forms import ContactForm, CouponForm
from django.urls import reverse
from django.db import transaction
from decimal import Decimal

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont





# Create your views here.


CATALOG_CACHE_TIMEOUT = 300


def _catalog_cache_key(name):
    version = cache.get_or_set(
        "store:catalog-version",
        "initial",
        timeout=None
    )
    return f"store:catalog:{version}:{name}"


def home(request):
    query = request.GET.get("q")
    offers = [
        offer for offer in CategoryOffer.objects.select_related("category")
        if offer.is_active()
    ]

    if query:

        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query)
        ).filter(
            available=True
        ).prefetch_related(
            "variants"
        ).order_by("-id")

        categories = Category.objects.order_by("?")

    else:

        catalog = cache.get_or_set(
            _catalog_cache_key("home"),
            lambda: {
                "products": list(
                    Product.objects.filter(
                        available=True
                    ).prefetch_related(
                        "variants"
                    )
                ),

                "categories": list(
                    Category.objects.all()
                ),
            },
            CATALOG_CACHE_TIMEOUT,
        )

        import random

        products = catalog["products"].copy()
        random.shuffle(products)

        categories = catalog["categories"].copy()
        random.shuffle(categories)

    context = {
        "products": products,
        "categories": categories,
        "query": query,
        "category_offers": offers,
    }

    return render(request, "home.html", context)

def product_detail(request, slug):

        # GET PRODUCT
    

    if slug.isdigit():

        product = get_object_or_404(
            Product,
            id=int(slug)
        )

    else:

        product_name = slug.replace("-", " ")

        product = get_object_or_404(
            Product,
            name__iexact=product_name
        )


    
    # RELATED PRODUCTS
    

    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(
        id=product.id
    )[:4]


    
    # REVIEWS
    

    reviews = product.reviews.all().order_by("-created_at")

    average_rating = reviews.aggregate(
        Avg("rating")
    )["rating__avg"]

    review_count = reviews.count()


    
    # REVIEW FORM
    

    form = ReviewForm()


    if request.method == "POST":

        # Only logged-in users can submit reviews
        if not request.user.is_authenticated:
            return redirect("login")


        existing_review = Review.objects.filter(
            product=product,
            user=request.user
        ).first()


        # Prevent multiple reviews
        if existing_review:

            messages.info(
                request,
                "You have already reviewed this perfume."
            )

            return redirect(
                "product_detail",
                slug=product.name.replace(" ", "-")
            )


        form = ReviewForm(request.POST)


        if form.is_valid():

            review = form.save(commit=False)

            review.product = product
            review.user = request.user

            review.save()


            messages.success(
                request,
                "Your review was added successfully."
            )


            return redirect(
                "product_detail",
                slug=product.name.replace(" ", "-")
            )


    context = {

        "product": product,

        "reviews": reviews,

        "form": form,

        "average_rating": average_rating,

        "review_count": review_count,

        "related_products": related_products,

    }


    return render(
        request,
        "product_detail.html",
        context
    )

@never_cache
@login_required(login_url="login")
def cart_detail(request):


    cart = Cart(request)
    context = {"cart": cart}

    return render(request,"cart.html",context)



@login_required(login_url="login")
def cart_increase(request, id, variant_id):

    cart = Cart(request)

    product = get_object_or_404(Product, id=id)

    variant = get_object_or_404(
        product.variants,
        id=variant_id
    )

    if not cart.increase(
        product=product,
        variant=variant
    ):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": False,
                "message": f"{product.name} has reached its stock limit for {variant.size or 'this size'}.",
            }, status=400)

        messages.error(
            request,
            f"{product.name} has reached its stock limit for {variant.size or 'this size'}."
        )
        return redirect("cart_detail")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        item = next(
            item for item in cart if item["product"].id == id and item["variant"].id == variant_id
        )
        return JsonResponse({
            "success": True,
            "quantity": item["quantity"],
            "subtotal": str(item["subtotal"]),
            "cart_total": str(cart.get_total_price()),
            "cart_count": len(cart),
        })

    return redirect("cart_detail")


@login_required(login_url="login")
def cart_decrease(request, id, variant_id):

    cart = Cart(request)

    product = get_object_or_404(Product, id=id)

    variant = get_object_or_404(
        product.variants,
        id=variant_id
    )

    cart.decrease(
        product=product,
        variant=variant
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        item = next(
            (item for item in cart if item["product"].id == id and item["variant"].id == variant_id),
            None,
        )
        return JsonResponse({
            "success": True,
            "quantity": item["quantity"] if item else 0,
            "subtotal": str(item["subtotal"]) if item else "0",
            "cart_total": str(cart.get_total_price()),
            "cart_count": len(cart),
            "removed": item is None,
        })

    return redirect("cart_detail")


@login_required(login_url="login")
def cart_remove(request, id, variant_id):

    cart = Cart(request)

    product = get_object_or_404(Product, id=id)

    variant = get_object_or_404(
        product.variants,
        id=variant_id
    )

    cart.remove(
        product=product,
        variant=variant
    )

    return redirect("cart_detail")

@login_required(login_url="login")
def cart_clear(request):

    cart = Cart(request)
    cart.clear()

    return redirect("cart_detail")


@login_required(login_url="login")
@require_POST
def cart_add(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )

    variant_id = request.POST.get("variant_id")

    if not variant_id:
        variant = next(
            (
                candidate
                for candidate in product.variants.filter(
                    available=True
                ).order_by("-stock", "id")
                if "".join((candidate.size or "").split()).lower() == "50ml"
            ),
            None,
        )

        if not variant:
            return JsonResponse({
                "success": False,
                "message": "The 50 ml variant is currently unavailable."
            })

    else:
        # Make sure the variant belongs to this product.
        variant = get_object_or_404(
            product.variants,
            id=variant_id
        )


    if not variant.available:

        return JsonResponse({
            "success": False,
            "message": "This variant is currently unavailable."
        })


    cart = Cart(request)

    if not cart.add(
        product=product,
        variant=variant
    ):
        return JsonResponse({
            "success": False,
            "message": f"{product.name} has reached its stock limit for this variant."
        })

    return JsonResponse({

        "success": True,

        "message": f"{product.name} added to cart!",

        "cart_count": len(cart),

        "product_name": product.name

    })

@never_cache
@login_required(login_url="login")
def checkout(request):

    profile = request.user.profile
    cart = Cart(request)

    subtotal = cart.get_total_price()

    
    # COUPON DISCOUNT
    

    coupon_code = request.session.get("coupon_code")
    coupon_discount = Decimal(
        request.session.get("coupon_discount", "0")
    )

    # Safety check
    if coupon_discount > subtotal:
        coupon_discount = Decimal("0")

        request.session.pop("coupon_code", None)
        request.session.pop("coupon_discount", None)

        coupon_code = None

    final_total = subtotal - coupon_discount

    
    # AVAILABLE COUPONS / OFFERS
   

    now = timezone.now()

    available_coupons = Coupon.objects.filter(
        active=True,
        valid_from__lte=now,
        valid_to__gte=now
    ).order_by("-discount_percent")

    
    # RAZORPAY ORDER
   

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    payment = client.order.create({

        "amount": int(final_total * 100),

        "currency": "INR",

        "receipt": f"order_{request.user.id}_{timezone.now().timestamp()}"

    })

    context = {

        "profile": profile,

        "cart": cart,

        "razorpay_key": settings.RAZORPAY_KEY_ID,

        "razorpay_order_id": payment["id"],

        "amount": int(final_total * 100),

        "subtotal": subtotal,

        "coupon_discount": coupon_discount,

        "final_total": final_total,

        "coupon_code": coupon_code,

        "available_coupons": available_coupons,

    }

    return render(
        request,
        "checkout.html",
        context
    )



@login_required(login_url="login")
@require_POST
def payment_success(request):

    data = json.loads(request.body)

    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_signature = data.get("razorpay_signature")

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    try:

        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })

    except razorpay.errors.SignatureVerificationError:

        return JsonResponse({
            "success": False,
            "message": "Payment verification failed."
        }, status=400)

    cart = Cart(request)

    if not cart:

        return JsonResponse({
            "success": False,
            "message": "Your cart is empty."
        }, status=400)

    profile = request.user.profile

    subtotal = cart.get_total_price()

    coupon_discount = Decimal(
        request.session.get("coupon_discount", "0")
    )

    total = subtotal - coupon_discount

    if total < 0:
        total = Decimal("0")

    try:

        with transaction.atomic():

            order = Order.objects.create(

                user=request.user,

                phone=profile.phone,

                address=profile.address,

                city=profile.city,

                state=profile.state,

                country=profile.country,

                postal_code=profile.postal_code,

                total=total,

                razorpay_order_id=razorpay_order_id,

                razorpay_payment_id=razorpay_payment_id,

                status="Processing"
            )

            for item in cart:

                OrderItem.objects.create(

                    order=order,

                    product=item["product"],

                    price=item["product"].price,

                    quantity=item["quantity"]
                )

    except Exception as e:

        print("ORDER CREATION ERROR:", e)

        return JsonResponse({

            "success": False,

            "message": "Payment received, but order creation failed."

        }, status=500)

    cart.clear()

    request.session.pop("coupon_code", None)
    request.session.pop("coupon_discount", None)

    return JsonResponse({

        "success": True,

        "order_id": order.id,

        "order_number": order.order_number
    })



def order_success(request):

    cart = Cart(request)
    cart.clear()

    order = None
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user).order_by("-created").first()

    return render(request, "order_success.html", {"order": order})


@never_cache
@login_required(login_url="login")
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created")

    context = {"orders": orders}

    return render(request,"my_orders.html",context)


@never_cache
@login_required(login_url="login")
def order_detail(request, id):

    order = get_object_or_404(
        Order,
        id=id,
        user=request.user
    )

    context = {"order": order}

    return render(request,"order_detail.html",context)


def search(request):
    """Search results page - displays all products matching user query"""
    query = request.GET.get("q", "").strip()
    
    if query:
        # Search by name, brand, and description - matching the navbar suggestions logic
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(description__icontains=query),
            available=True
        ).order_by("-created_at")
    else:
        products = Product.objects.none()

    context = {
        "query": query,
        "products": products,
        "product_count": products.count()
    }

    return render(request, "search.html", context)




def category_products(request, slug):
    if slug.isdigit():
        category = get_object_or_404(Category, id=int(slug))
    else:
        category_name = slug.replace("-", " ")
        category = get_object_or_404(Category, name__iexact=category_name)
    products = cache.get_or_set(
        _catalog_cache_key(f"category:{category.id}"),
        lambda: list(
            Product.objects.filter(category=category, available=True).order_by("-id")
        ),
        CATALOG_CACHE_TIMEOUT,
    )

    context = {
        "category": category,
        "products": products,

    }

    return render(request,"category_products.html",context)



def add_to_wishlist(request, id):

    if not request.user.is_authenticated:

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return JsonResponse({
                "success": False,
                "login_required": True,
                "message": "Please login to manage your wishlist."
            })

        return redirect(
            f"{reverse('login')}?next={request.get_full_path()}"
        )

    product = get_object_or_404(
        Product,
        id=id
    )

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).first()

    
    # REMOVE FROM WISHLIST
   

    if wishlist_item:

        wishlist_item.delete()

        return JsonResponse({
            "success": True,
            "is_wishlisted": False,
            "message": (
                f"{product.name} "
                "removed from your wishlist."
            )
        })

   
    # ADD TO WISHLIST
    

    Wishlist.objects.create(
        user=request.user,
        product=product
    )

    return JsonResponse({
        "success": True,
        "is_wishlisted": True,
        "message": (
            f"{product.name} "
            "added to your wishlist successfully."
        )
    })


@never_cache
@login_required(login_url="login")
def my_wishlist(request):

    wishlist = Wishlist.objects.filter(
        user=request.user
    ).order_by("-created_at")

    context = {
        "wishlist": wishlist
    }

    return render(
        request,
        "wishlist.html",
        context
    )


@login_required(login_url="login")
@require_POST
def clear_wishlist(request):

    Wishlist.objects.filter(user=request.user).delete()
    messages.success(request, "Your wishlist has been cleared.")

    return redirect("my_wishlist")


@login_required(login_url="login")
def remove_from_wishlist(request, id):

    wishlist_item = get_object_or_404(
        Wishlist,
        id=id,
        user=request.user
    )

    wishlist_item.delete()

    return redirect("my_wishlist")


@login_required(login_url="login")
@require_POST
def wishlist_toggle(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).first()


    
    # REMOVE FROM WISHLIST
    

    if wishlist_item:

        wishlist_item.delete()

        return JsonResponse({

            "success": True,

            "added": False,

            "message": f"{product.name} removed from wishlist."

        })


    
    # ADD TO WISHLIST
  

    Wishlist.objects.create(

        user=request.user,

        product=product

    )

    return JsonResponse({

        "success": True,

        "added": True,

        "message": f"{product.name} added to wishlist!"

    })

@never_cache
@login_required(login_url="login")
def edit_review(request, id):

    review = get_object_or_404(

        Review,

        id=id,
        user=request.user

    )

    if request.method == "POST":

        form = ReviewForm(

            request.POST,
            instance=review

        )

        if form.is_valid():

            form.save()
            return redirect("product_detail",review.product.id)

    else:

        form = ReviewForm(instance=review)

    context = {"form": form,"review": review,}

    return render(request,"edit_review.html",context)


@login_required(login_url="login")
def delete_review(request, id):

    review = get_object_or_404(

        Review,

        id=id,

        user=request.user

    )

    product_id = review.product.id
    review.delete()
    return redirect("product_detail",product_id)

@never_cache
@login_required(login_url="login")
def dashboard(request):

    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    total_reviews = Review.objects.count()
    total_wishlist = Wishlist.objects.count()

    low_stock = Product.objects.filter(
        stock__lte=5,
        stock__gt=0
    ).count()

    out_of_stock = Product.objects.filter(
        stock=0
    ).count()

    total_revenue = Order.objects.aggregate(
        total=Sum("total")
    )["total"] or 0


    recent_orders = Order.objects.select_related(
        "user"
    ).order_by("-created")[:5]


    monthly_sales = (

        Order.objects

        .annotate(month=ExtractMonth("created"))
        .values("month")
        .annotate(total_sales=Sum("total"))
        .order_by("month")

    )

    months = []
    sales = []

    for item in monthly_sales:

        months.append(item["month"])

        sales.append(float(item["total_sales"]))

    low_stock_products = Product.objects.filter(
        stock__lte=5,
        available=True
    ).order_by("stock")

    best_selling = (
        OrderItem.objects
        .values(
            "product__name"
        )
        .annotate(
            total_sold=Sum("quantity")
        )
        .order_by("-total_sold")[:5]
    )


    top_customers = (

        Order.objects

        .values("user__username")

        .annotate(
            total_spent=Sum("total"),
            total_orders=Count("id")
        )

        .order_by("-total_spent")[:5]

    )


    latest_reviews = (

        Review.objects

        .select_related("user","product")

        .order_by("-created_at")[:5]

    )

    category_names = []
    category_counts = []



    for category in Category.objects.all():

        category_names.append(category.name)

        category_counts.append(
            Product.objects.filter(category=category).count()
        )

    

    context = {

        "total_products": total_products,

        "total_categories": total_categories,

        "total_users": total_users,

        "total_orders": total_orders,

        "total_reviews": total_reviews,
        "total_wishlist": total_wishlist,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "total_revenue": total_revenue,
        "recent_orders":recent_orders,
        "low_stock_products": low_stock_products,
        "best_selling": best_selling,
        "category_names": category_names,
        "category_counts": category_counts,
        "months": months,
        "sales": sales,
        "top_customers": top_customers,
        "latest_reviews": latest_reviews,

    }

    return render(request,"dashboard/dashboard.html",context,)

@never_cache
@login_required(login_url="login")
@staff_member_required
def sales_report(request):
    orders = Order.objects.all().order_by("-created")


    # Get Dates
    
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    
    # Apply Filter

    if start_date and end_date:

        orders = orders.filter(

            created__date__range=[start_date,end_date]

        )


    # Dashboard Cards
    

    total_orders = orders.count()
    total_revenue = orders.aggregate(

        total=Sum("total")

    )["total"] or 0

    total_products_sold = (

        OrderItem.objects.filter(

            order__in=orders

        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0

    )


    # Monthly Sales Chart

    monthly_sales = (

        orders

        .annotate(month=ExtractMonth("created"))

        .values("month")

        .annotate(total_sales=Sum("total"))

        .order_by("month")

    )

    months = []
    sales = []

    for item in monthly_sales:
        months.append(item["month"])
        sales.append(float(item["total_sales"]))

    context = {

        "orders": orders,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_products_sold": total_products_sold,
        "months": months,
        "sales": sales,
        "start_date": start_date,
        "end_date": end_date,

    }

    return render(request,"reports/sales_report.html",context,)



@login_required(login_url="login")
@staff_member_required
def export_sales_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="sales_report.pdf"'

    document = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(

        Paragraph(

            "<b>FragVerse Sales Report</b>",

            styles["Title"]

        )

    )

    elements.append(Spacer(1,0.30 * inch))
    orders = Order.objects.all().order_by("-created")
    total_orders = orders.count()
    total_revenue = orders.aggregate(

        total=Sum("total")

    )["total"] or 0

    total_products = (

        OrderItem.objects.aggregate(

            total=Sum("quantity")

        )["total"] or 0

    )

    elements.append(

        Paragraph(

            f"<b>Total Orders:</b> {total_orders}",

            styles["Normal"]

        )

    )

    elements.append(

        Paragraph(

            f"<b>Total Revenue:</b> â‚¹{total_revenue}",

            styles["Normal"]

        )

    )

    elements.append(

        Paragraph(

            f"<b>Products Sold:</b> {total_products}",

            styles["Normal"]

        )

    )

    elements.append(

        Spacer(1,0.30 * inch))

    data = [

        [

            "ID",
            "Customer",
            "Revenue",
            "Date"

        ]

    ]

    for order in orders:

        data.append(

            [

                order.id,

                order.user.username,

                f"â‚¹{order.total}",

                order.created.strftime(

                    "%d-%m-%Y"

                )

            ]

        )

    table = Table(data)

    table.setStyle(

        TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.grey),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),1,colors.black),
            ("BACKGROUND",(0,1),(-1,-1),colors.beige),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("BOTTOMPADDING",(0,0),(-1,0),10),

        ])

    )

    elements.append(table)
    document.build(elements)
    return response


def shop(request):
    products = Product.objects.filter(available=True)

    search_query = request.GET.get('q', '').strip()
    category_value = request.GET.get('category', '').strip()
    brand_name = request.GET.get('brand', '').strip()
    price_filter = request.GET.get('price', '').strip()
    availability = request.GET.get('availability', '').strip()
    sort_by = request.GET.get('sort', 'newest')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_value:
        category_id = category_value if category_value.isdigit() else None
        if category_id is not None:
            products = products.filter(category_id=category_id)
        else:
            products = products.filter(category__name__iexact=category_value)

    if brand_name:
        products = products.filter(brand__iexact=brand_name)

    if availability == 'in_stock':
        products = products.filter(stock__gt=0)

    if price_filter == 'under_1000':
        products = products.filter(price__lt=1000)
    elif price_filter == '1000_2500':
        products = products.filter(price__gte=1000, price__lte=2500)
    elif price_filter == '2500_5000':
        products = products.filter(price__gt=2500, price__lte=5000)
    elif price_filter == 'above_5000':
        products = products.filter(price__gt=5000)

    if sort_by == 'price_low':
        products = products.order_by('price', '-created_at')
    elif sort_by == 'price_high':
        products = products.order_by('-price', '-created_at')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    else:
        products = products.order_by('-created_at')

    categories = Category.objects.all().order_by('name')
    brands = Product.objects.filter(available=True).values_list('brand', flat=True).distinct().order_by('brand')

    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'selected_category': category_value,
        'selected_brand': brand_name,
        'selected_price': price_filter,
        'selected_availability': availability,
        'selected_sort': sort_by,
        'search_query': search_query,
    }
    return render(request, 'shop.html', context)


def brands(request):

    perfumes = Product.objects.filter(available=True).order_by("-id")
    context = {"perfumes": perfumes}
    return render(request,"brands.html",context)


def about(request):
    return render(request,"about.html")


def contact(request):
    return render(request, "contact.html")



def apply_coupon(request):
    cart = Cart(request)
    form = CouponForm(request.POST, cart_total=cart.get_total_price())

    if form.is_valid():
        request.session["coupon_code"] = form.coupon.code
        request.session["coupon_discount"] = str(form.get_discount())
        messages.success(request, f"Coupon {form.coupon.code} applied successfully!")
    else:
        for errors in form.errors.values():
            messages.error(request, errors[0])

    return redirect("checkout")


def remove_coupon(request):

    request.session.pop("coupon_code",None)
    request.session.pop("coupon_discount",None)
    messages.success(request,"Coupon removed.")
    return redirect("checkout")



def contact(request):

    if request.method == "POST":

        form = ContactForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(request,"Message delivered successfully!")
            return redirect("contact")

    else:

        form = ContactForm()

    context = {"form": form}
    return render(request, "contact.html", context)


def search_suggestions(request):
    """API endpoint for search suggestions - returns JSON"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Search for products by name, brand, or description (case-insensitive)
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(brand__icontains=query) |
        Q(description__icontains=query),
        available=True
    )[:8]  # Limit to 8 suggestions for performance
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'brand': product.brand,
            'image': product.image.url if product.image else '',
            'price': str(product.price),
            'url': f'/product/{product.id}/'  # Use ID for faster lookup
        })
    
    return JsonResponse({'results': results})





@login_required(login_url="login")
def edit_review(request, id):

    review = get_object_or_404(

        Review,

        id=id,
        user=request.user

    )

    if request.method == "POST":

        form = ReviewForm(

            request.POST,
            instance=review

        )

        if form.is_valid():

            form.save()
            return redirect("product_detail",review.product.id)

    else:

        form = ReviewForm(instance=review)

    context = {"form": form,"review": review,}

    return render(request,"edit_review.html",context)


@login_required(login_url="login")
def delete_review(request, id):

    review = get_object_or_404(

        Review,

        id=id,

        user=request.user

    )

    product_id = review.product.id
    review.delete()
    return redirect("product_detail",product_id)


@login_required(login_url="login")
def dashboard(request):

    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    total_reviews = Review.objects.count()
    total_wishlist = Wishlist.objects.count()

    low_stock = Product.objects.filter(
        stock__lte=5,
        stock__gt=0
    ).count()

    out_of_stock = Product.objects.filter(
        stock=0
    ).count()

    total_revenue = Order.objects.aggregate(
        total=Sum("total")
    )["total"] or 0


    recent_orders = Order.objects.select_related(
        "user"
    ).order_by("-created")[:5]


    monthly_sales = (

        Order.objects

        .annotate(month=ExtractMonth("created"))
        .values("month")
        .annotate(total_sales=Sum("total"))
        .order_by("month")

    )

    months = []
    sales = []

    for item in monthly_sales:

        months.append(item["month"])

        sales.append(float(item["total_sales"]))

    low_stock_products = Product.objects.filter(
        stock__lte=5,
        available=True
    ).order_by("stock")

    best_selling = (
        OrderItem.objects
        .values(
            "product__name"
        )
        .annotate(
            total_sold=Sum("quantity")
        )
        .order_by("-total_sold")[:5]
    )


    top_customers = (

        Order.objects

        .values("user__username")

        .annotate(
            total_spent=Sum("total"),
            total_orders=Count("id")
        )

        .order_by("-total_spent")[:5]

    )


    latest_reviews = (

        Review.objects

        .select_related("user","product")

        .order_by("-created_at")[:5]

    )

    category_names = []
    category_counts = []



    for category in Category.objects.all():

        category_names.append(category.name)

        category_counts.append(
            Product.objects.filter(category=category).count()
        )

    

    context = {

        "total_products": total_products,

        "total_categories": total_categories,

        "total_users": total_users,

        "total_orders": total_orders,

        "total_reviews": total_reviews,
        "total_wishlist": total_wishlist,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "total_revenue": total_revenue,
        "recent_orders":recent_orders,
        "low_stock_products": low_stock_products,
        "best_selling": best_selling,
        "category_names": category_names,
        "category_counts": category_counts,
        "months": months,
        "sales": sales,
        "top_customers": top_customers,
        "latest_reviews": latest_reviews,

    }

    return render(request,"dashboard/dashboard.html",context,)


@login_required(login_url="login")
@staff_member_required
def sales_report(request):
    orders = Order.objects.all().order_by("-created")


    # Get Dates
    
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    
    # Apply Filter

    if start_date and end_date:

        orders = orders.filter(

            created__date__range=[start_date,end_date]

        )


    # Dashboard Cards
    

    total_orders = orders.count()
    total_revenue = orders.aggregate(

        total=Sum("total")

    )["total"] or 0

    total_products_sold = (

        OrderItem.objects.filter(

            order__in=orders

        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0

    )


    # Monthly Sales Chart

    monthly_sales = (

        orders

        .annotate(month=ExtractMonth("created"))

        .values("month")

        .annotate(total_sales=Sum("total"))

        .order_by("month")

    )

    months = []
    sales = []

    for item in monthly_sales:
        months.append(item["month"])
        sales.append(float(item["total_sales"]))

    context = {

        "orders": orders,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_products_sold": total_products_sold,
        "months": months,
        "sales": sales,
        "start_date": start_date,
        "end_date": end_date,

    }

    return render(request,"reports/sales_report.html",context,)



@login_required(login_url="login")
@staff_member_required
def export_sales_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="sales_report.pdf"'

    document = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(

        Paragraph(

            "<b>FragVerse Sales Report</b>",

            styles["Title"]

        )

    )

    elements.append(Spacer(1,0.30 * inch))
    orders = Order.objects.all().order_by("-created")
    total_orders = orders.count()
    total_revenue = orders.aggregate(

        total=Sum("total")

    )["total"] or 0

    total_products = (

        OrderItem.objects.aggregate(

            total=Sum("quantity")

        )["total"] or 0

    )

    elements.append(

        Paragraph(

            f"<b>Total Orders:</b> {total_orders}",

            styles["Normal"]

        )

    )

    elements.append(

        Paragraph(

            f"<b>Total Revenue:</b> â‚¹{total_revenue}",

            styles["Normal"]

        )

    )

    elements.append(

        Paragraph(

            f"<b>Products Sold:</b> {total_products}",

            styles["Normal"]

        )

    )

    elements.append(

        Spacer(1,0.30 * inch))

    data = [

        [

            "ID",
            "Customer",
            "Revenue",
            "Date"

        ]

    ]

    for order in orders:

        data.append(

            [

                order.id,

                order.user.username,

                f"â‚¹{order.total}",

                order.created.strftime(

                    "%d-%m-%Y"

                )

            ]

        )

    table = Table(data)

    table.setStyle(

        TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.grey),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),1,colors.black),
            ("BACKGROUND",(0,1),(-1,-1),colors.beige),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("BOTTOMPADDING",(0,0),(-1,0),10),

        ])

    )

    elements.append(table)
    document.build(elements)
    return response


def brands(request):

    perfumes = Product.objects.filter(available=True).order_by("-id")
    context = {"perfumes": perfumes}
    return render(request,"brands.html",context)


def about(request):
    return render(request,"about.html")


def contact(request):
    return render(request, "contact.html")



@login_required(login_url="login")
def apply_coupon(request):

    cart = Cart(request)

    form = CouponForm(
        request.POST,
        cart_total=cart.get_total_price()
    )

    if form.is_valid():

        request.session["coupon_code"] = form.coupon.code.upper()

        request.session["coupon_discount"] = str(
            form.get_discount()
        )

        messages.success(
            request,
            f"Coupon {form.coupon.code.upper()} applied successfully!"
        )

    else:

        for errors in form.errors.values():

            messages.error(
                request,
                errors[0]
            )

    return redirect("checkout")


def remove_coupon(request):

    request.session.pop("coupon_code",None)
    request.session.pop("coupon_discount",None)
    messages.success(request,"Coupon removed.")
    return redirect("checkout")



def contact(request):

    if request.method == "POST":

        form = ContactForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(request,"Message delivered successfully!")
            return redirect("contact")

    else:

        form = ContactForm()

    context = {"form": form}
    return render(request, "contact.html", context)


def search_suggestions(request):
    """API endpoint for search suggestions - returns JSON"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Search for products by name, brand, or description (case-insensitive)
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(brand__icontains=query) |
        Q(description__icontains=query),
        available=True
    )[:8]  # Limit to 8 suggestions for performance
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'brand': product.brand,
            'image': product.image.url if product.image else '',
            'price': str(product.price),
            'url': f'/product/{product.id}/'  # Use ID for faster lookup
        })
    
    return JsonResponse({'results': results})



