# -*- coding: utf-8 -*-
"""Malahi catalog fields on the ProductTemplate form views.

extensions.py declares malahi_price_before / malahi_provider / malahi_product_id
on products.producttemplate, but a ModelExtension only creates the column and the
model attribute — it never puts the field on a screen. These patches do that, for
every product form view that already shows sale_price.

The nightly sync maps the catalog's three prices as
    final_price  -> sale_price           (core field, already displayed)
    cost         -> cost                 (core field, already displayed)
    price_before -> malahi_price_before  (this module)
so price_before is the "was" half of a "was 150, now 120" pair. It is placed
directly under Sales Price where that comparison is readable, rather than in a
tab of its own; the two catalog-metadata fields go in a group below it.
"""
from django.utils.translation import gettext as _


# Content is built by factories rather than shared module-level constants
# because the `after` operation inserts its content BY REFERENCE
# (ui_view.py: parent.insert(index, content)). One dict reused across five
# patches would be the same object living in five rendered views.
#
# view_registry calls every module-level callable with no arguments and registers
# whatever comes back if it looks like a view (a dict carrying BOTH 'view_type'
# and 'name' — view_registry.py:212). None of these return that shape, so they
# cannot be mistaken for view definitions. _patch() raises TypeError under that
# probe, which the registry swallows deliberately (view_registry.py:218).


def _malahi_price_field():
    """The pre-discount catalog price, shown beside sale_price.

    "number" and not "money": sale_price and cost both use "number", and the
    "money" widget appears only a handful of times repo-wide and never on this
    model. Matching the neighbours matters more here than the nicer widget.

    Read-only because the sync overwrites it on every run — an edit would
    survive only until the next nightly catalog fetch.
    """
    return {
        "name": "malahi_price_before",
        "string": _("Price Before Discount"),
        "widget": "number",
        "min": 0,
        "precision": 2,
        "readonly": True,
        "help": _("Malahi catalog price before the discount. Updated by the catalog sync."),
    }


def _malahi_catalog_group():
    """Provider and external id, kept out of the pricing row."""
    return {
        "title": _("Malahi Catalog"),
        "fields": [
            {
                "name": "malahi_provider",
                "string": _("Malahi Provider"),
                "widget": "relation",
                "multiSelect": False,
                "placeholder": _("Select provider..."),
                "help": _("The Malahi provider this product was synced from"),
            },
            {
                # Read-only on purpose: sync_malahi_catalog() matches products on
                # this value, so editing it by hand orphans the product and the
                # next sync creates a duplicate alongside it.
                "name": "malahi_product_id",
                "string": _("Malahi Product ID"),
                "widget": "number",
                "readonly": True,
                "help": _("Product id on the Malahi catalog. The sync matches on this value."),
            },
        ],
    }


def _malahi_operations():
    """The two operations every one of these patches applies.

    Returns a list, so the zero-argument probe above cannot mistake it for a
    view definition either.
    """
    return [
        # "after", NOT "insert_after". insert_after/insert_before are menu-engine
        # vocabulary; in a view they fall through to the else branch of
        # _apply_single_operation and are a silent no-op (seven files in modules/
        # already do this and their patches never render).
        #
        # Targeting by name rather than by sheet.tabs.0.sections.0.groups.1.fields.0
        # so the patch survives a field being added above sale_price. The lookup is
        # a recursive whole-body search, which is safe only because sale_price
        # occurs exactly once in each of the five target views — verified before
        # writing this. Content is a bare dict: a list would nest inside `fields`.
        {
            "operation": "after",
            "target": "field[name=sale_price]",
            "content": _malahi_price_field(),
        },
        # Appends a third group to the General Information tab. Target resolves to
        # a list, and a list content is extended into it.
        {
            "operation": "append",
            "target": "sheet.tabs.0.sections.0.groups",
            "content": [_malahi_catalog_group()],
        },
    ]


def _patch(key, name, inherit_id, priority):
    """Build one patch against one target view.

    Every argument but `key`/`inherit_id` looks redundant; `priority` is not.
    UIView.unique_together is (model, view_type, priority, module, menu_item) and
    view_registry resolves a collision by DELETING the other row rather than
    raising (view_registry.py:487-498). These five patches share model, view_type,
    menu_item and module, so a shared priority would leave exactly one survivor
    and log nothing. Hence 30-34, above the 20/21/22/25 already in use on this
    model.

    The sibling patches in modules/sales_account and modules/stock avoid that
    collision by setting `module` to the TARGET view's module instead. That is a
    latent bug, not a convention to copy: sync_ui_views --app X hard-deletes every
    key under module X that it does not rediscover, so `"module": "sales"` here
    would mean a plain `sync_ui_views --app sales` silently wipes these patches —
    sales' own file glob will never find a file that lives in this extension.
    """
    return {
        "key": key,
        "name": name,
        "model": "products.producttemplate",
        "view_type": "form",
        "priority": priority,
        "inherit_mode": "extension",
        "inherit_id": inherit_id,
        "module": "malahi_extension",
        "inheritance_operations": _malahi_operations(),
    }


# Sales > Products
malahi_product_form_sales_patch = _patch(
    "malahi_product_form_sales_patch",
    "Sales Product Form - Malahi Patch",
    "sales_product_template_form_view",
    30,
)

# Purchase > Products
malahi_product_form_purchase_patch = _patch(
    "malahi_product_form_purchase_patch",
    "Purchase Product Form - Malahi Patch",
    "purchase_product_template_form_view",
    31,
)

# Inventory > Products. First patch this view has ever carried — its Purchase and
# Accounting tabs are hard-coded inline rather than inherited.
malahi_product_form_stock_patch = _patch(
    "malahi_product_form_stock_patch",
    "Stock Product Form - Malahi Patch",
    "stock_product_template_form_view",
    32,
)

# Accounting > Customers > Products
malahi_product_form_customer_patch = _patch(
    "malahi_product_form_customer_patch",
    "Customer Product Form - Malahi Patch",
    "customer_products_form_view",
    33,
)

# Accounting > Vendors > Products
malahi_product_form_vendor_patch = _patch(
    "malahi_product_form_vendor_patch",
    "Vendor Product Form - Malahi Patch",
    "vendor_products_form_view",
    34,
)
