import math
from datetime import datetime
from rx.subject import Subject
from ..logging import logging

logger = logging.getLogger(__name__)


def to_date(timestamp, *args, **kwargs):
    return datetime.fromtimestamp(timestamp)


def from_date(date, *args, **kwargs):
    return math.floor(date.timestamp())


def to_user(user_id, data, *args, **kwargs):
    return type(
        'User',
        (object,),
        {
            'id': data.get('user_id'),
            'username': data.get('user_username'),
            'score': data.get('user_score'),
        }
    )


def from_user(user, rant, data, *args, **kwargs):
    data['user_username'] = user.username
    data['user_score'] = user.score
    return user.id


def to_image(image_data, data, rant, *args, **kwargs):
    rant.has_image = type(image_data) is dict
    if rant.has_image:
        return type(
            'Image',
            (object,),
            {
                'url': image_data.get('url'),
                'width': image_data.get('width'),
                'height': image_data.get('height'),
            }
        )

    return None


def from_image(image, rant, data, *args, **kwargs):
    if not rant.has_image:
        return ''

    return {
        'url': image.url,
        'height': image.height,
        'width': image.width
    }


field_mapping = (
    ('id', 'id', None, None),
    ('tags', 'tags', None, None),
    ('text', 'text', None, None),
    ('score', 'score', None, None),
    ('edited', 'is_edited', None, None),
    ('num_comments', 'num_comments', None, None),
    ('comments', 'comments', None, None),
    ('user_id', 'user', to_user, from_user),
    ('attached_image', 'image', to_image, from_image),
    ('created_time', 'created_time', to_date, from_date),
)


class Rant(object):

    fields = [f[1] for f in field_mapping]

    def __init__(self, *args, **kwargs):
        self._prevent_update = False
        self._update_S = Subject()
        for arg in args:
            if type(arg) is dict:
                self.from_dict(arg)
        self.from_dict(kwargs)

    @property
    def update_S(self):
        return self._update_S

    def __setattr__(self, name, value):
        if hasattr(self, '_prevent_update') and not self._prevent_update\
                and name in Rant.fields:
            old_value = getattr(self, name, None)
            return_value = super().__setattr__(name, value)
            if old_value != value:
                self._update_S.on_next({
                    'type': 'Update',
                    'prev': {
                        name: old_value
                    },
                    'current': {
                        name: value
                    }
                })
            return return_value
        else:
            return super().__setattr__(name, value)

    def from_dict(self, data):

        _prevent_update = self._prevent_update
        self._prevent_update = True

        update_value = {
            'type': 'Update',
            'prev': {},
            'current': {}
        }

        for original_field, final_field, transformation, _ in field_mapping:

            if original_field not in data:
                if not hasattr(self, final_field):
                    setattr(self, final_field, None)
                else:
                    # keep actual value
                    pass
            elif transformation is None:
                old_value = getattr(self, final_field, None)
                new_value = data.get(original_field)
                setattr(self, final_field, new_value)
                if old_value != new_value:
                    update_value['prev'][final_field] = old_value
                    update_value['current'][final_field] = new_value
            else:
                old_value = getattr(self, final_field, None)
                new_value = transformation(
                    data.get(original_field),
                    data,
                    self
                )
                setattr(
                    self,
                    final_field,
                    new_value
                )
                if old_value != new_value:
                    update_value['prev'][final_field] = old_value
                    update_value['current'][final_field] = new_value

        self._update_S.on_next(update_value)

        self._prevent_update = _prevent_update

        return self

    def to_dict(self):

        data = {}

        for original_field, final_field, _, inverse_transformation\
                in field_mapping:

            if not hasattr(self, final_field)\
                    or getattr(self, final_field) is None:
                data[original_field] = None
            elif inverse_transformation is None:
                data[original_field] = getattr(self, final_field)
            else:
                data[original_field] = inverse_transformation(
                    getattr(self, final_field),
                    self,
                    data
                )

        return data

    def __dict__(self):
        return self.to_dict()

    def __str__(self):
        return str(self.to_dict())
