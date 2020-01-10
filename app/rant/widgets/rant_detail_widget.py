import urwid
from app.services import logging
from app.shared.widgets import TimeAgoText
from app.rant.widgets.rant_comment_list_element import RantCommentListElementWidget

logger = logging.getLogger(__name__)


class RantDetailWidget(urwid.WidgetWrap):

    def __init__(self, *args, **kwargs):

        self._rant = None
        self._rant_update_subscription = None
        self.parent_widget = kwargs.pop('parent_widget', None)
        self.create(*args, **kwargs)
        super().__init__(self.widget)

    @property
    def rant(self):
        return self._rant

    @rant.setter
    def rant(self, value):
        self._rant = value
        if self._rant_update_subscription:
            self._rant_update_subscription.dispose()
        self._rant_update_subscription = self._rant.update_S.subscribe(
            lambda x: self.update_rant()
        )
        self.update_rant()

    def update_rant(self):
        if self._rant:
            self.update_rant_header()
            self.update_rant_body()
        return self

    def create_rant_header(self):
        self.create_rant_header_timeago()
        self.rant_header = urwid.Pile(
            [
                urwid.Text('', align='center'),
                self.rant_header_timeago
            ]
        )

    def update_rant_header(self):
        self.update_rant_header_timeago()
        self.rant_header.contents[0][0].set_text(
            "Rant (++{}) (#{}) Detail of @{} (++{}) (#{})".format(
                self._rant.score,
                self._rant.id,
                self._rant.user.username,
                self._rant.user.score,
                self._rant.user.id,
            )
        )
        del self.rant_header.contents[1]
        self.rant_header.contents.append((
            self.rant_header_timeago,
            ('weight', 1)
        ))

    def create_rant_header_timeago(self):
        self.rant_header_timeago = TimeAgoText(
            format=u"{} \U0001F552",
            align='center'
        )

    def update_rant_header_timeago(self):
        self.rant_header_timeago = TimeAgoText(
            from_time=self._rant.created_time,
            format=u"{} \U0001F552",
            align='center'
        )

    def create_rant_body(self):

        self.create_rant_body_text()
        self.create_rant_body_comments()
        self.create_rant_body_tags()
        self.create_rant_body_image()

        self.rant_body = urwid.ListBox(
            urwid.SimpleListWalker(
                [
                    self.rant_body_text,
                    self.rant_body_image,
                    self.rant_body_tags,
                    self.rant_body_comments,
                ]
            )
        )
        return self

    def update_rant_body(self):
        self.update_rant_body_text()
        self.update_rant_body_tags()
        self.update_rant_body_comments()
        self.update_rant_body_image()
        return self

    def create_rant_body_text(self):
        self.rant_body_text = urwid.Pile([
            urwid.Divider()
        ])
        return self

    def update_rant_body_text(self):
        subelements = [
            urwid.Divider(),
            urwid.Text(self._rant.text)
        ]
        self.rant_body_text.contents = [
            (subelement, ('weight', 1))
            for subelement in subelements
        ]

    def create_rant_body_tags(self):
        self.rant_body_tags = urwid.Pile([
            urwid.Divider(),
            urwid.GridFlow([], 10, 1, 1, 'left'),
        ])

    def update_rant_body_tags(self):

        self.rant_body_tags.contents.pop(-1)
        self.rant_body_tags.contents.append(
            (
                urwid.GridFlow([
                    urwid.AttrMap(
                        urwid.Text('{}'.format(tag)),
                        'rant_tag'
                    )
                    for tag in self._rant.tags
                ], 10, 1, 1, 'left'),
                ('weight', 1)
            )
        )
        return self

    def create_rant_body_image(self):
        self.rant_body_image = urwid.Pile([
            urwid.Divider()
        ])
        return self

    def update_rant_body_image(self):
        subelements = [urwid.Divider()]
        if self._rant.has_image:
            subelements = [
                urwid.Divider(),
                urwid.AttrMap(
                    urwid.Text("{}".format(self._rant.image.url)),
                    'link'
                ),
                urwid.Divider()
            ]
        self.rant_body_image.contents = [
            (subelement, ('weight', 1))
            for subelement in subelements
        ]
        return self

    def create_rant_body_comments(self):

        self.rant_body_comments = urwid.Pile(
            [
                urwid.Divider(u'\u2500'),
            ]
        )
        return self

    def update_rant_body_comments(self):
        logger.debug(self._rant.comments)

        subelements = [
            urwid.Divider(u'\u2500'),
        ]

        if self._rant.comments:
            for comment in self._rant.comments:
                subelements.append(RantCommentListElementWidget(comment))

        self.rant_body_comments.contents = [
            (subelement, ('weight', 1))
            for subelement in subelements
        ]

    def create(self, *args, **kwargs):
        self.create_rant_header()
        self.create_rant_body()

        self.widget = urwid.Frame(
            self.rant_body,
            header=urwid.WidgetWrap(
                urwid.Pile(
                    [
                        urwid.AttrMap(self.rant_header, 'header'),
                        urwid.Divider(u'\u2500')
                    ]
                )
            ),
            focus_part='body'
        )
