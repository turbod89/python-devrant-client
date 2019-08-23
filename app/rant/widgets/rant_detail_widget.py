import urwid
from app.services import logging


class RantDetailWidget(urwid.WidgetWrap):

    def __init__(self, *args, **kwargs):
  
        self._rant = None

        self.parent_widget = kwargs.pop('parent_widget', None)
        self.create(*args, **kwargs)
        super().__init__(self.widget)

    @property
    def rant(self):
        return self._rant

    @rant.setter
    def rant(self, value):
        self._rant = value
        self.update_rant()

    def update_rant(self):
        '''
        self.header_title.set_text(
            'Rant Detail of {}'.format(self._rant.user.username)
        )
        '''
        logging.debug(self._rant)
        
        return self

    def create(self, *args, **kwargs):
        self.header_title = urwid.Text('Rant Detail', align='center')
        self.widget = urwid.Frame(
            urwid.Text('Rant Detail Body'),
            header=urwid.WidgetWrap(
                urwid.Pile(
                    [
                        urwid.AttrMap(
                            self.header_title,
                            'header'
                        ),
                        urwid.Divider(u'\u2500')
                    ]
                )
            ),
        )