# -*- coding: utf-8 -*-
# Models for malahi_extension module
from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.base.models.base import BaseModel
from modules.base.decorators import action


class MalahiProvider(BaseModel):
    """Malahi catalog provider/shop, synced from the Malahi AI-catalog API."""

    external_id = models.IntegerField(help_text="Provider id on the Malahi platform")
    name = models.CharField(max_length=255)
    terms = models.TextField(blank=True, null=True, help_text="Provider terms & conditions")

    class Meta:
        verbose_name = _('Malahi Provider')
        verbose_name_plural = _('Malahi Providers')
        ordering = ['name']

    def __str__(self):
        return self.name


class MalahiCoupon(BaseModel):
    """Discount coupon synced from the Malahi AI-catalog API."""

    code = models.CharField(max_length=100, unique=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Malahi Coupon')
        verbose_name_plural = _('Malahi Coupons')
        ordering = ['code']

    def __str__(self):
        return self.code

    @action
    def action_sync_malahi_catalog(queryset):
        """Fetch the Malahi catalog and upsert providers, products and coupons."""
        from modules.malahi_extension.services import sync_malahi_catalog, format_sync_result
        return format_sync_result(sync_malahi_catalog())
