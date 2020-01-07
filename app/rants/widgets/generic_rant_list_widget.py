import urwid
from app.rant.widgets import RantListElementWidget
from rx.subject import BehaviorSubject


class GenericRantList(urwid.WidgetWrap):

    def __init__(self, rants_subscriptable):

        self.widget = None
        self.rants_subscriptable = rants_subscriptable
        self.rants = []
        self.update = BehaviorSubject(self)
        self._subscriptions = []

        self.create()
        super().__init__(self.widget)

    def __del__(self):
        self.update.dispose()
        for subscription in self._subscritpions:
            subscription.unsubscribe()

    def create_list_box(self):

        elements = []
        for i, rant in enumerate(self.rants):
            if i > 0:
                elements.append(
                    urwid.Divider(u'\u2500')
                )

            element = RantListElementWidget(rant)
            elements.append(element)

        list_box = urwid.ListBox(
            urwid.SimpleListWalker(
                elements
            )
        )

        return list_box

    def create(self):
        self.widget = urwid.Frame(
            self.create_list_box()
        )
        self._subscribe_rant_list()

    def _subscribe_rant_list(self):
        def action(new_value):
            self.rants = new_value

            simple_list_walker = self.widget.contents['body'][0].body
            i = 0
            j = 0

            # update existent
            while i < len(simple_list_walker) and j < len(new_value):
                element = simple_list_walker[i]
                rant = new_value[j]
                if type(element) is not RantListElementWidget:
                    i += 1
                else:
                    element.update_rant(rant)
                    i += 1
                    j += 1

            # append new ones
            while j < len(new_value):
                rant = new_value[j]
                if i > 0:
                    simple_list_walker.append(
                        urwid.Divider(u'\u2500')
                    )
                    i += 1
                simple_list_walker.contents.append(
                    RantListElementWidget(rant)
                )
                i += 1
                j += 1

            # delete excedent
            simple_list_walker.contents[:i]

            self.update.on_next(self)

        self._subscriptions.append(
            self.rants_subscriptable.subscribe(action)
        )
