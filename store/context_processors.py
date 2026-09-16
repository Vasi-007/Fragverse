from .cart import Cart
from .models import Wishlist


def cart(request):
  return {"cart": Cart(request)}



from .models import Wishlist


def wishlist(request):

    if request.user.is_authenticated:

        wishlist_product_ids = set(
            Wishlist.objects.filter(
                user=request.user
            ).values_list(
                "product_id",
                flat=True
            )
        )

    else:

        wishlist_product_ids = set()


    return {
        "wishlist_product_ids": wishlist_product_ids
    }


