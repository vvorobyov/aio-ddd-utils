from uuid import uuid4# Messages

Пакет предоставляет базовые классы сообщений:

- `DDDMessage` - Базовый класс для классов `DDDCommand` и `DDDEvent`. Не используется для наследования.
- `DDDCommand` - Базовый класс для создания классов команд домена
- `DDDEvent` - Базовый класс для создания классов событий домена
- `DDDStructure` - Базовый класс для описания объектов структур необходимых для описания сложных объектов команд и
  запросов
- `DDDResponse` - Класс ответа на комманды

## События и Команды

В базовых классах `DDDCommand` и `DDDEvent` реализованы следующие методы и атрибуты:

- `__reference__: UUID` - Уникальный идентификатор команды/события. Генерируется в момент создания.
- `__timestamp__: float` - Время создания команды/события. Генерируется в момент создания.
- `__domain__: str` - Наименование домена которому принадлежит команда/событие.
- `load(cls, data: dict)` - Метод класса десериализации объекта команды/события из словаря.
- `load(cls, data: str)` - Метод класса десериализации объекта команды/события из `json` строки.
- `dump(self) -> dict` - Метод сераилизации объекта команды/события в словарь содержащий простые типа данных
- `dumps(self) -> str` - Метод сераилизации объекта команды/события в `json` строку

Все атрибуты классов команд и событий являются `frozen` и поднимают исключение `FrozenInstanceError` при попытке их
изменения

### Метаданные команд и событий

Метаданные команд и событий используются для структурирования классов и определения их поведения.

Для описания метаданных при описании класса добавляются атрибут-класс `Meta`, который может содержать следующие
атрибуты:

| Наименование  | Тип     | Описание                                                                                                                                                                                                                                                       |
|---------------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `domain`      | `str`   | Наименование домена к которому относится класс команды/события. Данный атрибут наследуется от родителя и не может быть переопределен в дочерних класса                                                                                                         |
| `is_baseclass` | `bool`  | Определяет, что класс является основой для дочерних классов команд/событий и не будет использован для создания объектов. Классы с установленным флагом в значение `True` не регистрируются в реестре сообщений. Значение по умолчанию `False`. Не наследуется. |

### Атрибуты команд и событий

Для определения дополнительных атрибутов для команд и событий используются классы дескрипторы из
пакета `dddmisc.messages.fields`.

**Примеры**

```python
from uuid import uuid4, UUID

from dddmisc.messages import DDDCommand, fields


class BaseCustomDomainCommand(DDDCommand):
  str_attr = fields.String()

  class Meta:
    domain = 'custom-domain'
    is_baseclass = True


class AnyCommand(BaseCustomDomainCommand):
  int_attr = fields.Integer()
  nullable_attr = fields.String(nullable=True)
  default_attr = fields.Float(default=123.45)

  class Meta:
    domain = 'other-domain'  # Пример не возможности переопределения домена


assert AnyCommand.__domain__ == 'custom-domain'

cmd = AnyCommand(str_attr='ABC', int_attr=1)  # Пример создания команды
assert isinstance(cmd.__reference__, UUID)
assert isinstance(cmd.__timestamp__, float)
assert cmd.str_attr == 'ABC'
assert cmd.int_attr == 1
assert cmd.nullable_attr is None
assert cmd.default_attr == 123.45

# Сериализации команды
assert cmd.dump() == {
  '__reference__': str(cmd.__reference__),
  '__timestamp__': cmd.__timestamp__,
  'data': {
    'str_attr': 'ABC',
    'int_attr': 1,
    'nullable_attr': None,
    'default_attr': 123.45
  }
}

assert cmd == AnyCommand.loads(cmd.dumps())  # Десериализация команды
```

# Структуры данных

Структуры данных используются для описания сложных структур данных в составе команд комманд и событий домена.
Все структуры данных должны унаследованы от базового класса `DDDStructure`.

В базовом классе `DDDStructure` реализованы следующие методы и атрибуты:

- `load(cls, data: dict)` - Метод класса десериализации объекта команды/события из словаря.
- `load(cls, data: str)` - Метод класса десериализации объекта команды/события из `json` строки.
- `dump(self) -> dict` - Метод сераилизации объекта команды/события в словарь содержащий простые типа данных
- `dumps(self) -> str` - Метод сераилизации объекта команды/события в `json` строку

Классы структур являются домено не зависимыми и могут одновременно использоваться разными доменами.

**Пример**

```python
from datetime import date
from dddmisc.messages import DDDCommand, DDDStructure, fields


class Person(DDDStructure):
  iin = fields.String()
  surname = fields.String()
  name = fields.String()
  birthday = fields.Date()


class CreatePerson(DDDCommand):
  client = fields.Structure(Person)

  class Meta:
    domain = 'clients'


# Пример создания команды CreatePerson
cmd1 = CreatePerson(client=Person(iin='123456789012',
                                  surname='Ivanov',
                                  name='Ivan',
                                  birthday=date(1990, 1, 1)))
# Или можно создать так. Оба способа приведут к одному результату
cmd2 = CreatePerson(client={"iin": "123456789012",
                            "surname": "Ivanov",
                            "name": "Ivan",
                            "birthday": "1990-01-01"})

assert cmd1.client == cmd2.client

assert cmd1.dump() == {
  '__reference__': str(cmd1.__reference__),
  '__timestamp__': cmd1.__timestamp__,
  'data': {
    "client": {
      "iin": "123456789012",
      "surname": "Ivanov",
      "name": "Ivan",
      "birthday": "1990-01-01"
    }}
}
```


## Ответ на команду
Для обеспечения единообразия ответов возвращаемых при вызове команд используется класс `DDDResponse`.

В классе `DDDResponse` реализованы следующие атрибуты и методы:
- `__reference__: UUID` - Уникальный идентификатор команды для которой сформирован объект ответа.
- `__timestamp__: float` - Время создания ответа. Генерируется в момент создания.
- `reference: UUID` - Идентификатор объекта аграгата, созданного/изменного в рамках исполнения команды.
- `aggregate: AbstractAggregate` - Объект агрегата созданного/изменного в рамках исполнения команды. Данное свойство не сериализуется и не десериализуется методами `dump`, `dumps`, `load`, `loads`.
- `load(cls, data: dict)` - Метод класса десериализации объекта ответа из словаря.
- `load(cls, data: str)` - Метод класса десериализации объекта ответа из `json` строки.
- `dump(self) -> dict` - Метод сераилизации объекта ответа в словарь содержащий простые типа данных.
- `dumps(self) -> str` - Метод сераилизации объекта ответа в `json` строку.

## Fields
_to be continue..._
