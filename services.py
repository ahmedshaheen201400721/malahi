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
            # 'coupons' is passed through as-is rather than coerced to []:
            # None means the payload carried no coupons key at all, which the
            # prune step in sync_malahi_catalog() must not read as "every
            # coupon was withdrawn". An explicit [] genuinely means none.
            return data.get('providers') or [], data.get('coupons'), data.get('generated_at')
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
    from malahi_extension.models import MalahiCoupon, MalahiProvider
    from modules.products.models import ProductTemplate

    providers, coupons, generated_at = fetch_malahi_catalog()

    # ProductTemplate requires a company; outside a request
    # (shell/Celery) there is no current company, so fall back to the first one.
    company_id = get_current_company() or Company.objects.values_list('id', flat=True).first()

    counts = {
        'products_created': 0, 'products_updated': 0,
        'coupons_created': 0, 'coupons_updated': 0, 'coupons_deleted': 0,
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

        # No category is derived from the provider. This used to mint one
        # ProductCategory per provider and assign it to every product, which put
        # 52 shop names at the top of a tree meant for accounting/reporting
        # categories — and duplicated, as a name-matched string, a fact already
        # held properly by the malahi_provider FK below. Grouping by shop is done
        # through that field, which the product form now shows.
        #
        # `categ` is left untouched on update, so a category a user has chosen
        # for a product survives the sync instead of being overwritten nightly.
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
    seen_codes = set()
    for item in coupons or []:
        code = (item.get('coupon') or '').strip()
        if not code:
            continue
        seen_codes.add(code)
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

    # A coupon withdrawn upstream is deleted locally, so a code the Malahi
    # platform no longer issues cannot keep being honoured here.
    #
    # Guarded on `is not None`, not on truthiness. fetch_malahi_catalog()
    # validates only that 'providers' is present, so a truncated or reshaped
    # response can reach this point with no coupons key at all — and treating
    # that as "every coupon was withdrawn" would empty the table on a bad
    # response rather than on a real change. An explicit empty list is a real
    # answer and still prunes everything.
    #
    # Deleted one at a time rather than via queryset.delete() so BaseModel's
    # pre_delete/post_delete hooks run; the coupon table is small enough that
    # the extra queries do not matter.
    if coupons is not None:
        for coupon in MalahiCoupon.objects.exclude(code__in=seen_codes):
            coupon.delete()
            counts['coupons_deleted'] += 1

    counts['rag_collections_queued'] = refresh_product_rag()

    logger.info("Malahi catalog sync done: %s", counts)
    return counts


def refresh_product_rag():
    """Queue a full re-index of every model-RAG collection over ProductTemplate.

    aistudio keeps model collections fresh with per-record post_save/post_delete
    signals, each firing its own Celery task. That works for ordinary edits but
    not for a catalog sync: this function creates and deletes products in bulk,
    so hundreds of tasks are queued at once and any that fail — a burst past the
    role's connection limit is enough — leave the index silently partial, with
    stale rows still pointing at deleted products.

    A full collection sync is the repair: it re-reads every record and indexes
    with cleanup="full", so it both adds what is missing and prunes what is gone.

    Best-effort by design — the catalog is already committed by the time this
    runs, so a RAG problem must never turn a successful sync into a failure.
    Returns the collection ids queued (empty list if none, or on failure).
    """
    try:
        from django.contrib.contenttypes.models import ContentType
        from modules.aistudio.models import Collection
        from modules.aistudio.tasks import sync_model_collection_task
        from modules.products.models import ProductTemplate

        content_type = ContentType.objects.get_for_model(ProductTemplate)
        collection_ids = list(
            Collection.objects.filter(
                source_type='model',
                model_content_type=content_type,
                is_indexed=True,
            ).values_list('id', flat=True)
        )
        for collection_id in collection_ids:
            sync_model_collection_task.delay(collection_id)
        if collection_ids:
            logger.info("Queued product RAG re-index for collections %s", collection_ids)
        return collection_ids
    except Exception as exc:
        logger.warning("Could not queue product RAG re-index: %s", exc)
        return []


def format_sync_result(counts):
    """Wrap sync counts into the standard @action response dict."""
    message = _(
        "Malahi catalog synced: %(pc)d products created, %(pu)d updated, "
        "%(cc)d coupons created, %(cu)d updated, %(cd)d removed."
    ) % {
        'pc': counts['products_created'], 'pu': counts['products_updated'],
        'cc': counts['coupons_created'], 'cu': counts['coupons_updated'],
        'cd': counts.get('coupons_deleted', 0),
    }
    if counts.get('rag_collections_queued'):
        message += " " + _("Search index refresh queued.")
    return {
        'status': True,
        'open_mode': 'message',
        'message': message,
        'data': {},
        'on_success': {'type': 'refresh'},
    }
