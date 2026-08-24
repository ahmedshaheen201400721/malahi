# -*- coding: utf-8 -*-
"""
Access rights for malahi_extension module.
Format: [view, add, change, delete] as [0/1, 0/1, 0/1, 0/1]
"""

MODEL_PERMISSIONS = [
    # MalahiProvider
    {
        'model': 'malahi_extension.malahiprovider',
        'group': 'malahi_extension.users',
        'permissions': [1, 1, 1, 0],
    },
    {
        'model': 'malahi_extension.malahiprovider',
        'group': 'malahi_extension.admins',
        'permissions': [1, 1, 1, 1],
    },
    {
        'model': 'malahi_extension.malahiprovider',
        'group': 'sales.users',
        'permissions': [1, 0, 0, 0],
    },
    # MalahiCoupon
    {
        'model': 'malahi_extension.malahicoupon',
        'group': 'malahi_extension.users',
        'permissions': [1, 1, 1, 0],
    },
    {
        'model': 'malahi_extension.malahicoupon',
        'group': 'malahi_extension.admins',
        'permissions': [1, 1, 1, 1],
    },
    {
        'model': 'malahi_extension.malahicoupon',
        'group': 'sales.users',
        'permissions': [1, 0, 0, 0],
    },
]

# Permission patterns for convenience
PERMISSION_PATTERNS = {
    'NONE': [0, 0, 0, 0],           # No access
    'VIEW_ONLY': [1, 0, 0, 0],      # View only
    'MANAGE': [1, 1, 1, 0],         # Manage but no delete
    'FULL': [1, 1, 1, 1],           # Full access
}

# Example using patterns:
# {
#     'model': 'malahi_extension.modelname',
#     'group': 'malahi_extension.users',
#     'permissions': PERMISSION_PATTERNS['MANAGE'],
# }
