import urwid
import asyncio, sys
from datetime import datetime
from app.shared.widgets import TimeAgoText
from app.services import Subscriptable, logging


class RantListElement(urwid.Pile):
    pass


class GenericRantList(urwid.WidgetWrap):

    def __init__(self, rants_subscriptable):

        self.widget = None
        self.rants_subscriptable = rants_subscriptable
        self.rants = []
        self.update = Subscriptable()

        self.create()
        super().__init__(self.widget)

    def update_rant_list_element(self, element, rant):

        user_text = u"@{} (++{}) (#{})".format(
            rant.user.username,
            rant.user.score,
            rant.user.id,
        )

        comments_text_widget = urwid.Text( 
            u"{} \U0001F4AC".format(
                rant.num_comments
            ),
            align='right'
        )

        time_ago_text_widget = TimeAgoText(
            from_time=rant.created_time,
            format=u"{} \U0001F552",
            align='right'
        )
        right_widget = urwid.Columns(
            [
                time_ago_text_widget,
                ('fixed', 8, comments_text_widget),
            ],
        )

        rant_tags_widget = urwid.GridFlow(
            [
                urwid.AttrMap(
                    urwid.Text('{}'.format(tag)),
                    'rant_tag'
                )
                for tag in rant.tags
            ],
            10,
            1,
            1,
            'left'
        )

        image_widget_list = []

        if rant.has_image:
            image_widget_list = [
                urwid.AttrMap(
                    urwid.Text("{}".format(rant.image.url)),
                    'link'
                ),
                urwid.Divider()
            ]

        subelements = [
            urwid.AttrMap(
                urwid.Columns(
                    [
                        urwid.Text(user_text),
                        right_widget
                    ],
                ),
                'rant_user'
            ),
            urwid.Divider(),
            urwid.Text("{}".format(rant.text)),
            urwid.Divider(),
        ] + image_widget_list + [
            rant_tags_widget,
            urwid.Divider(),
        ]

        element.contents = [
            (subelement, ('weight', 1))
            for subelement in subelements
        ]

        return self

    def create_rant_list_element(self, rant):

        element = RantListElement([])

        self.update_rant_list_element(element, rant)

        return element

    def create_list_box(self):

        elements = []
        for i, rant in enumerate(self.rants):
            if i > 0:
                elements.append(
                    urwid.Divider(u'\u2500')
                )

            element = self.create_rant_list_element(rant)
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
        async def action(new_value, old_value):
            self.rants = new_value

            simple_list_walker = self.widget.contents['body'][0].body
            i = 0
            j = 0

            # update existent
            while i < len(simple_list_walker) and j < len(new_value):
                element = simple_list_walker[i]
                rant = new_value[j]
                if type(element) is not RantListElement:
                    i += 1
                else:
                    self.update_rant_list_element(element, rant)
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
                    self.create_rant_list_element(rant)
                )
                i += 1
                j += 1

            # delete excedent
            simple_list_walker.contents[:i]

            await self.update.change(self)

        self.rant_list_subscription = self.rants_subscriptable.subscribe(
            action, True)
