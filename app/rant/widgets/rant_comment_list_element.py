import urwid
from app.shared.widgets import TimeAgoText


class RantCommentListElementWidget(urwid.Pile):

    def __init__(self, rant, focus_item=None):
        super().__init__([], focus_item=focus_item)
        self.update_rant(rant)

    def update_rant(self, rant):
        user_text = u"@{} (++{}) (#{})".format(
            rant.user.username,
            rant.user.score,
            rant.user.id,
        )

        rant_header_text = u"(++{})".format(
            rant.score,
        )

        time_ago_text_widget = TimeAgoText(
            from_time=rant.created_time,
            format=u"{} \U0001F552",
            align='right'
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
                        ('fixed', len(rant_header_text) + 1, urwid.Text(rant_header_text)),
                        urwid.Text(user_text),
                        time_ago_text_widget
                    ],
                ),
                'rant_user'
            ),
            urwid.Divider(),
            urwid.Text("{}".format(rant.text)),
            urwid.Divider(),
        ] + image_widget_list + [
            urwid.Divider(),
        ]

        self.contents = [
            (subelement, ('weight', 1))
            for subelement in subelements
        ]
