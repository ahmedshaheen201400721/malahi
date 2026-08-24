# -*- coding: utf-8 -*-
# Model extensions for malahi_extension module
from django.db import models

from modules.base.model_inheritance import ModelExtension
from modules.base.decorators import action


class ProductTemplateMalahiExtension(ModelExtension):
    """Malahi catalog fields on products.ProductTemplate (columns added by sync_schema)."""

    _inherit = 'products.producttemplate'
    _depends = ['products']

    malahi_product_id = models.IntegerField(
        null=True, blank=True,
        help_text="Product id on the Malahi catalog (sync upsert key)",
    )
    malahi_price_before = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True,
        help_text="Malahi price before discount",
    )
    malahi_provider = models.ForeignKey(
        'malahi_extension.MalahiProvider',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
    )

    @action
    def action_sync_malahi_catalog(queryset):
        """Fetch the Malahi catalog and upsert providers, products and coupons."""
        from modules.malahi_extension.services import sync_malahi_catalog, format_sync_result
        return format_sync_result(sync_malahi_catalog())
