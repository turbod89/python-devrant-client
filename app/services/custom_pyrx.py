
import asyncio


class Subscription():

    _next_id = 0

    def __init__(self, f, subscriptable):
        self.id = Subscription._next_id
        self.f = f
        self.subscriptable = subscriptable
        Subscription._next_id += 1

    def unsubscribe(self):
        del self.subscriptable.subscriptions[self.id]
        return self


class Subscriptable():

    def __init__(self, *args, **kwargs):
        self.subscriptions = {}
        self.value = None
        self._historic_values = []
        if len(args) >= 1:
            asyncio.ensure_future(self.change(args[0]))

    def subscribe(self, f, process_historic_values=False) -> Subscription:
        subscription = Subscription(f, self)
        self.subscriptions[subscription.id] = subscription

        if process_historic_values:
            async def g():
                for i, actual_value in enumerate(self._historic_values):
                    previous_value = self._historic_values[i-1] if i > 0 else None
                    await f(actual_value, previous_value)
            asyncio.ensure_future(g())

        return subscription

    async def change(self, new_value):
        for subscription_id, subscription in self.subscriptions.items():
            asyncio.ensure_future(subscription.f(new_value, self.value))
        self.value = new_value
        self._historic_values.append(self.value)
