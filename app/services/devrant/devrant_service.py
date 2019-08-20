import requests
import urllib
import json
import asyncio
from heapq import merge
from app.services.custom_pyrx import Subscriptable
from .auth_token import AuthToken
from .rant import Rant
from .draft_rant import DraftState
from ..logging import logging


class DevRantService():

    def __init__(self, *args, **kwargs):

        self.base_url = "https://devrant.com/api"

        self.base_params = {
            'app': 3,
        }

        self.rants = Subscriptable([])
        self.error = Subscriptable()
        self.me = Subscriptable()
        self.auth_token = Subscriptable()
        self.is_logged = Subscriptable(False)

        self._login_request = Subscriptable()

        self._subscribe_to_login_request()
        self._subscribe_to_auth_token()
        self._load_cache()

    def _get_params(self, **kwargs):
        params = dict(self.base_params, **kwargs)
        return urllib.parse.urlencode(params)

    def _load_cache(self, filename='.cache.json'):
        try:
            fh = open(filename, 'r')
        except FileNotFoundError:
            self._write_cache(filename)
            self._load_cache()
        else:
            try:
                cache_data = json.load(fh)
            except json.decoder.JSONDecodeError:
                pass
            else:
                cached_auth_token = cache_data.get('auth_token')

                if cached_auth_token is not None:
                    cached_auth_token = AuthToken(
                        **cached_auth_token)
                    asyncio.ensure_future(
                        self.auth_token.change(cached_auth_token)
                    )
            fh.close()

    def _write_cache(self, filename='.cache.json'):
        fh = open(filename, 'w')
        cache_data = {}
        if self.auth_token.value is not None:
            cache_data['auth_token'] = self.auth_token.value.__dict__()

        json.dump(cache_data, fh)
        fh.close()

    def _subscribe_to_login_request(self):
        async def action(response, *args, **kwargs):
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    auth_token = AuthToken(
                        **data.get('auth_token'))
                    await self.auth_token.change(auth_token)
                    await self.get_about_me()
                else:
                    self.error.change({
                        'message': data.get('error')
                    })

        self._login_request_subscription = self._login_request.subscribe(
            action)
        return self

    def _subscribe_to_auth_token(self):
        async def action(value, prev_value):
            # change is_logged value
            if self.is_logged.value and value.user_id is None:
                await self.is_logged.change(False)
            elif not self.is_logged.value and value.user_id is not None:
                await self.is_logged.change(True)

            # save new auth_token
            self._write_cache()

        self._auth_token_subscription = self.auth_token.subscribe(action)
        return self

    async def get_rants(self, limit=10):
        param_url = self._get_params(
            sort='recent',
            limit=limit,
            skip=len(self.rants.value)
        )

        response = requests.get(
            self.base_url + '/devrant/rants' + '?' + param_url)

        if response.status_code == 200:
            new_rants = json.loads(response.text)['rants']
            new_rants = [Rant(rant) for rant in new_rants]
            all_rants = list(merge(self.rants.value, new_rants,
                                   key=lambda x: x.id, reverse=True))
            await self.rants.change(all_rants)
        else:
            self.error.change({
                'code': 1,
                'message': 'Unexpected status code',
                'response': response
            })

        return self

    async def get_new_rants(self, skip=0, limit=10):

        if len(self.rants.value) == 0:
            return await self.get_rants()

        newest_actual_rant = self.rants.value[0]

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
                newest_actual_rant = self.rants.value[0]

            new_rants = [
                rant
                for rant in new_rants
                if rant.id > newest_actual_rant.id
            ]

            all_rants = list(merge(new_rants, self.rants.value,
                                   key=lambda x: x.id, reverse=True))

            await self.rants.change(all_rants)
        else:
            self.error.change({
                'code': 1,
                'message': 'Unexpected status code',
                'response': response
            })

        return self

    async def post_rant(self, draft_rant):

        logging.debug('here in dev_rant_service.post_rant')

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

        await draft_rant.state.change(DraftState.Sent)

        if draft_rant.response.status_code == 200:
            success = json.loads(draft_rant.response.text).get('success')
            if success:
                await self.get_new_rants()
                await draft_rant.state.change(DraftState.Published)
            else:
                await draft_rant.state.change(DraftState.Rejected)
                await self.error.change({
                    'code': 2,
                    'message': 'Posted rant error',
                    'response': draft_rant.response
                })
        elif draft_rant.response.status_code == 400:
            await draft_rant.state.change(DraftState.Rejected)
            await self.error.change({
                'code': 2,
                'message': 'Posted rant error',
                'response': draft_rant.response
            })
        else:
            await draft_rant.state.change(DraftState.Rejected)
            await self.error.change({
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

        await self._login_request.change(response)

    def logout(self):
        asyncio.ensure_future(
            self.auth_token.change(AuthToken())
        )

    async def get_about_me(self):

        param_url = self._get_params(
            token_id=self.auth_token.value.id,
            token_key=self.auth_token.value.key
        )
        response = requests.get(
            self.base_url + '/users/{}'.format(self.auth_token.value.user_id) + '?' + param_url)
