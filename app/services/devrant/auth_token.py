from datetime import datetime


class AuthToken():

    def __init__(self, *args, **kwargs):

        self.id = kwargs.get('id')
        self.key = kwargs.get('key')
        self.user_id = kwargs.get('user_id')
        self.expire_time = kwargs.get('expire_time', None)

        if self.expire_time is not None:
            self.expire_time = datetime.fromtimestamp(self.expire_time)

    def __dict__(self):
        res = {
            'id': self.id,
            'key': self.key,
            'user_id': self.user_id,
            'expire_time': None
        }

        if type(self.expire_time) is datetime:
            res['expire_time'] = self.expire_time.timestamp()

        return res
