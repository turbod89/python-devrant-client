from rx.subject import BehaviorSubject


class DraftState(object):

    def __init__(self, *args, **kwargs):
        self._label = None if len(args) == 0 else args[0]

    def __str__(self):
        return "<State {}>".format(self._label)


DraftState.Created = DraftState('Created')
DraftState.Sent = DraftState('Sent')
DraftState.Published = DraftState('Published')
DraftState.Rejected = DraftState('Rejected')


class DraftRant(object):

    def __init__(self, *args, **kwargs):
        self.response = None
        self.state = BehaviorSubject(DraftState.Created)

        for arg in args:
            if type(arg) is dict:
                self.from_dict(arg)

        self.from_dict(kwargs)

    def from_dict(self, data):
        self.text = data.get('text', getattr(self, 'text', None))
        self.tags = data.get('tags', getattr(self, 'tags', []))
