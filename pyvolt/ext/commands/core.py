from __future__ import annotations

import asyncio
from datetime import timezone
from functools import wraps
import inspect
import re
import typing

import pyvolt
from pyvolt.utils import MISSING

from ._types import GearT, _BaseCommand
from .converter import Greedy, run_converters
from .cooldown import BucketType, CooldownMapping, MaxConcurrency, Cooldown
from .errors import (
    CommandError,
    MissingRequiredArgument,
    MissingRequiredAttachment,
    TooManyArguments,
    CheckFailure,
    # CheckAnyFailure,
    # PrivateMessageOnly,
    # NoPrivateMessage,
    # NotOwner,
    DisabledCommand,
    CommandInvokeError,
    ArgumentParsingError,
    CommandRegistrationError,
)
from .events import CommandErrorEvent
from .gear import Gear
from .parameters import Parameter, Signature

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Generator
    from typing_extensions import Self

    from ._types import BotT, ContextT, Error, Hook, UserCheck
    from .context import Context

P = typing.ParamSpec('P')
T = typing.TypeVar('T')

CommandT = typing.TypeVar('CommandT', bound='Command[typing.Any, ..., typing.Any]')
GroupT = typing.TypeVar('GroupT', bound='Group[typing.Any, ..., typing.Any]')


def get_signature_parameters(
    function: Callable[..., typing.Any],
    globalns: dict[str, typing.Any],
    /,
    *,
    skip_parameters: int | None = None,
) -> dict[str, Parameter]:
    signature = Signature.from_callable(function)
    params: dict[str, Parameter] = {}
    cache: dict[str, typing.Any] = {}
    eval_annotation = pyvolt.utils.evaluate_annotation
    required_params = pyvolt.utils.is_inside_class(function) + 1 if skip_parameters is None else skip_parameters
    if len(signature.parameters) < required_params:
        raise TypeError(f'Command signature requires at least {required_params - 1} parameter(s)')

    iterator = iter(signature.parameters.items())
    for _ in range(0, required_params):
        next(iterator)

    for name, parameter in iterator:
        default = parameter.default
        if isinstance(default, Parameter):  # update from the default
            if default.annotation is not Parameter.empty:
                # There are a few cases to care about here.
                # x: TextChannel = commands.CurrentChannel
                # x = commands.CurrentChannel
                # In both of these cases, the default parameter has an explicit annotation
                # but in the second case it's only used as the fallback.
                if default._fallback:
                    if parameter.annotation is Parameter.empty:
                        parameter._annotation = default.annotation
                else:
                    parameter._annotation = default.annotation

            parameter._default = default.default
            parameter._description = default._description
            parameter._displayed_default = default._displayed_default
            parameter._displayed_name = default._displayed_name

        annotation = parameter.annotation

        if annotation is None:
            params[name] = parameter.replace(annotation=type(None))
            continue

        annotation = eval_annotation(annotation, globalns, globalns, cache)
        if annotation is Greedy:
            raise TypeError('Unparameterized Greedy[...] is disallowed in signature.')

        params[name] = parameter.replace(annotation=annotation)

    return params


def _fold_text(input: str, /) -> str:
    """Turns a single newline into a space, and multiple newlines into a newline."""

    def replacer(match: re.Match[str], /) -> str:
        if len(match.group()) <= 1:
            return ' '
        return '\n'

    return re.sub(r'\n+', replacer, inspect.cleandoc(input))


def extract_descriptions_from_docstring(
    function: Callable[..., typing.Any], params: dict[str, Parameter], /
) -> str | None:
    docstring = inspect.getdoc(function)

    if docstring is None:
        return None

    divide = pyvolt.utils.PARAMETER_HEADING_REGEX.split(docstring, 1)
    if len(divide) == 1:
        return docstring

    description, param_docstring = divide
    for match in pyvolt.utils.NUMPY_DOCSTRING_ARG_REGEX.finditer(param_docstring):
        name = match.group('name')

        if name not in params:
            is_display_name = None
            for v in params.values():
                if v.displayed_name == name:
                    is_display_name = v
                    break

            if is_display_name:
                name = is_display_name.name
            else:
                continue

        param = params[name]
        if param.description is None:
            param._description = _fold_text(match.group('description'))

    return _fold_text(description.strip())


def wrap_callback(
    coro: Callable[P, Coroutine[typing.Any, typing.Any, T]], /
) -> Callable[P, Coroutine[typing.Any, typing.Any, T | None]]:
    @wraps(coro)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T | None:
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            raise
        except asyncio.CancelledError:
            return
        except Exception as exc:
            raise CommandInvokeError(original=exc) from exc
        return ret

    return wrapped


def hooked_wrapped_callback(
    command: Command[typing.Any, ..., typing.Any],
    ctx: Context[BotT],
    coro: Callable[P, Coroutine[typing.Any, typing.Any, T]],
    /,
) -> Callable[P, Coroutine[typing.Any, typing.Any, T | None]]:
    @wraps(coro)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T | None:
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            ctx.command_failed = True
            raise
        except asyncio.CancelledError:
            ctx.command_failed = True
            return
        except Exception as exc:
            ctx.command_failed = True
            raise CommandInvokeError(original=exc) from exc
        finally:
            if command._max_concurrency is not None:
                await command._max_concurrency.release(ctx.message)

            await command.call_after_hooks(ctx)
        return ret

    return wrapped


class _CaseInsensitiveDict(dict):
    def __contains__(self, k, /):
        return super().__contains__(k.casefold())

    def __delitem__(self, k, /):
        return super().__delitem__(k.casefold())

    def __getitem__(self, k, /):
        return super().__getitem__(k.casefold())

    def get(self, k, default=None, /):
        return super().get(k.casefold(), default)

    def pop(self, k, default=None, /):
        return super().pop(k.casefold(), default)

    def __setitem__(self, k, v, /):
        super().__setitem__(k.casefold(), v)


