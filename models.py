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

    # Cities the venue operates in, from the feed's per-provider `cities` array.
    # Kept on the provider rather than the product: the feed carries no
    # per-product city, and a provider's branch-specific offers (الظهران مول vs
    # الحمراء مول) would otherwise be advertised in cities they don't exist in.
    cities = models.ManyToManyField(
        'base.City', blank=True, related_name='malahi_providers',
        help_text="Cities this venue operates in (synced from the Malahi catalog)",
    )

    # Business counterpart, used when transacting with the venue. Deliberately
    # separate from this mirror: the nightly sync overwrites name/terms and
    # re-sets cities on every run, and must never clobber a Partner that carries
    # purchase orders, invoices, payment terms or bank details.
    partner = models.ForeignKey(
        'base.Partner', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='malahi_providers',
        help_text="Supplier record used when transacting with this venue",
    )

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
        from malahi_extension.services import sync_malahi_catalog, format_sync_result
        return format_sync_result(sync_malahi_catalog())
