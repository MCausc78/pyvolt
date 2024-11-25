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

import inspect
from operator import attrgetter
import typing

from pyvolt.utils import MISSING

from .errors import NoPrivateMessage
from .converter import ServerConverter

from pyvolt import (
    Member,
    User,
    SavedMessagesChannel,
    DMChannel,
    GroupChannel,
    TextChannel,
    VoiceChannel,
)

if typing.TYPE_CHECKING:
    from collections import OrderedDict
    from typing_extensions import Self

    from pyvolt import Server

    from .context import Context

__all__ = (
    'Parameter',
    'parameter',
    'param',
    'Author',
    'CurrentChannel',
    'CurrentServer',
)


ParamKinds = typing.Literal[
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.VAR_POSITIONAL,
    inspect.Parameter.KEYWORD_ONLY,
    inspect.Parameter.VAR_KEYWORD,
]

EMPTY: typing.Any = inspect.Parameter.empty


def _gen_property(name: str, /) -> property:
    attr = f'_{name}'
    return property(
        attrgetter(attr),
        lambda self, value: setattr(self, attr, value),
        doc=f"The parameter's {name}.",
    )


class Parameter(inspect.Parameter):
    r"""A class that stores information on a :class:`Command`\'s parameter.

    This is a subclass of :class:`inspect.Parameter`.
    """

    __slots__ = (
        '_displayed_default',
        '_description',
        '_fallback',
        '_displayed_name',
    )

    def __init__(
        self,
        *,
        name: str,
        kind: ParamKinds,
        default: typing.Any = EMPTY,
        annotation: typing.Any = EMPTY,
        description: str = EMPTY,
        displayed_default: str = EMPTY,
        displayed_name: str = EMPTY,
    ) -> None:
        super().__init__(name=name, kind=kind, default=default, annotation=annotation)
        self._name: str = name
        self._kind: ParamKinds = kind
        self._description: str = description
        self._default: typing.Any = default
        self._annotation: typing.Any = annotation
        self._displayed_default: str = displayed_default
        self._fallback = False
        self._displayed_name: str = displayed_name

    def replace(  # type: ignore # TODO: Fix
        self,
        *,
        name: str = MISSING,
        kind: ParamKinds = MISSING,
        default: typing.Any = MISSING,
        annotation: typing.Any = MISSING,
        description: str = MISSING,
        displayed_default: typing.Any = MISSING,
        displayed_name: typing.Any = MISSING,
    ) -> Self:
        if name is MISSING:
            name = self._name
        if kind is MISSING:
            kind = self._kind
        if default is MISSING:
            default = self._default
        if annotation is MISSING:
            annotation = self._annotation
        if description is MISSING:
            description = self._description
        if displayed_default is MISSING:
            displayed_default = self._displayed_default
        if displayed_name is MISSING:
            displayed_name = self._displayed_name

        return self.__class__(
            name=name,
            kind=kind,
            default=default,
            annotation=annotation,
            description=description,
            displayed_default=displayed_default,
            displayed_name=displayed_name,
        )

    if not typing.TYPE_CHECKING:  # this is to prevent anything breaking if inspect internals change
        name = _gen_property('name')
        kind = _gen_property('kind')
        default = _gen_property('default')
        annotation = _gen_property('annotation')

    @property
    def required(self) -> bool:
        """:class:`bool`: Whether this parameter is required."""
        return self.default is EMPTY

    @property
    def converter(self) -> typing.Any:
        """The converter that should be used for this parameter."""
        if self.annotation is EMPTY:
            return type(self.default) if self.default not in (EMPTY, None) else str

        return self.annotation

    @property
    def description(self) -> str | None:
        """Optional[:class:`str`]: The description of this parameter."""
        return self._description if self._description is not EMPTY else None

    @property
    def displayed_default(self) -> str | None:
        """Optional[:class:`str`]: The displayed default in :class:`Command.signature`."""
        if self._displayed_default is not EMPTY:
            return self._displayed_default

        if self.required:
            return None

        if callable(self.default) or self.default is None:
            return None

        return str(self.default)

    @property
    def displayed_name(self) -> str | None:
        """Optional[:class:`str`]: The name that is displayed to the user."""
        return self._displayed_name if self._displayed_name is not EMPTY else None

    async def get_default(self, ctx: Context[typing.Any], /) -> typing.Any:
        """|coro|

        Gets this parameter's default value.

        Parameters
        ----------
        ctx: :class:`Context`
            The invocation context that is used to get the default argument.
        """
        # pre-condition: required is False
        if callable(self.default):
            ret = self.default(ctx)
            if inspect.isawaitable(ret):
                ret = await ret
            return ret
        return self.default


def parameter(
    *,
    converter: typing.Any = EMPTY,
    default: typing.Any = EMPTY,
    description: str = EMPTY,
    displayed_default: str = EMPTY,
    displayed_name: str = EMPTY,
) -> typing.Any:
    r"""parameter(\*, converter=..., default=..., description=..., displayed_default=..., displayed_name=...)

    A way to assign custom metadata for a :class:`Command`\'s parameter.

    Examples
    --------
    A custom default can be used to have late binding behaviour.

    .. code-block:: python3

        @bot.command()
        async def wave(ctx, to: pyvolt.User = commands.parameter(default=lambda ctx: ctx.author)):
            await ctx.send(f'Hello {to.mention} :wave:')

    Parameters
    ----------
    converter: Any
        The converter to use for this parameter, this replaces the annotation at runtime which is transparent to type checkers.
    default: Any
        The default value for the parameter, if this is a :term:`callable` or a |coroutine_link|_ it is called with a
        positional :class:`Context` argument.
    description: :class:`str`
        The description of this parameter.
    displayed_default: :class:`str`
        The displayed default in :attr:`Command.signature`.
    displayed_name: :class:`str`
        The name that is displayed to the user.
    """
    if isinstance(default, Parameter):
        if displayed_default is EMPTY:
            displayed_default = default._displayed_default

        default = default._default

    return Parameter(
        name='empty',
        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
        annotation=converter,
        default=default,
        description=description,
        displayed_default=displayed_default,
        displayed_name=displayed_name,
    )


class ParameterAlias(typing.Protocol):
    def __call__(
        self,
        *,
        converter: typing.Any = EMPTY,
        default: typing.Any = EMPTY,
        description: str = EMPTY,
        displayed_default: str = EMPTY,
        displayed_name: str = EMPTY,
    ) -> typing.Any: ...


param: ParameterAlias = parameter
r"""param(\*, converter=..., default=..., description=..., displayed_default=..., displayed_name=...)

An alias for :func:`parameter`.
"""

# some handy defaults
Author = parameter(
    default=attrgetter('author'),
    displayed_default='<you>',
    converter=Member | User,
)
Author._fallback = True

CurrentChannel = parameter(
    default=attrgetter('channel'),
    displayed_default='<this channel>',
    converter=SavedMessagesChannel | DMChannel | GroupChannel | TextChannel | VoiceChannel,
)
CurrentChannel._fallback = True


def default_server(ctx: Context[typing.Any], /) -> Server:
    server = ctx.server
    if server is None:
        raise NoPrivateMessage()
    return server


CurrentServer = parameter(
    default=default_server,
    displayed_default='<this server>',
    converter=ServerConverter,
)
CurrentServer._fallback = True


class Signature(inspect.Signature):
    _parameter_cls = Parameter
    parameters: OrderedDict[str, Parameter]
