# -*- coding: utf-8 -*-
"""
Security groups for malahi_extension module

This file defines all security groups for the malahi_extension module.
Groups are synced to the database using the sync_groups management command.
"""

GROUPS = [
    {
        'name': 'Malahi_extension Users',
        'technical_name': 'malahi_extension.users',
        'category': 'Malahi_extension',
        'description': 'Access malahi_extension module',
    },
    {
        'name': 'Malahi_extension Admins',
        'technical_name': 'malahi_extension.admins',
        'category': 'Malahi_extension',
        'implied_groups': ['malahi_extension.users'],
        'description': 'Manage all malahi_extension module',
    }
]