class _StatelessAssetIterator:
    def __init__(self, data: list[pyvolt.StatelessAsset], /):
        self.data: list[pyvolt.StatelessAsset] = data
        self.index: int = 0

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> pyvolt.StatelessAsset:
        try:
            value = self.data[self.index]
        except IndexError:
            raise StopIteration
        else:
            self.index += 1
            return value

    def is_empty(self) -> bool:
        return self.index >= len(self.data)


class _AssetIterator:
    __slots__ = (
        'data',
        'index',
    )

    def __init__(self, data: list[pyvolt.Asset], /):
        self.data: list[pyvolt.Asset] = data
        self.index: int = 0

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> pyvolt.Asset:
        try:
            value = self.data[self.index]
        except IndexError:
            raise StopIteration
        else:
            self.index += 1
            return value

    def is_empty(self) -> bool:
        return self.index >= len(self.data)


class Command(_BaseCommand, typing.Generic[GearT, P, T]):
    r"""A class that implements the protocol for a bot text command.

    These are not created manually, instead they are created via the
    decorator or functional interface.

    Attributes
    -----------
    name: :class:`str`
        The name of the command.
    callback: :ref:`coroutine <coroutine>`
        The coroutine that is executed when the command is called.
    help: Optional[:class:`str`]
        The long help text for the command.
    brief: Optional[:class:`str`]
        The short help text for the command.
    usage: Optional[:class:`str`]
        A replacement for arguments in the default help text.
    aliases: Union[List[:class:`str`], Tuple[:class:`str`]]
        The list of aliases the command can be invoked under.
    enabled: :class:`bool`
        A boolean that indicates if the command is currently enabled.
        If the command is invoked while it is disabled, then
        :exc:`.DisabledCommand` is raised to the :func:`.on_command_error`
        event. Defaults to ``True``.
    parent: Optional[:class:`Group`]
        The parent group that this command belongs to. ``None`` if there
        isn't one.
    gear: Optional[:class:`Gear`]
        The gear that this command belongs to. ``None`` if there isn't one.
    checks: List[Callable[[:class:`.Context`], :class:`bool`]]
        A list of predicates that verifies if the command could be executed
        with the given :class:`.Context` as the sole parameter. If an exception
        is necessary to be thrown to signal failure, then one inherited from
        :exc:`.CommandError` should be used. Note that if the checks fail then
        :exc:`.CheckFailure` exception is raised to the :func:`.on_command_error`
        event.
    description: :class:`str`
        The message prefixed into the default help command.
    hidden: :class:`bool`
        If ``True``\, the default help command does not show this in the
        help output.
    rest_is_raw: :class:`bool`
        If ``False`` and a keyword-only argument is provided then the keyword
        only argument is stripped and handled as if it was a regular argument
        that handles :exc:`.MissingRequiredArgument` and default values in a
        regular matter rather than passing the rest completely raw. If ``True``
        then the keyword-only argument will pass in the rest of the arguments
        in a completely raw matter. Defaults to ``False``.
    invoked_subcommand: Optional[:class:`Command`]
        The subcommand that was invoked, if any.
    require_var_positional: :class:`bool`
        If ``True`` and a variadic positional argument is specified, requires
        the user to specify at least one argument. Defaults to ``False``.
    ignore_extra: :class:`bool`
        If ``True``\, ignores extraneous strings passed to a command if all its
        requirements are met (e.g. ``?foo a b c`` when only expecting ``a``
        and ``b``). Otherwise :func:`.on_command_error` and local error handlers
        are called with :exc:`.TooManyArguments`. Defaults to ``True``.
    cooldown_after_parsing: :class:`bool`
        If ``True``\, cooldown processing is done after argument parsing,
        which calls converters. If ``False`` then cooldown processing is done
        first and then the converters are called second. Defaults to ``False``.
    extras: :class:`dict`
        A dict of user provided extras to attach to the Command.

        .. note::
            This object may be copied by the library.
    """

    __original_kwargs__: dict[str, typing.Any]

    def __new__(cls, /, *_: typing.Any, **kwargs: typing.Any) -> Self:
        # if you're wondering why this is done, it's because we need to ensure
        # we have a complete original copy of **kwargs even for classes that
        # mess with it by popping before delegating to the subclass __init__.
        # In order to do this, we need to control the instance creation and
        # inject the original kwargs through __new__ rather than doing it
        # inside __init__.
        self = super().__new__(cls)

        # we do a shallow copy because it's probably the most common use case.
        # this could potentially break if someone modifies a list or something
        # while it's in movement, but for now this is the cheapest and
        # fastest way to do what we want.
        self.__original_kwargs__ = kwargs.copy()
        return self

    def __init__(
        self,
        func: Callable[typing.Concatenate[GearT, Context[typing.Any], P], Coroutine[typing.Any, typing.Any, T]]
        | Callable[typing.Concatenate[Context[typing.Any], P], Coroutine[typing.Any, typing.Any, T]],
        /,
        **kwargs: typing.Any,
    ) -> None:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')

        name = kwargs.get('name') or func.__name__
        if not isinstance(name, str):
            raise TypeError('Name of a command must be a string.')
        self.name: str = name

        self.callback = func
        self.enabled: bool = kwargs.get('enabled', True)

        help_doc = kwargs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = extract_descriptions_from_docstring(func, self.params)

        self.help: str | None = help_doc

        self.brief: str | None = kwargs.get('brief')
        self.usage: str | None = kwargs.get('usage')
        self.rest_is_raw: bool = kwargs.get('rest_is_raw', False)
        self.aliases: list[str] | tuple[str] = kwargs.get('aliases', [])
        self.extras: dict[typing.Any, typing.Any] = kwargs.get('extras', {})

        if not isinstance(self.aliases, (list, tuple)):
            raise TypeError('Aliases of a command must be a list or a tuple of strings.')

        self.description: str = inspect.cleandoc(kwargs.get('description', ''))
        self.hidden: bool = kwargs.get('hidden', False)

        try:
            checks = func.__commands_checks__  # type: ignore
            checks.reverse()
        except AttributeError:
            checks = kwargs.get('checks', [])

        self.checks: list[UserCheck[Context[typing.Any]]] = checks

        try:
            cooldown = func.__commands_cooldown__  # type: ignore
        except AttributeError:
            cooldown = kwargs.get('cooldown')

        if cooldown is None:
            buckets = CooldownMapping(original=cooldown, type=BucketType.default)
        elif isinstance(cooldown, CooldownMapping):
            buckets: CooldownMapping[Context[typing.Any]] = cooldown
        else:
            raise TypeError('Cooldown must be an instance of CooldownMapping or None.')
        self._buckets: CooldownMapping[Context[typing.Any]] = buckets

        try:
            max_concurrency = func.__commands_max_concurrency__  # type: ignore
        except AttributeError:
            max_concurrency = kwargs.get('max_concurrency')

        self._max_concurrency: MaxConcurrency | None = max_concurrency

        self.require_var_positional: bool = kwargs.get('require_var_positional', False)
        self.ignore_extra: bool = kwargs.get('ignore_extra', True)
        self.cooldown_after_parsing: bool = kwargs.get('cooldown_after_parsing', False)
        self._gear: GearT = None  # type: ignore # This breaks every other pyright release

        # Bandaid for the fact that sometimes parent can be the bot instance
        parent: GroupMixin[typing.Any] | None = kwargs.get('parent')
        self.parent: GroupMixin[typing.Any] | None = parent if isinstance(parent, _BaseCommand) else None

        self._before_invoke: Hook | None = None
        try:
            before_invoke = func.__before_invoke__  # type: ignore
        except AttributeError:
            pass
        else:
            self.before_invoke(before_invoke)

        self._after_invoke: Hook | None = None
        try:
            after_invoke = func.__after_invoke__  # type: ignore
        except AttributeError:
            pass
        else:
            self.after_invoke(after_invoke)

    @property
    def gear(self) -> GearT:
        return self._gear

    @gear.setter
    def gear(self, value: GearT) -> None:
        self._gear = value

    @property
    def callback(
        self,
    ) -> (
        Callable[typing.Concatenate[GearT, Context[typing.Any], P], Coroutine[typing.Any, typing.Any, T]]
        | Callable[typing.Concatenate[Context[typing.Any], P], Coroutine[typing.Any, typing.Any, T]]
    ):
        return self._callback

    @callback.setter
    def callback(
        self,
        function: Callable[typing.Concatenate[GearT, Context[typing.Any], P], Coroutine[typing.Any, typing.Any, T]]
        | Callable[typing.Concatenate[Context[typing.Any], P], Coroutine[typing.Any, typing.Any, T]],
    ) -> None:
        self._callback = function
        unwrap = pyvolt.utils.unwrap_function(function)
        self.module: str = unwrap.__module__

        try:
            globalns = unwrap.__globals__
        except AttributeError:
            globalns = {}

        self.params: dict[str, Parameter] = get_signature_parameters(function, globalns)

    def add_check(self, func: UserCheck[Context[typing.Any]], /) -> None:
        """Adds a check to the command.

        This is the non-decorator interface to :func:`.check`.

        .. seealso:: The :func:`~pyvolt.ext.commands.check` decorator

        Parameters
        -----------
        func
            The function that will be used as a check.
        """

        self.checks.append(func)

    def remove_check(self, func: UserCheck[Context[typing.Any]], /) -> None:
        """Removes a check from the command.

        This function is idempotent and will not raise an exception
        if the function is not in the command's checks.


        Parameters
        -----------
        func
            The function to remove from the checks.
        """

        try:
            self.checks.remove(func)
        except ValueError:
            pass

    def update(self, /, **kwargs: typing.Any) -> None:
        """Updates :class:`Command` instance with updated attribute.

        This works similarly to the :func:`~pyvolt.ext.commands.command` decorator in terms
        of parameters in that they are passed to the :class:`Command` or
        subclass constructors, sans the name and callback.
        """
        gear = self.gear
        self.__init__(self.callback, **dict(self.__original_kwargs__, **kwargs))
        self.gear = gear

    async def __call__(self, context: Context[BotT], /, *args: P.args, **kwargs: P.kwargs) -> T:
        """|coro|

        Calls the internal callback that the command holds.

        .. note::

            This bypasses all mechanisms -- including checks, converters,
            invoke hooks, cooldowns, etc. You must take care to pass
            the proper arguments and types to this function.
        """
        if self.gear is not None:
            return await self.callback(self.gear, context, *args, **kwargs)  # type: ignore
        else:
            return await self.callback(context, *args, **kwargs)  # type: ignore

    def _ensure_assignment_on_copy(self, other: Self) -> Self:
        other._before_invoke = self._before_invoke
        other._after_invoke = self._after_invoke
        other.extras = self.extras
        if self.checks != other.checks:
            other.checks = self.checks.copy()
        if self._buckets.valid and not other._buckets.valid:
            other._buckets = self._buckets.copy()
        if self._max_concurrency and self._max_concurrency != other._max_concurrency:
            other._max_concurrency = self._max_concurrency.copy()

        try:
            other.on_error = self.on_error
        except AttributeError:
            pass
        return other

    def copy(self) -> Self:
        """Creates a copy of this command.

        Returns
        --------
        :class:`Command`
            A new instance of this command.
        """
        ret = self.__class__(self.callback, **self.__original_kwargs__)
        return self._ensure_assignment_on_copy(ret)

    def _update_copy(self, kwargs: dict[str, typing.Any], /) -> Self:
        if kwargs:
            kw = kwargs.copy()
            kw.update(self.__original_kwargs__)
            copy = self.__class__(self.callback, **kw)
            return self._ensure_assignment_on_copy(copy)
        else:
            return self.copy()

    async def dispatch_error(self, ctx: Context[BotT], error: CommandError, /) -> None:
        ctx.command_failed = True
        gear = self.gear
        try:
            coro = self.on_error
        except AttributeError:
            pass
        else:
            injected = wrap_callback(coro)  # type: ignore
            if gear is not None:
                await injected(gear, ctx, error)
            else:
                await injected(ctx, error)  # type: ignore

        try:
            if gear is not None:
                local = Gear._get_overridden_method(gear.gear_command_error)
                if local is not None:
                    wrapped = wrap_callback(local)
                    await wrapped(ctx, error)
        finally:
            event = CommandErrorEvent(
                context=ctx,
                error=error,
            )
            ctx.bot.dispatch(event)

    async def transform(self, ctx: Context[BotT], param: Parameter, attachments: _AssetIterator, /) -> typing.Any:
        converter = param.converter
        consume_rest_is_special = param.kind == param.KEYWORD_ONLY and not self.rest_is_raw
        view = ctx.view
        view.skip_ws()

        # The greedy converter is simple -- it keeps going until it fails in which case,
        # it undos the view ready for the next parameter to use instead
        if isinstance(converter, Greedy):
            # Special case for Greedy[pyvolt.Asset] to consume the attachments iterator
            if issubclass(converter.converter, pyvolt.StatelessAsset):
                return list(attachments)

            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                return await self._transform_greedy_pos(ctx, param, param.required, converter.constructed_converter)
            elif param.kind == param.VAR_POSITIONAL:
                return await self._transform_greedy_var_pos(ctx, param, converter.constructed_converter)
            else:
                # if we're here, then it's a KEYWORD_ONLY param type
                # since this is mostly useless, we'll helpfully transform Greedy[X]
                # into just X and do the parsing that way.
                converter = converter.constructed_converter

        # Try to detect Optional[pyvolt.Asset] or pyvolt.Asset special converter
        if issubclass(converter, pyvolt.StatelessAsset):
            try:
                return next(attachments)
            except StopIteration:
                raise MissingRequiredAttachment(parameter=param)

        if self._is_typing_optional(param.annotation) and issubclass(
            param.annotation.__args__[0], pyvolt.StatelessAsset
        ):
            if attachments.is_empty():
                # I have no idea who would be doing Optional[pyvolt.Asset] = 1
                # but for those cases then 1 should be returned instead of None
                return None if param.default is param.empty else param.default
            return next(attachments)

        if view.eof:
            if param.kind == param.VAR_POSITIONAL:
                raise RuntimeError()  # break the loop
            if param.required:
                if self._is_typing_optional(param.annotation):
                    return None
                if hasattr(converter, '__commands_is_flag__') and converter._can_be_constructible():
                    return await converter._construct_default(ctx)
                raise MissingRequiredArgument(parameter=param)
            return await param.get_default(ctx)

        previous = view.index
        if consume_rest_is_special:
            ctx.current_argument = argument = view.read_rest().strip()
        else:
            try:
                ctx.current_argument = argument = view.get_quoted_word()
            except ArgumentParsingError as exc:
                if self._is_typing_optional(param.annotation):
                    view.index = previous
                    return None if param.required else await param.get_default(ctx)
                else:
                    raise exc
        view.previous = previous

        # type-checker fails to narrow argument
        return await run_converters(ctx, converter, argument, param)  # type: ignore

    async def _transform_greedy_pos(
        self, ctx: Context[BotT], param: Parameter, required: bool, converter: typing.Any
    ) -> typing.Any:
        view = ctx.view
        result = []
        while not view.eof:
            # for use with a manual undo
            previous = view.index

            view.skip_ws()
            try:
                ctx.current_argument = argument = view.get_quoted_word()
                value = await run_converters(ctx, converter, argument, param)  # type: ignore
            except (CommandError, ArgumentParsingError):
                view.index = previous
                break
            else:
                result.append(value)

        if not result and not required:
            return await param.get_default(ctx)
        return result

    async def _transform_greedy_var_pos(
        self, ctx: Context[BotT], param: Parameter, converter: typing.Any
    ) -> typing.Any:
        view = ctx.view
        previous = view.index
        try:
            ctx.current_argument = argument = view.get_quoted_word()
            value = await run_converters(ctx, converter, argument, param)  # type: ignore
        except (CommandError, ArgumentParsingError):
            view.index = previous
            raise RuntimeError() from None  # break loop
        else:
            return value

    @property
    def clean_params(self) -> dict[str, Parameter]:
        """Dict[:class:`str`, :class:`Parameter`]:
        Retrieves the parameter dictionary without the context or self parameters.

        Useful for inspecting signature.
        """
        return self.params.copy()

    @property
    def cooldown(self) -> Cooldown | None:
        """Optional[:class:`~pyvolt.ext.commands.Cooldown`]: The cooldown of a command when invoked
        or ``None`` if the command doesn't have a registered cooldown.
        """
        return self._buckets._cooldown

    @property
    def full_parent_name(self) -> str:
        """:class:`str`: Retrieves the fully qualified parent command name.

        This the base command name required to execute it. For example,
        in ``?one two three`` the parent name would be ``one two``.
        """
        entries = []
        command = self
        # command.parent is type-hinted as GroupMixin some attributes are resolved via MRO
        while command.parent is not None:  # type: ignore
            command = command.parent  # type: ignore
            entries.append(command.name)  # type: ignore

        return ' '.join(reversed(entries))

    @property
    def parents(self) -> list[Group[typing.Any, ..., typing.Any]]:
        """List[:class:`Group`]: Retrieves the parents of this command.

        If the command has no parents then it returns an empty :class:`list`.

        For example in commands ``?a b c test``, the parents are ``[c, b, a]``.

        .. versionadded:: 1.1
        """
        entries = []
        command = self
        while command.parent is not None:  # type: ignore
            command = command.parent  # type: ignore
            entries.append(command)

        return entries

    @property
    def root_parent(self) -> Group[typing.Any, ..., typing.Any] | None:
        """Optional[:class:`Group`]: Retrieves the root parent of this command.

        If the command has no parents then it returns ``None``.

        For example in commands ``?a b c test``, the root parent is ``a``.
        """
        if not self.parent:
            return None
        return self.parents[-1]

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Retrieves the fully qualified command name.

        This is the full parent name with the command name as well.
        For example, in ``?one two three`` the qualified name would be
        ``one two three``.
        """

        parent = self.full_parent_name
        if parent:
            return parent + ' ' + self.name
        else:
            return self.name

    def __str__(self) -> str:
        return self.qualified_name

    async def _parse_arguments(self, ctx: Context[BotT]) -> None:
        ctx.args = [ctx] if self.gear is None else [self.gear, ctx]
        ctx.kwargs = {}
        args = ctx.args
        kwargs = ctx.kwargs
        attachments = _AssetIterator(ctx.message.attachments)

        view = ctx.view
        iterator = iter(self.params.items())

        for name, param in iterator:
            ctx.current_parameter = param
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                transformed = await self.transform(ctx, param, attachments)
                args.append(transformed)
            elif param.kind == param.KEYWORD_ONLY:
                # kwarg only param denotes "consume rest" semantics
                if self.rest_is_raw:
                    ctx.current_argument = argument = view.read_rest()
                    kwargs[name] = await run_converters(ctx, param.converter, argument, param)
                else:
                    kwargs[name] = await self.transform(ctx, param, attachments)
                break
            elif param.kind == param.VAR_POSITIONAL:
                if view.eof and self.require_var_positional:
                    raise MissingRequiredArgument(parameter=param)
                while not view.eof:
                    try:
                        transformed = await self.transform(ctx, param, attachments)
                        args.append(transformed)
                    except RuntimeError:
                        break

        if not self.ignore_extra and not view.eof:
            raise TooManyArguments('Too many arguments passed to ' + self.qualified_name)

    async def call_before_hooks(self, ctx: Context[BotT], /) -> None:
        # now that we're done preparing we can call the pre-command hooks
        # first, call the command local hook:
        gear = self.gear
        if self._before_invoke is not None:
            # should be gear if @commands.before_invoke is used
            instance = getattr(self._before_invoke, '__self__', gear)
            # __self__ only exists for methods, not functions
            # however, if @command.before_invoke is used, it will be a function
            if instance:
                await self._before_invoke(instance, ctx)  # type: ignore
            else:
                await self._before_invoke(ctx)  # type: ignore

        # call the gear local hook if applicable:
        if gear is not None:
            hook = Gear._get_overridden_method(gear.gear_before_invoke)
            if hook is not None:
                await hook(ctx)

        # call the bot global hook if necessary
        hook = ctx.bot._before_invoke
        if hook is not None:
            await hook(ctx)

    async def call_after_hooks(self, ctx: Context[BotT], /) -> None:
        gear = self.gear
        if self._after_invoke is not None:
            instance = getattr(self._after_invoke, '__self__', gear)
            if instance:
                await self._after_invoke(instance, ctx)  # type: ignore
            else:
                await self._after_invoke(ctx)  # type: ignore

        # call the gear local hook if applicable:
        if gear is not None:
            hook = Gear._get_overridden_method(gear.gear_after_invoke)
            if hook is not None:
                await hook(ctx)

        hook = ctx.bot._after_invoke
        if hook is not None:
            await hook(ctx)

    def _prepare_cooldowns(self, ctx: Context[BotT], /) -> None:
        if self._buckets.valid:
            dt = ctx.message.edited_at or ctx.message.created_at
            current = dt.replace(tzinfo=timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(ctx, current)
            if bucket is not None:
                retry_after = bucket.update_rate_limit(current)
                if retry_after:
                    raise CommandOnCooldown(bucket, retry_after, self._buckets.type)  # type: ignore

    async def prepare(self, ctx: Context[BotT], /) -> None:
        ctx.command = self

        if not await self.can_run(ctx):
            raise CheckFailure(f'The check functions for command {self.qualified_name} failed.')

        if self._max_concurrency is not None:
            # For this application, context can be duck-typed as a Message
            await self._max_concurrency.acquire(ctx)

        try:
            if self.cooldown_after_parsing:
                await self._parse_arguments(ctx)
                self._prepare_cooldowns(ctx)
            else:
                self._prepare_cooldowns(ctx)
                await self._parse_arguments(ctx)

            await self.call_before_hooks(ctx)
        except:
            if self._max_concurrency is not None:
                await self._max_concurrency.release(ctx)
            raise

    async def invoke(self, ctx: Context[BotT], /) -> None:
        await self.prepare(ctx)

        # terminate the invoked_subcommand chain.
        # since we're in a regular command (and not a group) then
        # the invoked subcommand is None.
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = hooked_wrapped_callback(self, ctx, self.callback)  # type: ignore
        await injected(*ctx.args, **ctx.kwargs)  # type: ignore

    async def reinvoke(self, ctx: Context[BotT], /, *, call_hooks: bool = False) -> None:
        ctx.command = self
        await self._parse_arguments(ctx)

        if call_hooks:
            await self.call_before_hooks(ctx)

        ctx.invoked_subcommand = None
        try:
            await self.callback(*ctx.args, **ctx.kwargs)  # type: ignore
        except:
            ctx.command_failed = True
            raise
        finally:
            if call_hooks:
                await self.call_after_hooks(ctx)

    def error(self, coro: Error[GearT, ContextT], /) -> Error[GearT, ContextT]:
        """A decorator that registers a coroutine as a local error handler.

        A local error handler is an :func:`.on_command_error` event limited to
        a single command. However, the :func:`.on_command_error` is still
        invoked afterwards as the catch-all.

        Parameters
        ----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the local error handler.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler must be a coroutine.')

        self.on_error: Error[GearT, typing.Any] = coro
        return coro

    def has_error_handler(self) -> bool:
        """:class:`bool`: Checks whether the command has an error handler registered."""
        return hasattr(self, 'on_error')

    def before_invoke(self, coro: Hook[GearT, ContextT], /) -> Hook[GearT, ContextT]:
        """A decorator that registers a coroutine as a pre-invoke hook.

        A pre-invoke hook is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.

        This pre-invoke hook takes a sole parameter, a :class:`.Context`.

        See :meth:`.Bot.before_invoke` for more info.

        Parameters
        ----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the pre-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The pre-invoke hook must be a coroutine.')

        self._before_invoke = coro
        return coro

    def after_invoke(self, coro: Hook[GearT, ContextT], /) -> Hook[GearT, ContextT]:
        """A decorator that registers a coroutine as a post-invoke hook.

        A post-invoke hook is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required.

        This post-invoke hook takes a sole parameter, a :class:`.Context`.

        See :meth:`.Bot.after_invoke` for more info.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the post-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The post-invoke hook must be a coroutine.')

        self._after_invoke = coro
        return coro

    def _is_typing_optional(self, annotation: type[T | None], /) -> bool:
        return getattr(annotation, '__origin__', None) is typing.Union and type(None) in annotation.__args__  # type: ignore

    @property
    def signature(self) -> str:
        """:class:`str`: Returns a POSIX-like signature useful for help command output."""
        if self.usage is not None:
            return self.usage

        params = self.clean_params
        if not params:
            return ''

        result = []
        for param in params.values():
            name = param.displayed_name or param.name

            greedy = isinstance(param.converter, Greedy)
            optional = False  # postpone evaluation of if it's an optional argument

            annotation: typing.Any = param.converter.converter if greedy else param.converter
            origin = getattr(annotation, '__origin__', None)
            if not greedy and origin is typing.Union:
                none_cls = type(None)
                union_args = annotation.__args__
                optional = union_args[-1] is none_cls
                if len(union_args) == 2 and optional:
                    annotation = union_args[0]
                    origin = getattr(annotation, '__origin__', None)

            if issubclass(annotation, pyvolt.Asset):
                # For pyvolt.Asset we need to signal to the user that it's an attachment
                # It's not exactly pretty but it's enough to differentiate
                if optional:
                    result.append(f'[{name} (upload a file)]')
                elif greedy:
                    result.append(f'[{name} (upload files)]...')
                else:
                    result.append(f'<{name} (upload a file)>')
                continue

            # for typing.Literal[...], typing.Optional[typing.Literal[...]], and Greedy[typing.Literal[...]], the
            # parameter signature is a literal list of it's values
            if origin is typing.Literal:
                name = '|'.join(f'"{v}"' if isinstance(v, str) else str(v) for v in annotation.__args__)
            if not param.required:
                # We don't want None or '' to trigger the [name=value] case and instead it should
                # do [name] since [name=None] or [name=] are not exactly useful for the user.
                if param.displayed_default:
                    result.append(
                        f'[{name}={param.displayed_default}]'
                        if not greedy
                        else f'[{name}={param.displayed_default}]...'
                    )
                    continue
                else:
                    result.append(f'[{name}]')

            elif param.kind == param.VAR_POSITIONAL:
                if self.require_var_positional:
                    result.append(f'<{name}...>')
                else:
                    result.append(f'[{name}...]')
            elif greedy:
                result.append(f'[{name}]...')
            elif optional:
                result.append(f'[{name}]')
            else:
                result.append(f'<{name}>')

        return ' '.join(result)

    async def can_run(self, ctx: Context[BotT], /) -> bool:
        """|coro|

        Checks if the command can be executed by checking all the predicates
        inside the :attr:`~Command.checks` attribute. This also checks whether the
        command is disabled.

        .. versionchanged:: 1.3
            Checks whether the command is disabled or not

        .. versionchanged:: 2.0

            ``ctx`` parameter is now positional-only.

        Parameters
        -----------
        ctx: :class:`.Context`
            The ctx of the command currently being invoked.

        Raises
        -------
        :class:`CommandError`
            Any command error that was raised during a check call will be propagated
            by this function.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the command can be invoked.
        """

        if not self.enabled:
            raise DisabledCommand(f'{self.name} command is disabled')

        original = ctx.command
        ctx.command = self

        try:
            if not await ctx.bot.can_run(ctx):
                raise CheckFailure(f'The global check functions for command {self.qualified_name} failed.')

            gear = self.gear
            if gear is not None:
                local_check = Gear._get_overridden_method(gear.gear_check)
                if local_check is not None:
                    ret = await pyvolt.utils.maybe_coroutine(local_check, ctx)
                    if not ret:
                        return False

            predicates = self.checks
            if not predicates:
                # since we have no checks, then we just return True.
                return True

            for predicate in predicates:
                tmp = predicate(ctx)
                if inspect.isawaitable(tmp):
                    tmp = await tmp

                if not tmp:
                    return False

            return True
        finally:
            ctx.command = original


