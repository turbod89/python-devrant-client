import urwid
from app.services import Subscriptable


class GenericRantList(urwid.WidgetWrap):

    def __init__(self, rants_subscriptable):

        self.widget = None
        self.rants_subscriptable = rants_subscriptable
        self.rants = []
        self.update = Subscriptable()

        self.create()
        super().__init__(self.widget)

    def create_list_box(self):

        elements = []
        for i, rant in enumerate(self.rants):
            if i > 0:
                elements.append(
                    urwid.Divider(u'\u2500')
                )

            user_text = u"@{} (++{}) (#{})".format(
                rant.user.username,
                rant.user.score,
                rant.user.id,
            )

            comments_text = u"{} \U0001F4AC".format(
                rant.num_comments
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

            elements.append(
                urwid.Pile(
                    [
                        urwid.AttrMap(
                            urwid.Columns(
                                [
                                    urwid.Text(user_text),
                                    urwid.Text(comments_text, align='right')
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
                )
            )

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
            self.widget.contents['body'] = (self.create_list_box(), None)
            await self.update.change(self)

        self.rant_list_subscription = self.rants_subscriptable.subscribe(
            action, True)
