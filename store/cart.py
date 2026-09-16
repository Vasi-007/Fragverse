from .models import Product, ProductVariant


class Cart:

    def __init__(self, request):

        self.session = request.session

        cart = self.session.get("cart")

        if not isinstance(cart, dict):
            cart = {}

        self.cart = cart

        self.session["cart"] = self.cart

    
    # ADD PRODUCT + VARIANT
    
    def add(self, product, variant):

        cart_key = f"{product.id}_{variant.id}"
        current_quantity = 0

        if cart_key in self.cart and isinstance(self.cart[cart_key], dict):
            current_quantity = self.cart[cart_key].get("quantity", 0)

        if variant.stock <= 0 or current_quantity >= variant.stock:
            return False

        # Create new cart item
        if cart_key not in self.cart:

            self.cart[cart_key] = {
                "product_id": product.id,
                "variant_id": variant.id,
                "quantity": 1,
            }

        else:

            # Safety check for old/broken cart data
            if not isinstance(self.cart[cart_key], dict):

                self.cart[cart_key] = {
                    "product_id": product.id,
                    "variant_id": variant.id,
                    "quantity": 1,
                }

            else:

                self.cart[cart_key]["quantity"] += 1

        self.save()
        return True

    
    # INCREASE
    
    def increase(self, product, variant):

        cart_key = f"{product.id}_{variant.id}"

        if cart_key in self.cart:

            if isinstance(self.cart[cart_key], dict):
                current_quantity = self.cart[cart_key].get("quantity", 0)

                if current_quantity >= variant.stock:
                    return False

                self.cart[cart_key]["quantity"] += 1
                self.save()
                return True

        return False

    
    # DECREASE
    
    def decrease(self, product, variant):

        cart_key = f"{product.id}_{variant.id}"

        if cart_key in self.cart:

            if isinstance(self.cart[cart_key], dict):

                self.cart[cart_key]["quantity"] -= 1

                if self.cart[cart_key]["quantity"] <= 0:

                    del self.cart[cart_key]

                self.save()

    
    # REMOVE
    
    def remove(self, product, variant):

        cart_key = f"{product.id}_{variant.id}"

        if cart_key in self.cart:

            del self.cart[cart_key]

            self.save()

    # --------------------------------
    # CLEAR CART
    # --------------------------------
    def clear(self):

        self.session["cart"] = {}

        self.cart = self.session["cart"]

        self.save()

    # --------------------------------
    # SAVE SESSION
    # --------------------------------
    def save(self):

        self.session.modified = True

    
    # ITERATE CART
    
    def __iter__(self):

        product_ids = []
        variant_ids = []

        # --------------------------------
        # REMOVE OLD / INVALID DATA
        # --------------------------------

        invalid_keys = []

        for key, item in self.cart.items():

            # Old cart format or invalid data
            if not isinstance(item, dict):

                invalid_keys.append(key)
                continue

            if "product_id" not in item:

                invalid_keys.append(key)
                continue

            if "variant_id" not in item:

                invalid_keys.append(key)
                continue

            if "quantity" not in item:

                invalid_keys.append(key)
                continue

            product_ids.append(
                item["product_id"]
            )

            variant_ids.append(
                item["variant_id"]
            )

        # Remove invalid old cart items
        if invalid_keys:

            for key in invalid_keys:

                del self.cart[key]

            self.save()

        
        # GET PRODUCTS
        

        products = Product.objects.filter(
            id__in=product_ids
        )

        
        # GET VARIANTS
        

        variants = ProductVariant.objects.filter(
            id__in=variant_ids
        )

        
        # CREATE DICTIONARIES
        

        product_dict = {
            product.id: product
            for product in products
        }

        variant_dict = {
            variant.id: variant
            for variant in variants
        }

    
        # BUILD CART ITEMS
        

        for key, item in self.cart.items():

            # Safety check
            if not isinstance(item, dict):
                continue

            if "product_id" not in item:
                continue

            if "variant_id" not in item:
                continue

            if "quantity" not in item:
                continue

            product = product_dict.get(
                item["product_id"]
            )

            variant = variant_dict.get(
                item["variant_id"]
            )

            # Product doesn't exist
            if not product:
                continue

            # Variant doesn't exist
            if not variant:
                continue

            # Make sure variant belongs to product
            if variant.product_id != product.id:
                continue

            quantity = item["quantity"]

            price = variant.discounted_price

            subtotal = price * quantity

            yield {
                "product": product,
                "variant": variant,
                "price": price,
                "quantity": quantity,
                "subtotal": subtotal,
            }

    
    # TOTAL PRICE

    def get_total_price(self):

        total = 0

        for item in self:

            total += item["subtotal"]

        return total


    # TOTAL QUANTITY
    
    def get_total_quantity(self):

        total = 0

        for item in self:

            total += item["quantity"]

        return total

    
    # LENGTH
   
    def __len__(self):

        return self.get_total_quantity()