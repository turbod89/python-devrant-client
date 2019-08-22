import urwid
import asyncio
from app.services import dev_rant_service, logging
from .generic_rant_list_widget import GenericRantList


class AllRantList(urwid.WidgetWrap):

    def __init__(self):

        self.widget = None
        self.body = GenericRantList(dev_rant_service.rants)

        self.create()
        super().__init__(self.widget)

    def subscribe_body_update(self):
        async def body_update_subscription_action(body, old_value):
            list_content = body.widget.contents['body'][0].body.contents

            refresh_widget_index = None
            get_more_widget_index = None
            for i, element in enumerate(list_content):
                if element is self.refresh_widget:
                    refresh_widget_index = i
                elif element is self.get_more_widget:
                    get_more_widget_index = i

            # asume refresh_widget_index < get_more_widget_index
            if get_more_widget_index is not None:
                list_content.pop(get_more_widget_index)

            if refresh_widget_index is not None:
                list_content.pop(refresh_widget_index)

            # apend again
            list_content.insert(0, self.refresh_widget)
            list_content.append(self.get_more_widget)

        self.body_update_subscription = self.body.update.subscribe(
            body_update_subscription_action, True)

    def create_refresh_widget(self):
        def f(button):
            asyncio.ensure_future(
                dev_rant_service.get_new_rants()
            )

        self.refresh_widget = urwid.Pile(
            [
                urwid.Divider(),
                urwid.Padding(
                    urwid.AttrMap(
                        urwid.Button(
                            'Refresh rants',
                            f
                        ),
                        'button normal',
                        'button select'
                    )
                ),
                urwid.Divider(),
                urwid.Divider(u'\u2500')
            ]
        )

    def create_get_more_widget(self):
        def f(button):
            asyncio.ensure_future(
                dev_rant_service.get_rants()
            )

        self.get_more_widget = urwid.Pile(
            [
                urwid.Divider(u'\u2500'),
                urwid.Divider(),
                urwid.Padding(
                    urwid.AttrMap(
                        urwid.Button(
                            'Get more rants',
                            f
                        ),
                        'button normal',
                        'button select'
                    )
                ),
                urwid.Divider(),
            ]
        )

    def create(self):

        self.create_get_more_widget()
        self.create_refresh_widget()

        self.widget = urwid.Frame(
            self.body,
            header=urwid.WidgetWrap(
                urwid.Pile(
                    [
                        urwid.AttrMap(
                            urwid.Text('Rants', align='center'),
                            'header'
                        ),
                        urwid.Divider(u'\u2500')
                    ]
                )
            ),
        )

        self.subscribe_body_update()
