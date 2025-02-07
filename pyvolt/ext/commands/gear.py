"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import typing
import inspect
import logging

import pyvolt
from pyvolt.utils import evaluate_annotation, maybe_coroutine, unwrap_function

from ._types import _BaseCommand, BotT

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from typing_extensions import Self

    from .bot import Bot
    from .context import Context
    from .core import Command

__all__ = (
    'GearMeta',
    'Gear',
)

FuncT = typing.TypeVar('FuncT', bound='Callable[..., typing.Any]')
_log = logging.getLogger(__name__)


class GearMeta(type):
    """A metaclass for defining a gear.

    Note that you should probably not use this directly. It is exposed
    purely for documentation purposes along with making custom metaclasses to intermix
    with other metaclasses such as the :class:`abc.ABCMeta` metaclass.

    For example, to create an abstract gear mixin class, the following would be done.

    .. code-block:: python3

        import abc


        class GearABCMeta(commands.GearMeta, abc.ABCMeta):
            pass


        class SomeMixin(metaclass=abc.ABCMeta):
            pass


        class SomeGearMixin(SomeMixin, commands.Gear, metaclass=GearABCMeta):
            pass

    .. note::

        When passing an attribute of a metaclass that is documented below, note
        that you must pass it as a keyword-only argument to the class creation
        like the following example:

        .. code-block:: python3

            class MyGear(commands.Gear, name='My Gear'):
                pass

    Attributes
    -----------
    name: :class:`str`
        The gear name. By default, it is the name of the class with no modification.
    description: :class:`str`
        The gear description. By default, it is the cleaned docstring of the class.
    command_attrs: :class:`dict`
        A list of attributes to apply to every command inside this gear. The dictionary
        is passed into the :class:`Command` options at ``__init__``.
        If you specify attributes inside the command attribute in the class, it will
        override the one specified inside this attribute. For example:

        .. code-block:: python3

            class MyGear(commands.Gear, command_attrs={'hidden': True}):
                @commands.command()
                async def foo(self, ctx):
                    pass  # hidden -> True

                @commands.command(hidden=False)
                async def bar(self, ctx):
                    pass  # hidden -> False

    """

    __gear_name__: str
    __gear_description__: str
    __gear_settings__: dict[str, typing.Any]
    __gear_commands__: list[Command[typing.Any, ..., typing.Any]]
    __gear_listeners__: list[tuple[type[pyvolt.BaseEvent], str]]

    def __new__(cls, /, *args: typing.Any, **kwargs: typing.Any) -> GearMeta:
        name, bases, attrs = args

        gear_name = kwargs.pop('name', name)

        attrs['__gear_settings__'] = kwargs.pop('command_attrs', {})
        attrs['__gear_name__'] = gear_name

        description = kwargs.pop('description', None)
        if description is None:
            description = inspect.cleandoc(attrs.get('__doc__', ''))

        attrs['__gear_description__'] = description

        commands = {}
        listeners = {}
        no_bot_gear = 'Commands or listeners must not start with gear_ or bot_ (in method {0.__name__}.{1})'

        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)
        for base in reversed(new_cls.__mro__):
            for elem, value in base.__dict__.items():
                if elem in commands:
                    del commands[elem]
                if elem in listeners:
                    del listeners[elem]

                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__
                if isinstance(value, _BaseCommand):
                    if is_static_method:
                        raise TypeError(f'Command in method {base}.{elem!r} must not be staticmethod.')
                    if elem.startswith(('gear_', 'bot_')):
                        raise TypeError(no_bot_gear.format(base, elem))
                    commands[elem] = value
                elif inspect.iscoroutinefunction(value):
                    if hasattr(value, '__gear_listener__'):
                        if elem.startswith(('gear_', 'bot_')):
                            raise TypeError(no_bot_gear.format(base, elem))
                        listeners[elem] = value

        new_cls.__gear_commands__ = list(commands.values())  # this will be copied in Gear.__new__

        listeners_as_list = []
        for listener in listeners.values():
            for listener_event in listener.__gear_listener_events__:
                # I use __name__ instead of just storing the value so I can inject
                # the self attribute when the time comes to add them to the bot
                listeners_as_list.append((listener_event, listener.__name__))

        new_cls.__gear_listeners__ = listeners_as_list
        return new_cls

    def __init__(self, /, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args)

    @classmethod
    def qualified_name(cls) -> str:
        return cls.__gear_name__


def _gear_special_method(func: FuncT, /) -> FuncT:
    func.__gear_special_method__ = None  # type: ignore
    return func


