from django.contrib import admin
from .models import Category,ContactMessage,Product,ProductVariant,Wishlist,Review,Coupon,CategoryOffer

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

  list_display=("id","name","created_at")

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "brand",
        "price",
        "stock",
        "available",
    )

    list_filter = ("available","category",)

    search_fields = ("name","brand",)

    inlines = [ProductVariantInline]

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "product",
        "created_at",
    )

    search_fields = ("user__username","product__name",)
    ordering = ("-created_at",)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (

        "id",
        "product",
        "user",
        "rating",
        "created_at",

    )

    list_filter = ("rating","created_at",)
    search_fields = ("product__name","user__username",)
    ordering = ("-created_at",)



@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "discount_percent",
        "minimum_amount",
        "maximum_discount",
        "valid_from",
        "valid_to",
        "active",
    )

    list_filter = (
        "active",
        "valid_from",
        "valid_to",
    )

    search_fields = ("code",)


@admin.register(CategoryOffer)
class CategoryOfferAdmin(admin.ModelAdmin):

    list_display = (
        "category",
        "title",
        "discount_percent",
        "active",
        "valid_from",
        "valid_to",
        "display_order",
    )
    list_filter = ("active", "category")
    search_fields = ("category__name", "title", "description")
    ordering = ("display_order", "category__name", "-created_at")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):

    list_display = ("full_name", "email", "subject", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email", "subject", "message")
    readonly_fields = ("created_at",)
    list_editable = ("status",)
    ordering = ("-created_at",)





@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "size",
        "color",
        "other",
        "price",
        "stock",
        "available",
    )

    list_filter = (
        "available",
        "size",
        "color",
    )

    search_fields = (
        "product__name",
        "product__brand",
        "size",
        "color",
        "other",
    )

