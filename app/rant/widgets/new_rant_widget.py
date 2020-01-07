import urwid
import asyncio
import json
from app.services import logging
from app.services import dev_rant_service
from app.services.devrant import DraftRant, DraftState

logger = logging.getLogger(__name__)


class NewRantWidget(urwid.WidgetWrap):

    def __init__(self, *args, **kwargs):
        self.widget = None
        self.parent_widget = kwargs.get('parent_widget')
        self.create()

        super().__init__(self.widget)

    def get_trigger_clear_new_rant(self):
        def clear_new_rant(button):
            self.rant_edit_widget.set_edit_text('')
            self.rant_tags_edit_widget.set_edit_text('')
        return clear_new_rant

    def create_send_button(self):

        if hasattr(self, 'send_btn_widget'):
            return getattr(self, 'send_btn_widget')

        def f(button):
            rant_text = self.rant_edit_widget.get_edit_text()
            rant_tags = self.rant_tags_edit_widget.get_edit_text()
            tags = [tag.strip() for tag in rant_tags.split(',')]

            draft_rant = DraftRant({
                'text': rant_text,
                'tags': tags
            })

            def g(new_value):

                if new_value is DraftState.Published:
                    self.clear_new_rant()
                    self.show_rant_list()
                elif new_value is DraftState.Rejected:
                    error_response_body = json.loads(
                        draft_rant.response.text)
                    logger.debug(error_response_body)

            draft_rant.state.subscribe(g)

            asyncio.ensure_future(
                dev_rant_service.post_rant(draft_rant)
            )

        self.send_btn_widget = urwid.Button('Send', f)

    def create(self):

        self.clear_new_rant = self.get_trigger_clear_new_rant()
        self.show_rant_list = self.parent_widget.get_trigger_show_rant_list()

        self.create_send_button()
        clear_btn_widget = urwid.Button(
            'Clear', self.get_trigger_clear_new_rant())

        self.rant_edit_widget = urwid.Edit(
            '', 'I hate my live because...', True)
        self.rant_tags_edit_widget = urwid.Edit('Tags: ', 'rant')

        self.widget = urwid.Frame(
            urwid.Filler(
                urwid.Pile([
                    urwid.LineBox(
                        self.rant_edit_widget
                    ),
                    urwid.LineBox(
                        self.rant_tags_edit_widget
                    ),
                    urwid.Columns(
                        [
                            ('weight', 1, self.send_btn_widget),
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
                            urwid.Text('New Rant', align='center'),
                            'header'
                        ),
                        urwid.Divider(u'\u2500')
                    ]
                )
            ),
        )
