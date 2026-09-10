# -*- coding: utf-8 -*-
"""List + form views for malahi_extension.MalahiProvider.

The providers table had no menu item and no views, so 53 synced venues were
invisible in the UI. Everything the nightly catalog sync owns (name, external_id,
terms, cities) is shown read-only: the sync overwrites those fields on every run,
so an edit here would silently disappear that night. `partner` is the one
editable field — it is the business counterpart used when transacting with the
venue, and the sync deliberately never writes to it.
"""
from django.utils.translation import gettext as _

malahi_provider_list_view = {
    "key": "malahi_extension_provider_list_view",
    "name": "Malahi Provider List View",
    "model": "malahi_extension.malahiprovider",
    "view_type": "list",
    "priority": 10,
    "menu_item": "malahi_extension_sales_providers",
    "module": "malahi_extension",
    "body": {
        "header": {
            "actions": [
                {
                    "name": "action_sync_malahi_catalog",
                    "string": _("Sync Malahi Catalog"),
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
                {"name": "name", "widget": "text", "string": _("Venue")},
                {"name": "external_id", "widget": "number", "string": _("Malahi ID")},
                {
                    "name": "cities",
                    "widget": "relation",
                    "multiSelect": True,
                    "string": _("Cities"),
                },
                {
                    "name": "partner",
                    "widget": "relation",
                    "multiSelect": False,
                    "string": _("Supplier"),
                },
            ],
        },
    },
}

malahi_provider_form_view = {
    "key": "malahi_extension_provider_form_view",
    "name": "Malahi Provider Form View",
    "model": "malahi_extension.malahiprovider",
    "view_type": "form",
    "priority": 10,
    "menu_item": "malahi_extension_sales_providers",
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
                                {
                                    "name": "name",
                                    "widget": "text",
                                    "string": _("Venue"),
                                    "readonly": True,
                                    "help": _("Synced from the Malahi catalog"),
                                },
                                {
                                    # The sync matches providers on this value;
                                    # editing it orphans the record and the next
                                    # run creates a duplicate beside it.
                                    "name": "external_id",
                                    "widget": "number",
                                    "string": _("Malahi ID"),
                                    "readonly": True,
                                },
                            ],
                        },
                        {
                            "title": "",
                            "fields": [
                                {
                                    "name": "cities",
                                    "widget": "relation",
                                    "multiSelect": True,
                                    "string": _("Cities"),
                                    "readonly": True,
                                    "help": _("Cities this venue operates in, from the Malahi catalog"),
                                },
                                {
                                    "name": "partner",
                                    "widget": "relation",
                                    "multiSelect": False,
                                    "string": _("Supplier"),
                                    "placeholder": _("Select supplier..."),
                                    "help": _("Partner record used when transacting with this venue"),
                                },
                            ],
                        },
                    ],
                },
                {
                    "title": _("Terms & Conditions"),
                    "groups": [
                        {
                            "title": "",
                            "fields": [
                                {
                                    "name": "terms",
                                    "widget": "textarea",
                                    "string": _("Terms"),
                                    "readonly": True,
                                },
                            ],
                        },
                    ],
                },
            ]
        }
    },
}
