"""
Helper methods for push notifications from Studio.
"""

from contentstore.tasks import push_notification_task
from contentstore.models import PushNotificationConfig


def push_notification_enabled():
    """
    Returns whether the push notification feature is enabled.
    """
    return PushNotificationConfig.is_enabled()


def push_course_update(update, course_key):
    """
    Sends a push notification for the given update for the given course if
      (1) the feature is enabled and
      (2) push_notification is selected for the update
    """
    if push_notification_enabled() and update.get("push_notification_selected"):
        push_notification_task.delay(unicode(course_key), update["content"])
