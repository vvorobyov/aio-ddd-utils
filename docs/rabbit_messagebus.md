## class AsyncRabbitMessageBus

Данный класс является асинхронной реалицией шины доставки событий и RPC вызова команд
для сторонних сервисов посредством RabbitMQ.

### Инициализация

Коструктор класса принимает два обязательных параметра:
-`url` - валидный адрес подключения к серверу RabbitMQ
-`domain` - наименование домена сервиса осуществляющего инициализацию класса

**_Важно!_** К моменту запуска сервиса на сервере RabbitMQ должен быть создан
vhost соответсвующий значению параметра `domain` и заведен пользователь с именем
идентичным значению параметра `domain`.

**Свойства:**

- `domain: str` - Наименование текущего домена, указанное при инициализации

**Методы**

```python
def register_domains(self, *domains: str)
```

Метод регистрации наименований доменов внешних сервисов с которыми будет взаимодействовать класс,
в частности отправлять комманды. Для каждого зарегистрированного домена будет поднято подключение
к соответствующему vhost. Регистрация допускается только до запуска шины методом start.

- `domains: Iterable[str]` - перечень наименований доменов
- `loop: AbstractEventLoop` - EventLoop исползуемый при работе класса

```python
def register_event_handlers(self, event: t.Type[DomainEvent], *handlers: EventHandlerType)
```
Метод регистрации функций обработчиков событий.
Обработчик должен соответствовать следующей сигнатуре `t.Callable[[DomainEvent], t.Awaitable]`.

- `event` - класс сообщения
- handlers - перечень функций обработчиков

```python
def register_command_handler(self, command: t.Type[DomainCommand], handler: CommandHandlerType, *allowed_domains: str)
```
Метод регистрации функций обработчиков команд.
Обработчик должен соответствовать следующей сигнатуре `t.Callable[[DomainCommand], t.Awaitable[DomainCommandResponse]`.

- `command` - класс команды
- `handler` - класс обработчика. Не допускается регистрация нескольких обработчиков для одной команды. 
Повторный вызов приведет к замене ранее зарегистированного обработчика.
- `allowed_domains` - перечень доменов которым разрешается осуществлять вызов комманды

```python
def set_permission_for_command(self, command: t.Type[DomainCommand], *allowed_domains: str)
```
Метод добавление разрешения на вызов команды для указанных доменов.

- `command` - Класс команды
- `allowed_domains` - перечень доменов которым разрешается осуществлять вызов комманды


```python
def get_registered_domains(self) -> t.Iterable[str]
```
Метод получения перечня доменов 

```python
def set_loop(self, loop: AbstractEventLoop)
```
Метод назначения EventLoop который будет использоваться в рамках взаимодействия с rabbitmq.
_**Важно!**_ `EventLoop` должен быть назначен до запуска класса



```python
async def start(self)
```
Метод запуска. При запуске выполняются следующие действия:
- Создаются подключения к vhost зарегистрированных доменов
- Осуществляется регистрация queues и exchanges для каждого и доменов
- Настраивается подписка на очереди

```python
async def stop(self)
```
Метод остановки. При остановке выполняются следующие действия:
- Отменяются подписки на очереди
- Дожидается завершения исполнения всех запущенных задач
- Останавливается публикация событий
- Закрываются подключения

```python
async def handle(self, message: DomainMessage, timeout: float = None) -> t.Optional[DomainCommandResponse]:
```
Метод публикации сообщений и событий. Допускается использование только после запуска.
- `message` - сообщение (событие или команда)
- `timeout` - время ожидания исполнения комманды, после истечения которого будет поднято исключение `asyncio.TimeoutError`

При передаче в метод комманды в ответ будут возвращен объект `DomainCommandResponse`. Для вызовов с передечей событий ответ не предусмотрен.


### Пример использования

```python
import asyncio
from custom.messages import CustomCommand, CustomEvent
from dddmisc.messagebus.rabbitmq import AsyncRabbitMessageBus

async def custom_event_handler(event: CustomEvent):
    print(event)


def bootstrap() -> AsyncRabbitMessageBus:
    import os
    url = os.environ.get('DDD_RMQ_MESSAGEBUS_URL')
    mb = AsyncRabbitMessageBus(url=url, domain='example')
    mb.register_event_handlers(CustomEvent, custom_event_handler)
    return mb


async def send_command_to_custom(messagebus: AsyncRabbitMessageBus):
    cmd = CustomCommand(value=123)
    response = await messagebus.handle(cmd)
    print(response)
    

async def main(loop):
    messagebus = bootstrap()
    messagebus.set_loop(loop)
    await messagebus.start()
    await send_command_to_custom(messagebus)
    await messagebus.stop()
    
    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))

```
