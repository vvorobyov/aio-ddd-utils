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
        def __init__(self, vhost: str = None, username: str = None, password: str = None):
            from urllib.parse import ParseResult
            from environ import Env
            from pyrabbit.api import Client

            env = Env()
            self.vhost = vhost or f'{random_word().lower()}-{random_word().lower()}'
            url: ParseResult = env.url('TEST_RABBIT_HOST')
            self.host = url.hostname
            self.port = env.int('TEST_RABBIT_AMQP_PORT')
            self.username = username or self.vhost
            self.password = password or 'test'
            url_port = (':' + str(url.port)) if url.port else ''
            adm_username = env.str('TEST_RABBIT_USERNAME')
            adm_password = env.str('TEST_RABBIT_PASSWORD')
            self._client = Client(f"{self.host}{url_port}",
                                  adm_username, adm_password)

        def __enter__(self):
            self._client.create_vhost(self.vhost)
            self._client.create_user(self.username, self.password)
            self._client.set_vhost_permissions(self.vhost, self.username, '.*', '.*', '.*')
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._client.delete_user(self.vhost)
            self._client.delete_vhost(self.vhost)

    return Rabbit
