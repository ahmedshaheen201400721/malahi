# -*- coding: utf-8 -*-
"""Celery tasks for malahi_extension.

The nightly schedule is a django_celery_beat PeriodicTask row (the project
runs DatabaseScheduler), registered by register_nightly_sync() — nothing is
added to project settings. The Malahi catalog regenerates daily at 00:00
Saudi time, so the sync runs at 01:00 Asia/Riyadh, safely after it.
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)

NIGHTLY_TASK_NAME = 'malahi-nightly-catalog-sync'


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def sync_malahi_catalog_task(self):
    """Nightly fetch of the Malahi catalog into products/providers/coupons."""
    from modules.malahi_extension.services import sync_malahi_catalog
    try:
        counts = sync_malahi_catalog()
        logger.info("Nightly Malahi catalog sync: %s", counts)
        return counts
    except Exception as exc:
        # The service already falls back to the static file; a failure here
        # means both sources were unreachable — retry 3x, 10 min apart.
        raise self.retry(exc=exc)


def register_nightly_sync():
    """Idempotently create/update the beat schedule row (daily 01:00 Riyadh)."""
    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0', hour='1',
        day_of_week='*', day_of_month='*', month_of_year='*',
        timezone='Asia/Riyadh',
    )
    task, created = PeriodicTask.objects.update_or_create(
        name=NIGHTLY_TASK_NAME,
        defaults={
            'task': 'modules.malahi_extension.tasks.sync_malahi_catalog_task',
            'crontab': schedule,
            'interval': None,
            'enabled': True,
        },
    )
    logger.info("Malahi nightly sync schedule %s", 'created' if created else 'updated')
    return task
