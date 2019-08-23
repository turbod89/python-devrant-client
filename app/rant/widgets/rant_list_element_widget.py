import urwid
from app.shared.widgets import TimeAgoText
from app.services import router_service


class RantListElementWidget(urwid.Pile):

    def __init__(self, rant, focus_item=None):
        super().__init__([], focus_item=focus_item)
        self.update_rant(rant)

    def update_rant(self, rant):
        user_text = u"@{} (++{}) (#{})".format(
            rant.user.username,
            rant.user.score,
            rant.user.id,
        )

        comments_text_widget = urwid.Text(
            u"{} \U0001F4AC".format(
                rant.num_comments
            ),
            align='right'
        )

        time_ago_text_widget = TimeAgoText(
            from_time=rant.created_time,
            format=u"{} \U0001F552",
            align='right'
        )
        right_widget = urwid.Columns(
            [
                time_ago_text_widget,
                ('fixed', 8, comments_text_widget),
            ],
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

        def navigate_to_details(*args, **kwargs):
            router_service.navigate_to('/rant', rant)

        view_detail_btn = urwid.Button('View', navigate_to_details)

        subelements = [
            urwid.AttrMap(
                urwid.Columns(
                    [
                        urwid.Text(user_text),
                        right_widget
                    ],
                ),
                'rant_user'
            ),
            urwid.Divider(),
            urwid.Text("{}".format(rant.text)),
            urwid.Divider(),
        ] + image_widget_list + [
            rant_tags_widget,
            view_detail_btn,
            urwid.Divider(),
        ]

        self.contents = [
            (subelement, ('weight', 1))
            for subelement in subelements
        ]