class Gear(metaclass=GearMeta):
    """The base class that all gears must inherit from.

    A gear is a collection of commands, listeners, and optional state to
    help group commands together. More information on them can be found on
    the :ref:`ext_commands_gears` page.

    When inheriting from this class, the options shown in :class:`GearMeta`
    are equally valid here.
    """

    __gear_name__: str
    __gear_description__: str
    __gear_settings__: dict[str, typing.Any]
    __gear_commands__: list[Command[Self, ..., typing.Any]]
    __gear_listeners__: list[tuple[str, str]]

    def __new__(cls, /, *_: typing.Any, **__: typing.Any) -> Self:
        # For issue Rapptz/discord.py#426, we need to store a copy of the command objects
        # since we modify them to inject `self` to them.
        # To do this, we need to interfere with the Gear creation process.
        self = super().__new__(cls)
        cmd_attrs = cls.__gear_settings__

        # Either update the command with the gear provided defaults or copy it.
        # r.e type ignore, type-checker complains about overriding a ClassVar
        self.__gear_commands__ = tuple(c._update_copy(cmd_attrs) for c in cls.__gear_commands__)  # type: ignore

        lookup = {cmd.qualified_name: cmd for cmd in self.__gear_commands__}

        # Update the Command instances dynamically as well
        for command in self.__gear_commands__:
            setattr(self, command.callback.__name__, command)
            parent = command.parent
            if parent is not None:
                # Get the latest parent reference
                parent = lookup[parent.qualified_name]  # type: ignore

                # Update our parent's reference to our self
                parent.remove_command(command.name)  # type: ignore
                parent.add_command(command)  # type: ignore

        return self

    def get_commands(self) -> list[Command[Self, ..., typing.Any]]:
        r"""Returns the commands that are defined inside this gear.

        Returns
        --------
        List[:class:`.Command`]
            A :class:`list` of :class:`.Command`\s that are
            defined inside this gear, not including subcommands.
        """
        return [c for c in self.__gear_commands__ if c.parent is None]

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Returns the gear's specified name, not the class name."""
        return self.__gear_name__

    @property
    def description(self) -> str:
        """:class:`str`: Returns the gear's description, typically the cleaned docstring."""
        return self.__gear_description__

    @description.setter
    def description(self, description: str) -> None:
        self.__gear_description__ = description

    def walk_commands(self) -> Generator[Command[Self, ..., typing.Any], None, None]:
        """An iterator that recursively walks through this gear's commands and subcommands.

        Yields
        ------
        Union[:class:`.Command`, :class:`.Group`]
            A command or group from the gear.
        """
        from .core import GroupMixin

        for command in self.__gear_commands__:
            if command.parent is None:
                yield command
                if isinstance(command, GroupMixin):
                    yield from command.walk_commands()

    def get_listeners(self) -> list[tuple[type[pyvolt.BaseEvent], Callable[..., typing.Any]]]:
        """Returns a :class:`list` of (event, function) listener pairs that are defined in this gear.

        Returns
        --------
        List[Tuple[Type[:class:`pyvolt.BaseEvent`], :ref:`coroutine <coroutine>`]]
            The listeners defined in this gear.
        """
        return [(name, getattr(self, method_name)) for name, method_name in self.__gear_listeners__]

    @classmethod
    def _get_overridden_method(cls, method: FuncT, /) -> typing.Optional[FuncT]:
        """Return None if the method is not overridden. Otherwise returns the overridden method."""
        return getattr(method.__func__, '__gear_special_method__', method)  # type: ignore

    @classmethod
    def listener(cls, to: typing.Optional[type[pyvolt.BaseEvent]] = None) -> Callable[[FuncT], FuncT]:
        """A decorator that marks a function as a listener.

        This is the gear equivalent of :meth:`.Bot.listen`.

        Parameters
        ------------
        to: Optional[Type[:class:`BaseEvent`]]
            The class of the event being listened to. If not provided, it
            defaults to the argument's type.

        Raises
        --------
        :class:`TypeError`
            The event was not passed.
        """

        if to is not None and not issubclass(to, pyvolt.BaseEvent):
            raise TypeError(f'Gear.listener expected BaseEvent but received {to.__name__} instead.')

        def decorator(func: FuncT, /) -> FuncT:
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__

            tmp = to
            if tmp is None:
                args = list(inspect.signature(actual).parameters.values())
                annotation = args[1].annotation
                if annotation is None:
                    raise TypeError('No annotation was found')

                try:
                    globalns = unwrap_function(func).__globals__
                except AttributeError:
                    globalns = {}

                tmp = evaluate_annotation(annotation, globalns, globalns, {})

            actual.__gear_listener__ = True  # type: ignore
            try:
                actual.__gear_listener_events__.append(tmp)  # type: ignore
            except AttributeError:
                actual.__gear_listener_events__ = [tmp]  # type: ignore
            # we have to return `func` instead of `actual` because
            # we need the type to be `staticmethod` for the metaclass
            # to pick it up but the metaclass unfurls the function and
            # thus the assignments need to be on the actual function
            return func

        return decorator

    def has_error_handler(self) -> bool:
        """:class:`bool`: Checks whether the gear has an error handler."""
        return not hasattr(self.gear_command_error.__func__, '__gear_special_method__')  # type: ignore

    @_gear_special_method
    async def gear_load(self) -> None:
        """|maybecoro|

        A special method that is called when the gear gets loaded.

        Subclasses must replace this if they want special asynchronous loading behaviour.
        Note that the ``__init__`` special method does not allow asynchronous code to run
        inside it, thus this is helpful for setting up code that needs to be asynchronous.
        """
        pass

    @_gear_special_method
    async def gear_unload(self) -> None:
        """|maybecoro|

        A special method that is called when the gear gets removed.

        Subclasses must replace this if they want special unloading behaviour.

        Exceptions raised in this method are ignored during extension unloading.
        """
        pass

    @_gear_special_method
    def bot_check_once(self, ctx: Context[BotT], /) -> bool:
        """A special method that registers as a :meth:`.Bot.check_once`
        check.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_gear_special_method
    def bot_check(self, ctx: Context[BotT], /) -> bool:
        """A special method that registers as a :meth:`.Bot.check`
        check.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_gear_special_method
    def gear_check(self, ctx: Context[BotT], /) -> bool:
        """A special method that registers as a :func:`~pyvolt.ext.commands.check`
        for every command and subcommand in this gear.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_gear_special_method
    async def gear_command_error(self, ctx: Context[BotT], error: Exception, /) -> None:
        """|coro|

        A special method that is called whenever an error
        is dispatched inside this gear.

        This is similar to :func:`.on_command_error` except only applying
        to the commands inside this gear.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context where the error happened.
        error: :class:`CommandError`
            The error that happened.
        """
        pass

    @_gear_special_method
    async def gear_before_invoke(self, ctx: Context[BotT], /) -> None:
        """|coro|

        A special method that acts as a gear local pre-invoke hook.

        This is similar to :meth:`.Command.before_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    @_gear_special_method
    async def gear_after_invoke(self, ctx: Context[BotT], /) -> None:
        """|coro|

        A special method that acts as a gear local post-invoke hook.

        This is similar to :meth:`.Command.after_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    async def _inject(self, bot: Bot, /) -> Self:
        cls = self.__class__

        # we'll call this first so that errors can propagate without
        # having to worry about undoing anything
        await maybe_coroutine(self.gear_load)

        # realistically, the only thing that can cause loading errors
        # is essentially just the command loading, which raises if there are
        # duplicates. When this condition is met, we want to undo all what
        # we've added so far for some form of atomic loading.
        for index, command in enumerate(self.__gear_commands__):
            command.gear = self
            if command.parent is None:
                try:
                    bot.add_command(command)
                except Exception as e:
                    # undo our additions
                    for to_undo in self.__gear_commands__[:index]:
                        if to_undo.parent is None:
                            bot.remove_command(to_undo.name)
                    try:
                        await maybe_coroutine(self.gear_unload)
                    finally:
                        raise e

        # check if we're overriding the default
        if cls.bot_check is not Gear.bot_check:
            bot.add_check(self.bot_check)

        if cls.bot_check_once is not Gear.bot_check_once:
            bot.add_check(self.bot_check_once, call_once=True)

        # while Bot.add_listener can raise if it's not a coroutine,
        # this precondition is already met by the listener decorator
        # already, thus this should never raise.
        # Outside of, memory errors and the like...
        for event, method_name in self.__gear_listeners__:
            bot.subscribe(event, getattr(self, method_name))

        return self

    async def _eject(self, bot: Bot, /) -> None:
        cls = self.__class__

        try:
            for command in self.__gear_commands__:
                if command.parent is None:
                    bot.remove_command(command.name)

            for event, method_name in self.__gear_listeners__:
                bot.unsubscribe(event, getattr(self, method_name))

            if cls.bot_check is not Gear.bot_check:
                bot.remove_check(self.bot_check)

            if cls.bot_check_once is not Gear.bot_check_once:
                bot.remove_check(self.bot_check_once, call_once=True)
        finally:
            try:
                await maybe_coroutine(self.gear_unload)
            except Exception:
                _log.exception('Ignoring exception in gear unload for Gear %r (%r)', cls, self.qualified_name)
