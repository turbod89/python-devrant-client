import requests
import urllib
import json
from rx import operators as ops
from rx.subject import BehaviorSubject, Subject
from heapq import merge
from .auth_token import AuthToken
from .rant import Rant
from .draft_rant import DraftState
from ..logging import logging

logger = logging.getLogger(__name__)


class DevRantService():

    def __init__(self, *args, **kwargs):

        self.base_url = "https://devrant.com/api"

        self.base_params = {
            'app': 3,
        }

        self._rants = BehaviorSubject([])
        self.rants = self._rants.pipe(
            ops.map(self._on_update_rants),
        )
        self._rants_by_id = {}
        self.error = Subject()
        self.me = BehaviorSubject(None)
        self.auth_token = BehaviorSubject(None)
        self.is_logged = BehaviorSubject(False)

        self._subscribe_to_auth_token()
        self._load_cache()

    def __del__(self):
        self._rants.dispose()
        self.error.dispose()
        self.me.dispose()
        self.auth_token.dispose()
        self.is_logged.dispose()

    def _get_params(self, **kwargs):
        params = dict(self.base_params, **kwargs)
        return urllib.parse.urlencode(params)

    def _load_cache(self, filename='.cache.json'):
        try:
            fh = open(filename, 'r')
        except FileNotFoundError:
            self._write_cache(filename)
            self._load_cache(filename)
        else:
            try:
                cache_data = json.load(fh)
            except json.decoder.JSONDecodeError:
                pass
            else:
                cached_auth_token = cache_data.get('auth_token')

                if cached_auth_token is not None:
                    cached_auth_token = AuthToken(**cached_auth_token)
                    self.auth_token.on_next(cached_auth_token)
            fh.close()

    def _write_cache(self, filename='.cache.json'):

        cache_data = {}

        try:
            fh = open(filename, 'r')
            cache_data = json.load(fh)
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass
        else:
            fh.close()

        fh = open(filename, 'w')
        if self.auth_token.value is not None:
            cache_data['auth_token'] = self.auth_token.value.__dict__()

        json.dump(cache_data, fh)
        fh.close()

    def _delete_cache(self, filename='.cache.json'):
        fh = open(filename, 'w')
        json.dump({}, fh)
        fh.close()

    def _subscribe_to_auth_token(self):
        def action(value):
            # change is_logged value
            if self.is_logged.value and value.user_id is None:
                self.is_logged.on_next(False)
            elif not self.is_logged.value and value and value.user_id:
                self.is_logged.on_next(True)

            # save new auth_token
            self._write_cache()

        self._auth_token_subscription = self.auth_token.subscribe(action)
        return self

    def _on_update_rants(self, rants):
        self._rants_by_id = {
            rant.id: rant
            for rant in rants
        }
        return rants

    async def get_rants(self, limit=10):
        param_url = self._get_params(
            sort='recent',
            limit=limit,
            skip=len(self._rants.value)
        )

        response = requests.get(
            self.base_url + '/devrant/rants' + '?' + param_url)

        if response.status_code == 200:
            new_rants = json.loads(response.text)['rants']
            new_rants = [Rant(rant) for rant in new_rants]
            all_rants = list(merge(self._rants.value, new_rants,
                                   key=lambda x: x.id, reverse=True))
            self._rants.on_next(all_rants)
        else:
            self.error.on_next({
                'code': 1,
                'message': 'Unexpected status code',
                'response': response
            })

        return self

    async def get_rant_comments(self, rant):
        param_url = self._get_params()

        response = requests.get(
            self.base_url + '/devrant/rants/{}'.format(rant.id)
            + '?' + param_url
        )

        if response.status_code != 200:
            self.error.on_next({
                'code': 1,
                'message': 'Unexpected status code',
                'response': response
            })
            return self

        response_data = json.loads(response.text)
        new_rant_data = response_data['rant']
        comments_data = response_data['comments']
        rant.from_dict(new_rant_data)
        logger.debug(comments_data)
        rant.comments = [
            Rant({
                'id': comment_data['id'],
                'text': comment_data['body'],
                'score': comment_data['score'],
                'created_time': comment_data['created_time'],
                'user_id': comment_data['user_id'],
                'user_username': comment_data['user_username'],
                'user_score': comment_data['user_score'],
                'num_comments': 0,
                'attached_image': None,
                'tags': []
            })
            for comment_data in comments_data
        ]

        return self

    async def get_new_rants(self, skip=0, limit=10):

        if len(self._rants.value) == 0:
            return await self.get_rants()

        newest_actual_rant = self._rants.value[0]

        param_url = self._get_params(
            sort='recent',
            limit=limit,
            skip=skip
        )
        response = requests.get(
            self.base_url + '/devrant/rants' + '?' + param_url)

        if response.status_code == 200:
            new_rants = json.loads(response.text)['rants']
            new_rants = [Rant(rant) for rant in new_rants]
            new_rants.sort(key=lambda x: x.id, reverse=True)
            if new_rants[-1].id > newest_actual_rant.id:
                await self.get_new_rants(skip+limit, limit)
                newest_actual_rant = self._rants.value[0]

            new_rants = [
                rant
                for rant in new_rants
                if rant.id > newest_actual_rant.id
            ]

            all_rants = list(merge(new_rants, self._rants.value,
                                   key=lambda x: x.id, reverse=True))

            self._rants.on_next(all_rants)
        else:
            self.error.on_next({
                'code': 1,
                'message': 'Unexpected status code',
                'response': response
            })

        return self

    async def post_rant(self, draft_rant):

        headers = {
            "Host": "devrant.com",
            "Connection": "keep-alive",
            "Accept": "application/json",
            "Origin": "https://devrant.com",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://devrant.com/feed",
        }

        form_data = {
            **self.base_params,
            'rant': draft_rant.text,
            'token_id': self.auth_token.value.id,
            'token_key': self.auth_token.value.key,
            'user_id': self.auth_token.value.user_id,
            'tags': ', '.join(draft_rant.tags),
            'type': 1
        }

        draft_rant.response = requests.post(
            self.base_url + '/devrant/rants',
            headers=headers,
            data=form_data
        )

        draft_rant.state.on_next(DraftState.Sent)

        if draft_rant.response.status_code == 200:
            success = json.loads(draft_rant.response.text).get('success')
            if success:
                await self.get_new_rants()
                draft_rant.state.on_next(DraftState.Published)
            else:
                draft_rant.state.on_next(DraftState.Rejected)
                self.error.on_next({
                    'code': 2,
                    'message': 'Posted rant error',
                    'response': draft_rant.response
                })
        elif draft_rant.response.status_code == 400:
            draft_rant.state.on_next(DraftState.Rejected)
            self.error.on_next({
                'code': 2,
                'message': 'Posted rant error',
                'response': draft_rant.response
            })
        else:
            draft_rant.state.on_next(DraftState.Rejected)
            self.error.on_next({
                'code': 1,
                'message': 'Unexpected status code',
                'response': draft_rant.response
            })

    async def login(self, username, password):

        headers = {
            "Host": "devrant.com",
            "Connection": "keep-alive",
            "Accept": "application/json",
            "Origin": "https://devrant.com",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://devrant.com/",
        }
        response = requests.post(
            self.base_url + '/users/auth-token',
            headers=headers,
            data={
                **self.base_params,
                "username": username,
                "password": password,
            }
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                auth_token = AuthToken(**data.get('auth_token'))
                self.auth_token.on_next(auth_token)
                # await self.get_about_me()
            else:
                self.error.on_next({
                    'message': data.get('error')
                })

    def logout(self):
        self._delete_cache()
        self.auth_token.on_next(AuthToken())

    async def get_about_me(self):

        param_url = self._get_params(
            token_id=self.auth_token.value.id,
            token_key=self.auth_token.value.key
        )
        response = requests.get(
            self.base_url +
            '/users/{}'.format(self.auth_token.value.user_id) + '?' + param_url
        )
        return response
