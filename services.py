# -*- coding: utf-8 -*-
"""Sync the Malahi AI-catalog API into local providers, products and coupons."""
import logging
from decimal import Decimal, InvalidOperation

import requests
from django.utils import timezone
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

CATALOG_URL = "https://backend.malahi.sa/client-api/v1/ai-catalog"
CATALOG_FALLBACK_URL = "https://backend.malahi.sa/storage/ai_catalog.json"
REQUEST_TIMEOUT = 20


def _to_decimal(value):
    if value in (None, ''):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def fetch_malahi_catalog():
    """Return (providers, coupons, generated_at) from the Malahi catalog.

    Tries the live API first, then the nightly static file. The two sources
    differ only in envelope: the API wraps the payload in {"status", "data"}
    while the static file is the bare object.
    """
    last_error = None
    for url in (CATALOG_URL, CATALOG_FALLBACK_URL):
        try:
            response = requests.get(url, headers={'Accept': 'application/json'}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
            data = payload.get('data', payload)
            if 'providers' not in data:
                raise ValueError(f"Unexpected catalog payload from {url}")
            return data.get('providers') or [], data.get('coupons') or [], data.get('generated_at')
        except Exception as exc:
            last_error = exc
            logger.warning("Malahi catalog fetch failed from %s: %s", url, exc)
    raise RuntimeError(f"Could not fetch the Malahi catalog: {last_error}")


def sync_malahi_catalog():
    """Upsert MalahiProvider / ProductTemplate / MalahiCoupon rows from the API.

    Idempotent: providers are keyed by external_id, products by
    malahi_product_id, coupons by code.
    """
    from modules.base.middleware import get_current_company
    from modules.base.models import Company
    from modules.malahi_extension.models import MalahiCoupon, MalahiProvider
    from modules.products.models import ProductCategory, ProductTemplate

    providers, coupons, generated_at = fetch_malahi_catalog()

    # ProductCategory/ProductTemplate require a company; outside a request
    # (shell/Celery) there is no current company, so fall back to the first one.
    company_id = get_current_company() or Company.objects.values_list('id', flat=True).first()

    counts = {
        'products_created': 0, 'products_updated': 0,
        'coupons_created': 0, 'coupons_updated': 0,
        'providers': 0, 'generated_at': generated_at,
    }

    for block in providers:
        info = block.get('provider') or {}
        external_id = info.get('id')
        if external_id is None:
            continue

        provider_vals = {'name': info.get('name') or '', 'terms': info.get('terms') or ''}
        provider = MalahiProvider.objects.filter(external_id=external_id).first()
        if provider:
            for field, value in provider_vals.items():
                setattr(provider, field, value)
            provider.save()
        else:
            provider = MalahiProvider.create(external_id=external_id, **provider_vals)
        counts['providers'] += 1

        category = None
        if provider.name:
            category = ProductCategory.all_objects.filter(name=provider.name, company_id=company_id).first()
            if not category:
                category = ProductCategory.create(name=provider.name, company_id=company_id)

        for item in block.get('products') or []:
            product_id = item.get('product_id')
            if product_id is None:
                continue
            product_vals = {
                'name': item.get('name') or '',
                'description': item.get('description') or '',
                'sale_price': _to_decimal(item.get('final_price')),
                'cost': _to_decimal(item.get('cost')),
                'malahi_price_before': _to_decimal(item.get('price_before')),
                'malahi_provider': provider,
                'categ': category,
                'type': 'service',
                'sale_ok': True,
            }
            product = ProductTemplate.objects.filter(malahi_product_id=product_id).first()
            if product:
                for field, value in product_vals.items():
                    setattr(product, field, value)
                product.save()
                counts['products_updated'] += 1
            else:
                ProductTemplate.create(malahi_product_id=product_id, company_id=company_id, **product_vals)
                counts['products_created'] += 1

    now = timezone.now()
    for item in coupons:
        code = (item.get('coupon') or '').strip()
        if not code:
            continue
        coupon_vals = {'percentage': _to_decimal(item.get('percentage')) or Decimal('0'), 'last_synced_at': now}
        coupon = MalahiCoupon.objects.filter(code=code).first()
        if coupon:
            for field, value in coupon_vals.items():
                setattr(coupon, field, value)
            coupon.save()
            counts['coupons_updated'] += 1
        else:
            MalahiCoupon.create(code=code, **coupon_vals)
            counts['coupons_created'] += 1

    logger.info("Malahi catalog sync done: %s", counts)
    return counts


def format_sync_result(counts):
    """Wrap sync counts into the standard @action response dict."""
    message = _(
        "Malahi catalog synced: %(pc)d products created, %(pu)d updated, "
        "%(cc)d coupons created, %(cu)d updated."
    ) % {
        'pc': counts['products_created'], 'pu': counts['products_updated'],
        'cc': counts['coupons_created'], 'cu': counts['coupons_updated'],
    }
    return {
        'status': True,
        'open_mode': 'message',
        'message': message,
        'data': {},
        'on_success': {'type': 'refresh'},
    }
