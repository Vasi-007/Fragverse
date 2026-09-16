from uuid import uuid4

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Category, Product


def invalidate_catalog_cache(**kwargs):
    cache.set("store:catalog-version", uuid4().hex, timeout=None)


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_catalog_cache_on_change(sender, **kwargs):
    invalidate_catalog_cache()
