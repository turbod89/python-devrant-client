import urwid
import asyncio
from app.services import dev_rant_service


class LoginWidget(urwid.WidgetWrap):

    def __init__(self, *args, **kwargs):
        self.widget = None
        self.parent_widget = kwargs.get('parent_widget')
        self.create()

        super().__init__(self.widget)

    def get_trigger_login(self):
        def login(button):
            username = self.username_edit.get_edit_text()
            password = self.password_edit.get_edit_text()
            asyncio.ensure_future(
                dev_rant_service.login(username, password)
            )
        return login

    def get_trigger_clear_form(self):
        def clear_form(button):
            self.username_edit.set_edit_text('')
            self.password_edit.set_edit_text('')
        return clear_form

    def create(self):

        send_btn_widget = urwid.Button('Send', self.get_trigger_login())
        clear_btn_widget = urwid.Button('Clear', self.get_trigger_clear_form())

        self.username_edit = urwid.Edit('Username: ', '')
        self.password_edit = urwid.Edit('Password: ', '', mask='*')

        self.widget = urwid.Frame(
            urwid.Filler(
                urwid.Pile([
                    urwid.LineBox(
                        self.username_edit
                    ),
                    urwid.LineBox(
                        self.password_edit
                    ),
                    urwid.Columns(
                        [
                            ('weight', 1, send_btn_widget),
                            ('weight', 1, clear_btn_widget),
                        ],
                        dividechars=1,
                        focus_column=None
                    )
                ])
            ),
            header=urwid.WidgetWrap(
                urwid.Pile(
                    [
                        urwid.AttrMap(
                            urwid.Text('Log In', align='center'),
                            'header'
                        ),
                        urwid.Divider(u'\u2500')
                    ]
                )
            ),
        )
