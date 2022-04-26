from dataclasses import dataclass

import pytest


def random_word() -> str:
    import random
    word_file = "/usr/share/dict/words"
    WORDS = open(word_file).read().splitlines()
    return random.choice(WORDS)


@pytest.fixture
def rabbit(load_environment):
    class Rabbit:
        def __init__(self, vhost: str = None, username: str = None, password: str = 'test'):
            from urllib.parse import ParseResult
            from environ import Env
            from aiorabbitmq_admin import AdminAPI

            env = Env()
            self.vhost = vhost or f'{random_word().lower()}-{random_word().lower()}'
            url: ParseResult = env.url('TEST_RABBIT_HOST')
            self.host = url.hostname
            self.port = env.int('TEST_RABBIT_AMQP_PORT')
            self.username = username or self.vhost
            self.password = password
            self.url = f'amqp://{self.username}:{self.password}@{self.host}:{self.port}/{self.vhost}'

            # url_port = (':' + str(url.port)) if url.port else ''
            adm_username = env.str('TEST_RABBIT_USERNAME')
            adm_password = env.str('TEST_RABBIT_PASSWORD')
            # self.client = AdminAPI(f"{self.host}{url_port}", adm_username, adm_password)
            self.client = AdminAPI(url.geturl(), auth=(adm_username, adm_password))

        async def __aenter__(self):
            await self.client.create_vhost(self.vhost)
            await self.client.create_user(self.username, self.password)
            # self.client.set_vhost_permissions(self.vhost, self.username, '.*', '.*', '.*')
            await self.client.create_user_permission(self.username, self.vhost, '.*', '.*', '.*')

            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.client.delete_user(self.vhost)
            await self.client.delete_vhost(self.vhost)

    return Rabbit
