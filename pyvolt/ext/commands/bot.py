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

from importlib.machinery import ModuleSpec
from importlib.util import find_spec, module_from_spec, resolve_name
from inspect import cleandoc, isawaitable
import logging
import sys
import types
import typing

from pyvolt import Client, Message, MessageCreateEvent, Shard, utils

from .context import Context
from .core import GroupMixin
from .errors import (
    # CommandError,
    CommandNotFound,
    ExtensionAlreadyLoaded,
    ExtensionNotLoaded,
    NoEntryPointError,
    ExtensionFailed,
    ExtensionNotFound,
)
from .events import CommandErrorEvent, CommandEvent, CommandCompletionEvent
from .view import StringView

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Mapping
    from typing_extensions import Self

    from ._types import BotT, ContextT, UserCheck
    from .core import Command
    from .gear import Gear

_L = logging.getLogger(__name__)

T = typing.TypeVar('T')


class Bot(Client, GroupMixin[None]):
    """Represents a Revolt bot.

    Parameters
    ----------
    command_prefix: Union[MaybeAwaitableFunc[[:class:`.Context`], List[:class:`str`]], List[:class:`str`], :class:`str`]
        The command's prefix.
    description: Optional[:class:`str`]
        The bot's description.
    owner_id: Optional[:class:`str`]
        The bot owner's ID.
    owner_ids: Set[:class:`str`]
        The bot owner's IDs.
    self_bot: :class:`bool`
        Whether the bot should respond only to logged in user.
    skip_check: Optional[MaybeAwaitableFunc[[:class:`.Context`], :class:`bool`]]
        A callable that checks whether the command should skipped.
    strip_after_prefix: :class:`bool`
        Whether to strip whitespace after prefix. Setting this to ``True`` allows
        using ``!    help``. Defaults to ``False``.
    user_bot: :class:`bool`
        Whether the bot should respond to everyone, including themselves.
    """

    __slots__ = (
        'all_commands',
        'command_prefix',
        'description',
        'owner_id',
        'owner_ids',
        'skip_check',
        'strip_after_prefix',
    )

    def __init__(
        self,
        command_prefix: utils.MaybeAwaitableFunc[[Context[Self]], list[str]] | str | list[str],
        *,
        description: str | None = None,
        self_bot: bool = False,
        strip_after_prefix: bool = False,
        user_bot: bool = False,
        **options,
    ) -> None:
        skip_check = options.pop('skip_check', self.traditional_bot_skip_check)

        if self_bot:
            if user_bot:
                raise TypeError('Both self_bot and user_bot are set')
            skip_check = self.self_bot_skip_check
        elif user_bot:
            skip_check = self.user_bot_skip_check

        self.all_commands: dict[str, Command] = {}
        if isinstance(command_prefix, str):
            command_prefix = [command_prefix]

        self.__gears: dict[str, Gear] = {}
        self.__extensions: dict[str, types.ModuleType] = {}
        self._checks: list[UserCheck] = []
        self._check_once: list[UserCheck] = []
        self._before_invoke: Callable[..., Coroutine[typing.Any, typing.Any, typing.Any]] | None = None
        self._after_invoke: Callable[..., Coroutine[typing.Any, typing.Any, typing.Any]] | None = None

        self.command_prefix: utils.MaybeAwaitableFunc[[Context[Self]], list[str]] | str | list[str] = command_prefix
        self.description: str = cleandoc(description) if description else ''
        self.owner_id: str | None = options.get('owner_id')
        self.owner_ids: set[str] = options.pop('owner_ids', set())
        self.skip_check: utils.MaybeAwaitableFunc[[Context[Self]], bool] = skip_check
        self.strip_after_prefix: bool = strip_after_prefix

        super().__init__(**options)

    @utils.copy_doc(Client.close)
    async def close(self, *, http: bool = True, cleanup_websocket: bool = True) -> None:
        for extension in tuple(self.__extensions):
            try:
                await self.unload_extension(extension)
            except Exception:
                pass

        for gear in tuple(self.__gears):
            try:
                await self.remove_gear(gear)
            except Exception:
                pass

        await super().close(http=http, cleanup_websocket=cleanup_websocket)  # type: ignore

    # Error handler

    async def on_command_error(self, event: CommandErrorEvent, /) -> None:
        """|coro|

        The default command error handler provided by the bot.

        By default this logs to the library logger, however it could be
        overridden to have a different implementation.

        This only fires if you do not specify any listeners for command error.
        """

        command = event.context.command
        if command and command.has_error_handler():
            return

        gear = event.context.gear
        if gear and gear.has_error_handler():
            return

        _L.error('Ignoring exception in command %s', command, exc_info=event.error)

    # global check registration

    def check(self, func: T, /) -> T:
        r"""A decorator that adds a global check to the bot.

        A global check is similar to a :func:`.check` that is applied
        on a per command basis except it is run before any command checks
        have been verified and applies to every command the bot has.

        .. note::

            This function can either be a regular function or a coroutine.

        Similar to a command :func:`.check`\, this takes a single parameter
        of type :class:`.Context` and can only raise exceptions inherited from
        :exc:`.CommandError`.

        Example
        ---------

        .. code-block:: python3

            @bot.check
            def check_commands(ctx):
                return ctx.command.qualified_name in allowed_commands

        """
        # T was used instead of Check to ensure the type matches on return
        self.add_check(func)  # type: ignore
        return func

    def add_check(self, func: UserCheck[ContextT], /, *, call_once: bool = False) -> None:
        """Adds a global check to the bot.

        This is the non-decorator interface to :meth:`.check`
        and :meth:`.check_once`.

        .. seealso:: The :func:`~discord.ext.commands.check` decorator

        Parameters
        -----------
        func
            The function that was used as a global check.
        call_once: :class:`bool`
            If the function should only be called once per
            :meth:`.invoke` call.
        """

        if call_once:
            self._check_once.append(func)
        else:
            self._checks.append(func)

    def remove_check(self, func: UserCheck[ContextT], /, *, call_once: bool = False) -> None:
        """Removes a global check from the bot.

        This function is idempotent and will not raise an exception
        if the function is not in the global checks.

        Parameters
        -----------
        func
            The function to remove from the global checks.
        call_once: :class:`bool`
            If the function was added with ``call_once=True`` in
            the :meth:`.Bot.add_check` call or using :meth:`.check_once`.
        """
        l = self._check_once if call_once else self._checks

        try:
            l.remove(func)
        except ValueError:
            pass

    def check_once(
        self, func: Callable[..., Coroutine[typing.Any, typing.Any, bool]], /
    ) -> Callable[..., Coroutine[typing.Any, typing.Any, bool]]:
        r"""A decorator that adds a "call once" global check to the bot.

        Unlike regular global checks, this one is called only once
        per :meth:`.invoke` call.

        Regular global checks are called whenever a command is called
        or :meth:`.Command.can_run` is called. This type of check
        bypasses that and ensures that it's called only once, even inside
        the default help command.

        .. note::

            When using this function the :class:`.Context` sent to a group subcommand
            may only parse the parent command and not the subcommands due to it
            being invoked once per :meth:`.Bot.invoke` call.

        .. note::

            This function can either be a regular function or a coroutine.

        Similar to a command :func:`.check`\, this takes a single parameter
        of type :class:`.Context` and can only raise exceptions inherited from
        :exc:`.CommandError`.

        Example
        ---------

        .. code-block:: python3

            @bot.check_once
            def whitelist(ctx):
                return ctx.message.author.id in my_whitelist

        """
        self.add_check(func, call_once=True)
        return func

    async def can_run(self, ctx: Context[BotT], /, *, call_once: bool = False) -> bool:
        data = self._check_once if call_once else self._checks

        if len(data) == 0:
            return True

        for f in data:
            tmp = f(ctx)
            if isawaitable(tmp):
                tmp = await tmp

            if not tmp:
                return False

        return True

    # gears

    async def add_gear(
        self,
        gear: Gear,
        /,
    ) -> None:
        """|coro|

        Adds a "gear" to the bot.

        A gear is a class that has its own event listeners and commands.

        .. note::

            Exceptions raised inside a :class:`.Gear`'s :meth:`~.Gear.gear_load` method will be
            propagated to the caller.

        Parameters
        -----------
        gear: :class:`.Gear`
            The gear to register to the bot.

        Raises
        -------
        TypeError
            The gear does not inherit from :class:`.Gear`.
        CommandError
            An error happened during loading.
        ClientException
            A gear with the same name is already loaded.
        """

        if not isinstance(gear, Gear):
            raise TypeError('gears must derive from Gear')

        gear_name = gear.__gear_name__
        existing = self.__gears.get(gear_name)

        if existing is not None:
            await self.remove_gear(gear_name)

        gear = await gear._inject(self)
        self.__gears[gear_name] = gear

    def get_gear(self, name: str, /) -> Gear | None:
        """Gets the gear instance requested.

        If the gear is not found, ``None`` is returned instead.

        Parameters
        -----------
        name: :class:`str`
            The name of the gear you are requesting.
            This is equivalent to the name passed via keyword
            argument in class creation or the class name if unspecified.

        Returns
        --------
        Optional[:class:`Gear`]
            The gear that was requested. If not found, returns ``None``.
        """
        return self.__gears.get(name)

    async def remove_gear(
        self,
        name: str,
        /,
    ) -> Gear | None:
        """|coro|

        Removes a gear from the bot and returns it.

        All registered commands and event listeners that the
        gear has registered will be removed as well.

        If no gear is found then this method has no effect.

        Parameters
        -----------
        name: :class:`str`
            The name of the gear to remove.

        Returns
        -------
        Optional[:class:`.Gear`]
             The gear that was removed. ``None`` if not found.
        """

        gear = self.__gears.pop(name, None)
        if gear is None:
            return

        await gear._eject(self)

        return gear

    @property
    def gears(self) -> Mapping[str, Gear]:
        """Mapping[:class:`str`, :class:`Gear`]: A read-only mapping of gear name to gear."""
        return self.__gears

    # extensions

    async def _remove_module_references(self, name: str, /) -> None:
        # find all references to the module
        # remove the gears registered from the module
        for gearname, gear in self.__gears.copy().items():
            if utils._is_submodule(name, gear.__module__):
                await self.remove_gear(gearname)

        # remove all the commands from the module
        for cmd in self.all_commands.copy().values():
            if cmd.module is not None and utils._is_submodule(name, cmd.module):
                if isinstance(cmd, GroupMixin):
                    cmd.recursively_remove_all_commands()
                self.remove_command(cmd.name)

        # remove all the listeners from the module
        for subscription in self.all_subscriptions():
            if subscription.callback.__module__ is not None and utils._is_submodule(
                name,
                subscription.callback.__module__,
            ):
                subscription.remove()

    async def _call_module_finalizers(self, lib: types.ModuleType, key: str, /) -> None:
        try:
            func = getattr(lib, 'teardown')
        except AttributeError:
            pass
        else:
            try:
                await func(self)
            except Exception:
                pass
        finally:
            self.__extensions.pop(key, None)
            sys.modules.pop(key, None)
            name = lib.__name__
            for module in list(sys.modules.keys()):
                if utils._is_submodule(name, module):
                    del sys.modules[module]

    async def _load_from_module_spec(self, spec: ModuleSpec, key: str) -> None:
        # precondition: key not in self.__extensions
        lib = module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)  # type: ignore
        except Exception as e:
            del sys.modules[key]
            raise ExtensionFailed(name=key, original=e) from e

        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            del sys.modules[key]
            raise NoEntryPointError(name=key)

        try:
            await setup(self)
        except Exception as e:
            del sys.modules[key]
            await self._remove_module_references(lib.__name__)
            await self._call_module_finalizers(lib, key)
            raise ExtensionFailed(name=key, original=e) from e
        else:
            self.__extensions[key] = lib

    def _resolve_name(self, name: str, package: str | None, /) -> str:
        try:
            return resolve_name(name, package)
        except ImportError:
            raise ExtensionNotFound(name=name)

    async def load_extension(self, name: str, *, package: str | None = None) -> None:
        """|coro|

        Loads an extension.

        An extension is a python module that contains commands, gears, or
        listeners.

        An extension must have a global function, ``setup`` defined as
        the entry point on what to do when the extension is loaded. This entry
        point must have a single argument, the ``bot``.

        Parameters
        ------------
        name: :class:`str`
            The extension name to load. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when loading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

        Raises
        --------
        ExtensionNotFound
            The extension could not be imported.
            This is also raised if the name of the extension could not
            be resolved using the provided ``package`` parameter.
        ExtensionAlreadyLoaded
            The extension is already loaded.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension or its setup function had an execution error.
        """

        name = self._resolve_name(name, package)
        if name in self.__extensions:
            raise ExtensionAlreadyLoaded(name=name)

        spec = find_spec(name)
        if spec is None:
            raise ExtensionNotFound(name=name)

        await self._load_from_module_spec(spec, name)

    async def unload_extension(self, name: str, *, package: str | None = None) -> None:
        """|coro|

        Unloads an extension.

        When the extension is unloaded, all commands, listeners, and gears are
        removed from the bot and the module is un-imported.

        The extension can provide an optional global function, ``teardown``,
        to do miscellaneous clean-up if necessary. This function takes a single
        parameter, the ``bot``, similar to ``setup`` from
        :meth:`~.Bot.load_extension`.

        Parameters
        ------------
        name: :class:`str`
            The extension name to unload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when unloading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

        Raises
        -------
        ExtensionNotFound
            The name of the extension could not
            be resolved using the provided ``package`` parameter.
        ExtensionNotLoaded
            The extension was not loaded.
        """

        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise ExtensionNotLoaded(name=name)

        await self._remove_module_references(lib.__name__)
        await self._call_module_finalizers(lib, name)

    async def reload_extension(self, name: str, *, package: str | None = None) -> None:
        """|coro|

        Atomically reloads an extension.

        This replaces the extension with the same extension, only refreshed. This is
        equivalent to a :meth:`unload_extension` followed by a :meth:`load_extension`
        except done in an atomic way. That is, if an operation fails mid-reload then
        the bot will roll-back to the prior working state.

        Parameters
        ------------
        name: :class:`str`
            The extension name to reload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when reloading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

        Raises
        -------
        ExtensionNotLoaded
            The extension was not loaded.
        ExtensionNotFound
            The extension could not be imported.
            This is also raised if the name of the extension could not
            be resolved using the provided ``package`` parameter.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension setup function had an execution error.
        """

        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise ExtensionNotLoaded(name=name)

        # get the previous module states from sys modules
        modules = {name: module for name, module in sys.modules.items() if utils._is_submodule(lib.__name__, name)}

        try:
            # Unload and then load the module...
            await self._remove_module_references(lib.__name__)
            await self._call_module_finalizers(lib, name)
            await self.load_extension(name)
        except Exception:
            # if the load failed, the remnants should have been
            # cleaned from the load_extension function call
            # so let's load it from our old compiled library.
            await lib.setup(self)
            self.__extensions[name] = lib

            # revert sys.modules back to normal and raise back to caller
            sys.modules.update(modules)
            raise

    @property
    def extensions(self) -> Mapping[str, types.ModuleType]:
        """Mapping[:class:`str`, :class:`py:types.ModuleType`]: A read-only mapping of extension name to extension."""
        return types.MappingProxyType(self.__extensions)

    async def get_prefix(self, ctx: Context[Self], /) -> list[str]:
        """List[:class:`str`]: Return prefixes possible in this context."""
        tmp = self.command_prefix
        if callable(tmp):
            tmp = tmp(ctx)
            if isawaitable(tmp):
                tmp = await tmp
        if isinstance(tmp, str):
            tmp = [tmp]
        return tmp

    async def get_context(self, origin: Message, shard: Shard, /, *, cls: type[ContextT] = Context) -> ContextT:
        view = StringView(origin.content)
        ctx = cls(
            bot=self,
            command=None,
            message=origin,
            shard=shard,
            view=view,
        )

        prefixes = await self.get_prefix(ctx)
        invoked_prefix = None
        for prefix in prefixes:
            if view.skip_string(prefix):
                invoked_prefix = prefix
                break

        if invoked_prefix:
            if self.strip_after_prefix:
                view.skip_ws()

            label = view.get_word()

            ctx.label = label
            ctx.prefix = invoked_prefix
            ctx.command = self.all_commands.get(label)

        return ctx

    def self_bot_skip_check(self, ctx: Context[Self], /) -> bool:
        return ctx.author.bot is not None or ctx.message.webhook is not None or ctx.author_id != ctx.me.id

    def traditional_bot_skip_check(self, ctx: Context[Self], /) -> bool:
        return ctx.author.bot is not None or ctx.message.webhook is not None or ctx.author_id == ctx.me.id

    def user_bot_skip_check(self, ctx: Context[Self], /) -> bool:
        return ctx.author.bot is not None or ctx.message.webhook is not None

    @property
    def self_bot(self) -> bool:
        """:class:`bool`: Whether the bot is a self-bot (responds only to :attr:`.me`)."""
        return self.skip_check is self.self_bot_skip_check

    @property
    def traditional_bot(self) -> bool:
        """:class:`bool`: Whether the bot is a traditional bot (does not respond to :attr:`.me`)."""
        return self.skip_check is self.traditional_bot_skip_check

    @property
    def user_bot(self) -> bool:
        """:class:`bool`: Whether the bot is a userbot (responds to everyone)."""
        return self.skip_check is self.user_bot_skip_check

    async def invoke(self, ctx: Context[Self], /) -> None:
        if ctx.command is not None:
            self.dispatch(CommandEvent(context=ctx))
            await ctx.command.invoke(ctx)
            self.dispatch(CommandCompletionEvent(context=ctx))
        elif ctx.label:
            exc = CommandNotFound(f'Command "{ctx.label}" is not found')
            self.dispatch(CommandErrorEvent(context=ctx, error=exc))

    async def process_commands(self, message: Message, shard: Shard, /) -> None:
        ctx = await self.get_context(message, shard)

        tmp = self.skip_check(ctx)  # type: ignore
        if isawaitable(tmp):
            tmp = await tmp

        if tmp:
            return

        await self.invoke(ctx)  # type: ignore

    async def on_message_create(self, event: MessageCreateEvent, /) -> None:
        await self.process_commands(event.message, event.shard)


__all__ = ('Bot',)
