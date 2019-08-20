import urwid
from app.shared.widgets import LogInLogOutBtn

from app.services import dev_rant_service


class MainMenu(urwid.WidgetWrap):

    def __init__(self, controller, *args, **kwargs):
        self.controller = controller

        self.widget = None
        self.parent_widget = kwargs.get('parent_widget')

        self.create()
        super().__init__(self.widget)

    def create_new_rant_button(self):

        enabled_btn = urwid.AttrMap(
            urwid.Button(
                "New Rant",
                self.parent_widget.get_trigger_show_new_rant_widget()
            ),
            'button normal',
            'button select'
        )

        disabled_btn = urwid.WidgetDisable(
            urwid.AttrMap(
                urwid.Button("New Rant", None),
                'button disabled',
                'button disabled'
            )
        )

        self.new_rant_button = urwid.Pile([
            enabled_btn
        ])

        async def action(is_logged, prev_value):
            if is_logged:
                self.new_rant_button.contents[0] = (
                    enabled_btn,
                    self.new_rant_button.contents[0][1]
                )
            else:
                self.new_rant_button.contents[0] = (
                    disabled_btn,
                    self.new_rant_button.contents[0][1]
                )

        self._is_logged_subscription = dev_rant_service.is_logged.subscribe(
            action, True)

    def create(self):

        self.create_new_rant_button()

        login_logout_btn = LogInLogOutBtn(
            parent_widget=self,
            login_action=self.parent_widget.get_trigger_show_login_widget()
        )

        rant_list_btn = urwid.AttrMap(
            urwid.Button(
                "Rants", self.parent_widget.get_trigger_show_rant_list()),
            'button normal',
            'button select'
        )

        quit_btn = urwid.AttrMap(
            urwid.Button("Quit", self.controller.exit_program()),
            'button normal',
            'button select'
        )

        options = [
            rant_list_btn,
            self.new_rant_button,
            urwid.Divider(),
            login_logout_btn,
            quit_btn,
        ]

        self.widget = urwid.Frame(
            urwid.ListBox(
                urwid.SimpleListWalker(
                    [
                        urwid.AttrMap(option, None, focus_map='reversed')
                        for option in options
                    ]
                )
            ),

            header=urwid.WidgetWrap(
                urwid.Pile(
                    [
                        urwid.AttrMap(
                            urwid.Text('Main menu', align='center'),
                            'header'
                        ),
                        urwid.Divider(u'\u2500')
                    ]
                )
            ),
            focus_part='body'
        )
