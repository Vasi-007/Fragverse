from django.urls import path
from . import views

urlpatterns = [

    path("", views.home, name="home"),

    path("product/<slug:slug>/", views.product_detail, name="product_detail"),

    path("cart/", views.cart_detail, name="cart_detail"),

    path("cart/add/<int:id>/", views.cart_add, name="cart_add"),

    path("cart/increase/<int:id>/<int:variant_id>/", views.cart_increase, name="cart_increase"),

    path("cart/decrease/<int:id>/<int:variant_id>/", views.cart_decrease, name="cart_decrease"),

    path("cart/remove/<int:id>/<int:variant_id>/", views.cart_remove, name="cart_remove"),

    path("cart/clear/", views.cart_clear, name="cart_clear"),

    path('checkout/',views.checkout,name='checkout'),

    path("payment-success/", views.payment_success, name="payment_success"),

    path("order-success/",views.order_success,name="order_success"),

    path("my-orders/",views.my_orders,name="my_orders"),

    path("order/<int:id>/",views.order_detail,name="order_detail"),

    path("search/",views.search,name="search"),

    path("api/search-suggestions/", views.search_suggestions, name="search_suggestions"),

    path("category/<slug:slug>/",views.category_products,name="category_products"),

    path("wishlist/add/<int:id>/",views.add_to_wishlist,name="add_to_wishlist",),

    path("wishlist/",views.my_wishlist,name="my_wishlist"),

    path("wishlist/clear/", views.clear_wishlist, name="clear_wishlist"),

    path("wishlist/remove/<int:id>/",views.remove_from_wishlist,name="remove_from_wishlist"),

    path(
    "wishlist/toggle/<int:id>/",views.wishlist_toggle,name="wishlist_toggle"),

    path("review/edit/<int:id>/",views.edit_review,name="edit_review"),

    path("review/delete/<int:id>/",views.delete_review,name="delete_review"),

    path("dashboard/",views.dashboard,name="dashboard"),

    path("sales-report/pdf/",views.export_sales_pdf,name="export_sales_pdf",),

    path("sales-report/",views.sales_report,name="sales_report",),

    path("shop/",views.shop,name="shop"),

    path("brands/",views.brands,name="brands"),

    path("about/",views.about,name="about"),

    path("contact/",views.contact,name="contact"),

    path("apply-coupon/",views.apply_coupon,name="apply_coupon"),
    
    path("remove-coupon/",views.remove_coupon,name="remove_coupon"),

    
]