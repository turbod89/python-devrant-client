import urwid
import asyncio
from app.services import router_service, logging
from app.rants.widgets import AllRantList
from app.rant.widgets import NewRantWidget, RantDetailWidget
from app.main_menu.widgets import MainMenu
from app.auth.widgets import LoginWidget
from app.services import dev_rant_service, logging
from .app_style import AppStyle


logger = logging.getLogger(__name__)


class AppWidget(AppStyle, urwid.WidgetWrap):

    def __init__(self, controller):

        self.widget = None

        self.main_menu = MainMenu(controller, parent_widget=self)
        self.rant_list = AllRantList()
        self.new_rant_widget = NewRantWidget(parent_widget=self)
        self.rant_detail_widget = RantDetailWidget(parent_widget=self)
        self.login_widget = LoginWidget(parent_widget=self)

        self.create()
        super().__init__(self.widget)

    def _subscribe_is_logged(self):
        show_rant_list = self.get_trigger_show_rant_list()
        show_login_widget = self.get_trigger_show_login_widget()

        def action(is_logged):
            logger.debug(is_logged)
            if is_logged:
                show_rant_list()
            else:
                show_login_widget()

        self._is_logged_subscritption = dev_rant_service.is_logged.subscribe(
            action)
        return self

    def _subscribe_error(self):
        async def f(error, last_error):
            logger.error(error)

        dev_rant_service.error.subscribe(f)

    def get_trigger_show_new_rant_widget(self):
        def show_new_rant_widget(*args, **kwargs):
            self.columns_widget.contents[2] = (
                self.new_rant_widget,
                self.columns_widget.contents[2][1]
            )
        return show_new_rant_widget

    def get_trigger_show_rant_list(self):
        def show_rant_list(*args, **kwargs):
            self.columns_widget.contents[2] = (
                self.rant_list,
                self.columns_widget.contents[2][1]
            )
        return show_rant_list

    def get_trigger_show_login_widget(self):
        def show_login_widget(*args, **kwargs):
            self.columns_widget.contents[2] = (
                self.login_widget,
                self.columns_widget.contents[2][1]
            )
        return show_login_widget

    def _register_route_rant_detail_widget(self):
        def show_rant_detail_widget(*args, **kwargs):

            if len(args) == 0:
                logging.error('Expected to receive a rant to navigate to.')

            self.rant_detail_widget.rant = args[0]
            asyncio.ensure_future(
                dev_rant_service.get_rant_comments(self.rant_detail_widget.rant)
            )

            self.columns_widget.contents[2] = (
                self.rant_detail_widget,
                self.columns_widget.contents[2][1]
            )

        router_service.register_route('/rant', show_rant_detail_widget)
        return self

    def create(self):

        self._register_route_rant_detail_widget()

        self.columns_widget = urwid.Columns(
            [
                ('fixed', 16, self.main_menu),
                ('fixed', 1,
                    urwid.AttrMap(urwid.SolidFill(u'\u2502'), 'line')),
                ('weight', 4, self.login_widget),
            ],
            dividechars=1,
            focus_column=None
        )

        w = urwid.Padding(
            self.columns_widget,
            ('fixed left', 0),
            ('fixed right', 0)
        )
        self.widget = urwid.AttrMap(w, 'body')
        self._subscribe_is_logged()
        self._subscribe_error()
