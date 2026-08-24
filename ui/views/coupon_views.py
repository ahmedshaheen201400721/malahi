# -*- coding: utf-8 -*-
# List + form views for malahi_extension.MalahiCoupon
from django.utils.translation import gettext as _

malahi_coupon_list_view = {
    "key": "malahi_extension_coupon_list_view",
    "name": "Malahi Coupon List View",
    "model": "malahi_extension.malahicoupon",
    "view_type": "list",
    "priority": 10,
    "menu_item": "malahi_extension_sales_coupons",
    "module": "malahi_extension",
    "body": {
        "header": {
            "actions": [
                {
                    "name": "action_sync_malahi_catalog",
                    "string": _("Sync Malahi Coupons"),
                    "icon": "RefreshCw",
                    "type": "server",
                    "as": "button",
                    "variant": "primary",
                    "selection_required": False,
                    "confirm_required": False,
                },
            ],
        },
        "tree": {
            "fields": [
                {"name": "id", "widget": "number", "string": _("ID"), "visible": False},
                {"name": "code", "widget": "text", "string": _("Code")},
                {"name": "percentage", "widget": "number", "string": _("Percentage")},
                {"name": "last_synced_at", "widget": "datetime", "string": _("Last Synced")},
            ],
        },
    },
}

malahi_coupon_form_view = {
    "key": "malahi_extension_coupon_form_view",
    "name": "Malahi Coupon Form View",
    "model": "malahi_extension.malahicoupon",
    "view_type": "form",
    "priority": 10,
    "menu_item": "malahi_extension_sales_coupons",
    "module": "malahi_extension",
    "body": {
        "sheet": {
            "sections": [
                {
                    "title": "",
                    "groups": [
                        {
                            "title": "",
                            "fields": [
                                {"name": "code", "widget": "text", "string": _("Code"), "required": True},
                            ],
                        },
                        {
                            "title": "",
                            "fields": [
                                {"name": "percentage", "widget": "number", "string": _("Percentage")},
                                {"name": "last_synced_at", "widget": "datetime", "string": _("Last Synced"), "readonly": True},
                            ],
                        },
                    ],
                }
            ]
        }
    },
}
