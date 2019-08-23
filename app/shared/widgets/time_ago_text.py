import asyncio
import urwid
from datetime import datetime

from app.services import Subscriptable, Subscription, logging


def _time_ago(time=False):

    # source: https://stackoverflow.com/questions/1551382/user-friendly-time-format-in-python

    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return None, 0

    if day_diff == 0:
        if second_diff < 10:
            return "just now", 10
        if second_diff < 60:
            return "{} seconds ago".format(second_diff), 1
        if second_diff < 120:
            return "a minute ago", 60
        if second_diff < 3600:
            return "{} minutes ago".format(second_diff // 60), 5
        if second_diff < 7200:
            return "an hour ago", 3600
        if second_diff < 86400:
            return "{} hours ago".format(second_diff // 3600), 3600
    if day_diff == 1:
        return "Yesterday", 86400
    if day_diff < 7:
        return "{} days ago".format(day_diff), 7*86400
    if day_diff < 31:
        return "{} weeks ago".format(day_diff // 7), 31*86400
    if day_diff < 365:
        return "{} months ago".format(day_diff // 30), 365*86400
    return "{} years ago".format(day_diff // 365), None


class TimeAgoText(urwid.WidgetWrap):

    def __init__(self, *args, **kwargs):

        self.from_time = None

        new_args = list(args)

        if len(new_args) > 0:
            self.from_time = new_args[0]
            new_args = new_args[1:]

        self.format = kwargs.pop('format', '{}')
        self.from_time = kwargs.pop('from_time', self.from_time)
        self.default_text = kwargs.pop('default_text', '')

        self.widget = None
        self.parent_widget = kwargs.pop('parent_widget', None)

        self.time_ago_S = Subscriptable()
        self._time_ago_subscription = None

        self.create(*new_args, **kwargs)
    
        super().__init__(self.widget)

    def _subscribe_to_time_ago(self):

        async def subscription_action(new_value, old_value):
            time_ago_text = self.format.format(
                new_value
            )
            self.widget.set_text(time_ago_text)

        self._time_ago_subscription = self.time_ago_S.subscribe(
            subscription_action)
        return self

    def _create_counter_task(self):

        async def recursive_waiter():
            text, time = _time_ago(self.from_time)
            if text is None:
                text = self.default_text
            await self.time_ago_S.change(text)
            await asyncio.sleep(time)

            if time is not None:
                await recursive_waiter()

        asyncio.ensure_future(recursive_waiter())

    def create(self, *args, **kwargs):
        self.widget = urwid.Text(self.default_text, *args, **kwargs)
        self._subscribe_to_time_ago()
        self._create_counter_task()