class GroupMixin(typing.Generic[GearT]):
    """A mixin that implements common functionality for classes that behave
    similar to :class:`.Group` and are allowed to register commands.

    Attributes
    -----------
    all_commands: :class:`dict`
        A mapping of command name to :class:`.Command`
        objects.
    case_insensitive: :class:`bool`
        Whether the commands should be case insensitive. Defaults to ``False``.
    """

    def __init__(self, /, *args: typing.Any, **kwargs: typing.Any) -> None:
        case_insensitive = kwargs.get('case_insensitive', False)
        self.all_commands: dict[str, Command[GearT, ..., typing.Any]] = (
            _CaseInsensitiveDict() if case_insensitive else {}
        )
        self.case_insensitive: bool = case_insensitive
        super().__init__(*args, **kwargs)

    @property
    def commands(self) -> set[Command[GearT, ..., typing.Any]]:
        """Set[:class:`.Command`]: A unique set of commands without aliases that are registered."""
        return set(self.all_commands.values())

    def recursively_remove_all_commands(self) -> None:
        for command in self.all_commands.copy().values():
            if isinstance(command, GroupMixin):
                command.recursively_remove_all_commands()
            self.remove_command(command.name)

    def add_command(self, command: Command[GearT, ..., typing.Any], /) -> None:
        """Adds a :class:`.Command` into the internal list of commands.

        This is usually not called, instead the :meth:`~.GroupMixin.command` or
        :meth:`~.GroupMixin.group` shortcut decorators are used instead.

        Parameters
        -----------
        command: :class:`Command`
            The command to add.

        Raises
        -------
        CommandRegistrationError
            If the command or its alias is already registered by different command.
        TypeError
            If the command passed is not a subclass of :class:`.Command`.
        """

        if not isinstance(command, Command):
            raise TypeError('The command passed must be a subclass of Command')

        if isinstance(self, Command):
            command.parent = self

        if command.name in self.all_commands:
            raise CommandRegistrationError(name=command.name)

        self.all_commands[command.name] = command
        for alias in command.aliases:
            if alias in self.all_commands:
                self.remove_command(command.name)
                raise CommandRegistrationError(name=alias, alias_conflict=True)
            self.all_commands[alias] = command

    def remove_command(self, name: str, /) -> Command[GearT, ..., typing.Any] | None:
        """Remove a :class:`.Command` from the internal list
        of commands.

        This could also be used as a way to remove aliases.

        Parameters
        -----------
        name: :class:`str`
            The name of the command to remove.

        Returns
        --------
        Optional[:class:`.Command`]
            The command that was removed. If the name is not valid then
            ``None`` is returned instead.
        """
        command = self.all_commands.pop(name, None)

        # does not exist
        if command is None:
            return None

        if name in command.aliases:
            # we're removing an alias so we don't want to remove the rest
            return command

        # we're not removing the alias so let's delete the rest of them.
        for alias in command.aliases:
            cmd = self.all_commands.pop(alias, None)
            # in the case of a CommandRegistrationError, an alias might conflict
            # with an already existing command. If this is the case, we want to
            # make sure the pre-existing command is not removed.
            if cmd is not None and cmd != command:
                self.all_commands[alias] = cmd
        return command

    def walk_commands(self) -> Generator[Command[GearT, ..., typing.Any], None, None]:
        """An iterator that recursively walks through all commands and subcommands.

        Yields
        ------
        Union[:class:`.Command`, :class:`.Group`]
            A command or group from the internal list of commands.
        """
        for command in self.commands:
            yield command
            if isinstance(command, GroupMixin):
                yield from command.walk_commands()

    def get_command(self, name: str, /) -> Command[GearT, ..., typing.Any] | None:
        """Get a :class:`.Command` from the internal list
        of commands.

        This could also be used as a way to get aliases.

        The name could be fully qualified (e.g. ``'foo bar'``) will get
        the subcommand ``bar`` of the group command ``foo``. If a
        subcommand is not found then ``None`` is returned just as usual.

        Parameters
        -----------
        name: :class:`str`
            The name of the command to get.

        Returns
        --------
        Optional[:class:`Command`]
            The command that was requested. If not found, returns ``None``.
        """

        # fast path, no space in name.
        if ' ' not in name:
            return self.all_commands.get(name)

        names = name.split()
        if not names:
            return None
        obj = self.all_commands.get(names[0])
        if not isinstance(obj, GroupMixin):
            return obj

        for name in names[1:]:
            try:
                obj = obj.all_commands[name]  # type: ignore
            except (AttributeError, KeyError):
                return None

        return obj

    @typing.overload
    def command(
        self: GroupMixin[GearT],
        name: str = ...,
        *args: typing.Any,
        cls: None = ...,
        **kwargs: typing.Any,
    ) -> Callable[
        [
            Callable[typing.Concatenate[GearT, ContextT, P], Coroutine[typing.Any, typing.Any, T]]
            | Callable[typing.Concatenate[ContextT, P], Coroutine[typing.Any, typing.Any, T]]
        ],
        Command[GearT, P, T],
    ]: ...

    @typing.overload
    def command(
        self: GroupMixin[GearT],
        name: str = ...,
        *args: typing.Any,
        cls: type[CommandT] = ...,  # type: ignore
        **kwargs: typing.Any,
    ) -> Callable[
        [
            Callable[typing.Concatenate[GearT, ContextT, P], Coroutine[typing.Any, typing.Any, T]]
            | Callable[typing.Concatenate[ContextT, P], Coroutine[typing.Any, typing.Any, T]]
        ],
        CommandT,
    ]: ...

    def command(
        self,
        name: str = MISSING,
        *args: typing.Any,
        cls: type[Command[typing.Any, ..., typing.Any]] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Any:
        """A shortcut decorator that invokes :func:`~pyvolt.ext.commands.command` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.

        Returns
        --------
        Callable[..., :class:`Command`]
            A decorator that converts the provided method into a Command, adds it to the bot, then returns it.
        """

        def decorator(func):
            kwargs.setdefault('parent', self)
            result = command(name=name, cls=cls, *args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    @typing.overload
    def group(
        self: GroupMixin[GearT],
        name: str = ...,
        *args: typing.Any,
        cls: type[GroupT] = ...,  # type: ignore
        **kwargs: typing.Any,
    ) -> Callable[
        [
            Callable[typing.Concatenate[GearT, ContextT, P], Coroutine[typing.Any, typing.Any, T]]
            | Callable[typing.Concatenate[ContextT, P], Coroutine[typing.Any, typing.Any, T]]
        ],
        GroupT,
    ]: ...

    @typing.overload
    def group(
        self: GroupMixin[GearT],
        name: str = ...,
        *args: typing.Any,
        cls: None = ...,
        **kwargs: typing.Any,
    ) -> Callable[
        [
            Callable[typing.Concatenate[GearT, ContextT, P], Coroutine[typing.Any, typing.Any, T]]
            | Callable[typing.Concatenate[ContextT, P], Coroutine[typing.Any, typing.Any, T]]
        ],
        Group[GearT, P, T],
    ]: ...

    def group(
        self,
        name: str = MISSING,
        *args: typing.Any,
        cls: type[Group[typing.Any, ..., typing.Any]] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Any:
        """A shortcut decorator that invokes :func:`.group` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.

        Returns
        --------
        Callable[..., :class:`Group`]
            A decorator that converts the provided method into a Group, adds it to the bot, then returns it.
        """

        def decorator(func, /):
            kwargs.setdefault('parent', self)
            result = group(name=name, cls=cls, *args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator


class Group(GroupMixin[GearT], Command[GearT, P, T]):
    """A class that implements a grouping protocol for commands to be
    executed as subcommands.

    This class is a subclass of :class:`.Command` and thus all options
    valid in :class:`.Command` are valid in here as well.

    Attributes
    -----------
    invoke_without_command: :class:`bool`
        Indicates if the group callback should begin parsing and
        invocation only if no subcommand was found. Useful for
        making it an error handling function to tell the user that
        no subcommand was found or to have different functionality
        in case no subcommand was found. If this is ``False``, then
        the group callback will always be invoked first. This means
        that the checks and the parsing dictated by its parameters
        will be executed. Defaults to ``False``.
    case_insensitive: :class:`bool`
        Indicates if the group's commands should be case insensitive.
        Defaults to ``False``.
    """

    def __init__(self, /, *args: typing.Any, **attrs: typing.Any) -> None:
        self.invoke_without_command: bool = attrs.pop('invoke_without_command', False)
        super().__init__(*args, **attrs)

    def copy(self) -> Self:
        """Creates a copy of this :class:`Group`.

        Returns
        --------
        :class:`Group`
            A new instance of this group.
        """
        ret = super().copy()
        for cmd in self.commands:
            ret.add_command(cmd.copy())
        return ret

    async def invoke(self, ctx: Context[BotT], /) -> None:
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            await self.prepare(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            injected = hooked_wrapped_callback(self, ctx, self.callback)  # type: ignore
            await injected(*ctx.args, **ctx.kwargs)  # type: ignore

        ctx.invoked_parents.append(ctx.label)  # type: ignore

        if trigger and ctx.invoked_subcommand:
            ctx.label = trigger
            await ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().invoke(ctx)

    async def reinvoke(self, ctx: Context[BotT], /, *, call_hooks: bool = False) -> None:
        ctx.invoked_subcommand = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            ctx.command = self
            await self._parse_arguments(ctx)

            if call_hooks:
                await self.call_before_hooks(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            try:
                await self.callback(*ctx.args, **ctx.kwargs)  # type: ignore
            except:
                ctx.command_failed = True
                raise
            finally:
                if call_hooks:
                    await self.call_after_hooks(ctx)

        ctx.invoked_parents.append(ctx.label)  # type: ignore

        if trigger and ctx.invoked_subcommand:
            ctx.label = trigger
            await ctx.invoked_subcommand.reinvoke(ctx, call_hooks=call_hooks)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().reinvoke(ctx, call_hooks=call_hooks)


# Decorators

if typing.TYPE_CHECKING:
    # Using a class to emulate a function allows for overloading the inner function in the decorator.

    class _CommandDecorator:
        @typing.overload
        def __call__(
            self, func: Callable[typing.Concatenate[GearT, ContextT, P], Coroutine[typing.Any, typing.Any, T]], /
        ) -> Command[GearT, P, T]: ...

        @typing.overload
        def __call__(
            self, func: Callable[typing.Concatenate[ContextT, P], Coroutine[typing.Any, typing.Any, T]], /
        ) -> Command[None, P, T]: ...

        def __call__(self, func: Callable[..., Coroutine[typing.Any, typing.Any, T]], /) -> typing.Any: ...

    class _GroupDecorator:
        @typing.overload
        def __call__(
            self, func: Callable[typing.Concatenate[GearT, ContextT, P], Coroutine[typing.Any, typing.Any, T]], /
        ) -> Group[GearT, P, T]: ...

        @typing.overload
        def __call__(
            self, func: Callable[typing.Concatenate[ContextT, P], Coroutine[typing.Any, typing.Any, T]], /
        ) -> Group[None, P, T]: ...

        def __call__(self, func: Callable[..., Coroutine[typing.Any, typing.Any, T]], /) -> typing.Any: ...


@typing.overload
def command(
    name: str | None = None,
    **attrs: typing.Any,
) -> _CommandDecorator: ...


@typing.overload
def command(
    name: str | None = None,
    cls: type[CommandT] | None = ...,  # type: ignore
    **attrs: typing.Any,
) -> Callable[
    [
        Callable[typing.Concatenate[ContextT, P], Coroutine[typing.Any, typing.Any, typing.Any]]
        | Callable[typing.Concatenate[GearT, ContextT, P], Coroutine[typing.Any, typing.Any, typing.Any]]  # type: ignore
    ],
    CommandT,
]: ...


def command(
    name: str | None = None,
    cls: type[Command[typing.Any, ..., typing.Any]] | None = None,
    **attrs: typing.Any,
) -> typing.Any:
    """A decorator that transforms a function into a :class:`.Command`
    or if called with :func:`.group`, :class:`.Group`.

    By default the ``help`` attribute is received automatically from the
    docstring of the function and is cleaned up with the use of
    ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
    into :class:`str` using utf-8 encoding.

    All checks added using the :func:`.check` & co. decorators are added into
    the function. There is no way to supply your own checks through this
    decorator.

    Parameters
    -----------
    name: :class:`str`
        The name to create the command with. By default this uses the
        function name unchanged.
    cls
        The class to construct with. By default this is :class:`.Command`.
        You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted
        by ``cls``.

    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    if cls is None:
        cls = Command

    def decorator(func, /):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator


@typing.overload
def group(
    name: str | None = ...,
    **attrs: typing.Any,
) -> _GroupDecorator: ...


@typing.overload
def group(
    name: str | None = ...,
    cls: type[GroupT] | None = None,
    **attrs: typing.Any,
) -> Callable[
    [
        Callable[typing.Concatenate[GearT, ContextT, P], Coroutine[typing.Any, typing.Any, typing.Any]]  # type: ignore
        | Callable[typing.Concatenate[ContextT, P], Coroutine[typing.Any, typing.Any, typing.Any]]
    ],
    GroupT,
]: ...


def group(
    name: str | None = None,
    cls: type[Group[typing.Any, ..., typing.Any]] | None = None,
    **attrs: typing.Any,
) -> typing.Any:
    """A decorator that transforms a function into a :class:`.Group`.

    This is similar to the :func:`~discord.ext.commands.command` decorator but the ``cls``
    parameter is set to :class:`Group` by default.
    """
    if cls is None:
        cls = Group

    return command(name=name, cls=cls, **attrs)
