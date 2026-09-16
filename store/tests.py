from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from store.cart import Cart
from store.models import Category, ContactMessage, Product, ProductVariant, CategoryOffer, Wishlist


class CartStockLimitTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name="Perfume",
            image="categories/test.jpg",
        )
        self.product = Product.objects.create(
            category=category,
            name="Test Perfume",
            brand="Test Brand",
            description="A test fragrance",
            image="products/test.jpg",
            price=1200,
            stock=5,
            available=True,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size="50 ml",
            price=1200,
            stock=3,
            available=True,
        )

    def test_increase_does_not_exceed_variant_stock(self):
        request = type("Request", (), {"session": self.client.session})()
        cart = Cart(request)

        cart.add(self.product, self.variant)
        cart.increase(self.product, self.variant)
        cart.increase(self.product, self.variant)
        cart.increase(self.product, self.variant)

        cart_items = list(cart)

        self.assertEqual(len(cart_items), 1)
        self.assertEqual(cart_items[0]["quantity"], 3)

    def test_cart_add_defaults_to_50_ml_variant(self):
        user = User.objects.create_user(username="cart-user", password="password")
        self.client.force_login(user)
        self.product.name = "Rose Elegance"
        self.product.save(update_fields=["name"])
        self.variant.size = "50 ML "
        self.variant.save(update_fields=["size"])

        response = self.client.post(reverse("cart_add", args=[self.product.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["message"], "Rose Elegance added to cart!")
        self.assertEqual(
            self.client.session["cart"][f"{self.product.id}_{self.variant.id}"]["quantity"],
            1,
        )

    def test_cart_add_uses_selected_variant(self):
        user = User.objects.create_user(username="variant-user", password="password")
        self.client.force_login(user)
        selected_variant = ProductVariant.objects.create(
            product=self.product,
            size="100 ml",
            price=2200,
            stock=2,
            available=True,
        )

        response = self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": selected_variant.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn(
            f"{self.product.id}_{selected_variant.id}",
            self.client.session["cart"],
        )

    def test_ajax_quantity_updates_return_updated_cart_data(self):
        user = User.objects.create_user(username="quantity-user", password="password")
        self.client.force_login(user)
        self.client.post(reverse("cart_add", args=[self.product.id]))

        increase_response = self.client.get(
            reverse("cart_increase", args=[self.product.id, self.variant.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(increase_response.status_code, 200)
        self.assertEqual(increase_response.json()["quantity"], 2)

        decrease_response = self.client.get(
            reverse("cart_decrease", args=[self.product.id, self.variant.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(decrease_response.status_code, 200)
        self.assertEqual(decrease_response.json()["quantity"], 1)


class ShopFilterTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Luxury",
            image="categories/luxury.jpg",
        )
        self.other_category = Category.objects.create(
            name="Daily",
            image="categories/daily.jpg",
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Velvet Oud",
            brand="Maison Luxe",
            description="Warm oud scent",
            image="products/velvet.jpg",
            price=1800,
            stock=2,
            available=True,
        )
        ProductVariant.objects.create(
            product=self.product,
            size="50 ml",
            price=1800,
            stock=2,
            available=True,
        )

        Product.objects.create(
            category=self.other_category,
            name="Fresh Citrus",
            brand="Daily Bloom",
            description="Citrus fresh scent",
            image="products/citrus.jpg",
            price=900,
            stock=1,
            available=True,
        )

    def test_shop_search_and_category_filter_work(self):
        response = self.client.get(reverse("shop"), {"q": "Velvet", "category": str(self.category.id)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["products"]), [self.product])

    def test_shop_search_filters_products_by_query(self):
        response = self.client.get(reverse("shop"), {"q": "Fresh"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["products"].count(), 1)
        self.assertEqual(response.context["products"].first().name, "Fresh Citrus")

    def test_shop_can_sort_products_by_price(self):
        low_to_high = self.client.get(reverse("shop"), {"sort": "price_low"})
        self.assertEqual(
            list(low_to_high.context["products"].values_list("name", flat=True)),
            ["Fresh Citrus", "Velvet Oud"],
        )

        high_to_low = self.client.get(reverse("shop"), {"sort": "price_high"})
        self.assertEqual(
            high_to_low.context["products"].first().price,
            1800,
        )

    def test_shop_can_filter_products_by_price_range(self):
        response = self.client.get(reverse("shop"), {"price": "under_1000"})

        self.assertEqual(response.context["products"].count(), 1)
        self.assertEqual(response.context["products"].first().name, "Fresh Citrus")


class CategoryOfferTests(TestCase):
    def test_active_category_offer_is_shown_on_home(self):
        category = Category.objects.create(name="Arabic", image="categories/arabic.jpg")
        offer = CategoryOffer.objects.create(
            category=category,
            title="Arabic Oud Offer",
            description="Save on Arabic fragrances.",
            discount_percent=20,
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(offer, response.context["category_offers"])

    def test_inactive_category_offer_is_not_shown_on_home(self):
        category = Category.objects.create(name="Women", image="categories/women.jpg")
        CategoryOffer.objects.create(
            category=category,
            title="Women Offer",
            description="Save on women's fragrances.",
            active=False,
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["category_offers"], [])

    def test_active_offer_changes_variant_price(self):
        category = Category.objects.create(name="Arabic", image="categories/arabic.jpg")
        product = Product.objects.create(
            category=category,
            name="Oud Test",
            brand="FragVerse",
            description="Oud fragrance",
            image="products/oud.jpg",
            price=1000,
            stock=2,
        )
        variant = ProductVariant.objects.create(
            product=product, size="50 ml", price=1000, stock=2, available=True
        )
        CategoryOffer.objects.create(
            category=category,
            title="Diwali Offer",
            description="20% off",
            discount_percent=20,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=1),
        )

        self.assertEqual(variant.discounted_price, 800)

    def test_expired_offer_restores_original_variant_price(self):
        category = Category.objects.create(name="Women", image="categories/women.jpg")
        product = Product.objects.create(
            category=category,
            name="Floral Test",
            brand="FragVerse",
            description="Floral fragrance",
            image="products/floral.jpg",
            price=1000,
            stock=2,
        )
        variant = ProductVariant.objects.create(
            product=product, size="50 ml", price=1000, stock=2, available=True
        )
        CategoryOffer.objects.create(
            category=category,
            title="Expired Offer",
            description="20% off",
            discount_percent=20,
            valid_from=timezone.now() - timedelta(days=2),
            valid_to=timezone.now() - timedelta(days=1),
        )

        self.assertEqual(variant.discounted_price, 1000)


class ContactMessageTests(TestCase):

    def test_contact_form_creates_admin_message(self):
        response = self.client.post(
            reverse("contact"),
            {
                "full_name": "Asha Menon",
                "email": "asha@example.com",
                "subject": "Order fragrance help",
                "message": "Please help me choose a fragrance for an evening event.",
            },
        )

        self.assertRedirects(response, reverse("contact"))
        contact_message = ContactMessage.objects.get()
        self.assertEqual(contact_message.full_name, "Asha Menon")
        self.assertEqual(contact_message.status, "new")


class WishlistClearTests(TestCase):

    def test_clear_wishlist_removes_only_current_users_items(self):
        user = User.objects.create_user(username="wishlist-user", password="password")
        other_user = User.objects.create_user(username="other-user", password="password")
        category = Category.objects.create(name="Wishlist category", image="categories/wishlist.jpg")
        product = Product.objects.create(
            category=category,
            name="Wishlist perfume",
            brand="FragVerse",
            description="A saved fragrance",
            image="products/wishlist.jpg",
            price=1000,
        )
        Wishlist.objects.create(user=user, product=product)
        Wishlist.objects.create(user=other_user, product=product)
        self.client.force_login(user)

        response = self.client.post(reverse("clear_wishlist"))

        self.assertRedirects(response, reverse("my_wishlist"))
        self.assertFalse(Wishlist.objects.filter(user=user).exists())
        self.assertTrue(Wishlist.objects.filter(user=other_user).exists())
