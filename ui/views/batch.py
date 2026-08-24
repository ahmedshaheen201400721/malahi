# -*- coding: utf-8 -*-
# View batches from malahi_extension into other modules' views
from django.utils.translation import gettext as _

sales_settings_malahi_batch = {
    "key": "sales_settings_malahi_batch",
    "name": "Sales Settings - Malahi Invitations",
    "view_type": "settings",
    "priority": 20,
    "inherit_mode": "extension",
    "inherit_id": "sales_settings",
    "module": "sales",
    "inheritance_operations": [
        {
            "operation": "append",
            "target": "sections.0.groups",
            "content": {
                "title": _("Malahi"),
                "fields": [
                    {
                        "name": "number_of_invitations",
                        "string": _("Number of Invitations"),
                        "description": "مكافأة دعوة الأصدقاء: ٢٠ ريال تُضاف للمحفظة بعد ما يكمل 8 أشخاص التسجيل، وبشرط أن كل واحد منهم يحمّل التطبيق ويسجّل لأول مرة. اللي عنده حساب قديم ما يُحتسب.",
                        "widget": "number",
                        "default": 8,
                    },
                ],
            },
        }
    ],
}
