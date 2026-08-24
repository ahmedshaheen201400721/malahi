# -*- coding: utf-8 -*-
# Menu items for malahi_extension module
from django.utils.translation import gettext as _

menu_dict = {
    # Sales > Products > Malahi Coupons
    "malahi_extension_sales_coupons": {
        "name": _("Malahi Coupons"),
        "icon": "Ticket",
        "module": "malahi_extension",
        "model": "malahi_extension.malahicoupon",
        "sequence": 6,
        "parent_key": "sales_main_menu_products",
        "allowed_groups": ["sales.users"],
    },
    # Inject the catalog sync button into the Sales > Products list view.
    # The base menu item has no "actions" key, so "replace" (which creates
    # the key) is used instead of "append" (which raises on a missing path).
    "malahi_extension_products_sync_action": {
        "_inherit": "sales_main_menu_products_product",
        "inheritance_operations": [
            {
                "operation": "replace",
                "target": "actions",
                "content": [
                    {
                        "name": "action_sync_malahi_catalog",
                        "string": _("Sync Malahi Products"),
                        "icon": "RefreshCw",
                        "type": "server",
                        "as": "button",
                        "variant": "primary",
                        "view_type": ["list"],
                        "selection_required": False,
                        "confirm_required": False,
                    },
                ],
            },
        ],
    },
}
