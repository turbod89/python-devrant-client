import urwid
from app.services import dev_rant_service


class LogInLogOutBtn(urwid.WidgetWrap):

    def __init__(self, *args, **kwargs):

        self.widget = None
        self.parent_widget = kwargs.get('parent_widget')

        self.login_action = kwargs.get('login_action')

        def logout_action(*args, **kwargs):
            dev_rant_service.logout()
        self.logout_action = kwargs.get('logout_action', logout_action)

        self.create()
        super().__init__(self.widget)

    def _subscribe_to_is_logged(self, login_btn, logout_btn):
        def action(is_logged):
            if not is_logged:
                self.widget.contents[0] = (
                    login_btn, self.widget.contents[0][1]
                )
            else:
                self.widget.contents[0] = (
                    logout_btn, self.widget.contents[0][1]
                )

        self.subscription_is_logged = dev_rant_service.is_logged.subscribe(
            action)
        return self

    def create(self):

        login_btn = urwid.AttrMap(
            urwid.Button("Log In", self.login_action),
            'button normal',
            'button select'
        )

        logout_btn = urwid.AttrMap(
            urwid.Button("Log Out", self.logout_action),
            'button normal',
            'button select'
        )

        self.widget = urwid.Pile([login_btn])
        self._subscribe_to_is_logged(login_btn, logout_btn)
