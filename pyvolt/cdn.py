"""
The MIT License (MIT)

Copyright (c) 2024-present MCausc78

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

import abc
import aiohttp
from attrs import define, field
import io
import logging
import typing
from urllib.parse import quote

from . import utils
from .core import __version__ as version
from .errors import HTTPException

if typing.TYPE_CHECKING:
    from .enums import AssetMetadataType
    from .state import State
    from typing_extensions import Self


_L = logging.getLogger(__name__)


@define(slots=True)
class AssetMetadata:
    """Metadata associated with a file."""

    type: AssetMetadataType = field(repr=True, kw_only=True, eq=True)
    width: int | None = field(repr=True, kw_only=True, eq=True)
    height: int | None = field(repr=True, kw_only=True, eq=True)


Tag = typing.Literal['icons', 'banners', 'emojis', 'backgrounds', 'avatars', 'attachments']


@define(slots=True)
class StatelessAsset:
    """Stateless representation of a file on Revolt generated by Autumn.

    For better user experience, prefer using `parent.foo` rather than `parent.internal_foo`.
    """

    id: str = field(repr=True, kw_only=True)
    """Unique ID."""

    filename: str = field(repr=True, kw_only=True)
    """Original filename."""

    metadata: AssetMetadata = field(repr=True, kw_only=True)
    """Parsed metadata of this file."""

    content_type: str = field(repr=True, kw_only=True)
    """Raw content type of this file."""

    size: int = field(repr=True, kw_only=True)
    """Size of this file (in bytes)."""

    deleted: bool = field(repr=True, kw_only=True)
    """Whether this file was deleted."""

    reported: bool = field(repr=True, kw_only=True)
    """Whether this file was reported."""

    message_id: str | None = field(repr=True, kw_only=True)
    """ID of the message this file is associated with."""

    user_id: str | None = field(repr=True, kw_only=True)
    """ID of the user this file is associated with."""

    server_id: str | None = field(repr=True, kw_only=True)
    """ID of the server this file is associated with."""

    object_id: str | None = field(repr=True, kw_only=True)
    """ID of the object this file is associated with."""

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessAsset) and self.id == other.id

    def _stateful(self, state: State, tag: Tag) -> Asset:
        return Asset(
            id=self.id,
            filename=self.filename,
            metadata=self.metadata,
            content_type=self.content_type,
            size=self.size,
            deleted=self.deleted,
            reported=self.reported,
            message_id=self.message_id,
            user_id=self.user_id,
            server_id=self.server_id,
            object_id=self.object_id,
            # Stateful properties
            state=state,
            tag=tag,
        )


@define(slots=True)
class Asset(StatelessAsset):
    state: State = field(repr=False, hash=False, kw_only=True, eq=False)
    tag: Tag = field(repr=True, kw_only=True)

    def __hash__(self) -> int:
        return hash(self.id)

    def url(
        self,
        *,
        size: int | None = None,
        width: int | None = None,
        height: int | None = None,
        max_side: int | None = None,
    ) -> str:
        """:class:`str`: The asset URL."""
        return self.state.cdn_client.url_for(
            self.id, self.tag, size=size, width=width, height=height, max_side=max_side
        )

    async def read(
        self,
        *,
        size: int | None = None,
        width: int | None = None,
        height: int | None = None,
        max_side: int | None = None,
    ) -> bytes:
        """|coro|

        Read asset contents.

        Returns
        -------
        :class:`bytes`
            The asset contents.
        """
        return await self.state.cdn_client.read(
            self.tag, self.id, size=size, width=width, height=height, max_side=max_side
        )


class Resource(abc.ABC):
    @abc.abstractmethod
    async def upload(self, cdn_client: CDNClient, tag: Tag, /) -> str:
        """Uploads the resource to CDN, then returns ID."""
        ...


_cdn_session: aiohttp.ClientSession | None = None

DEFAULT_USER_AGENT = f'pyvolt CDN client (https://github.com/MCausc78/pyvolt, {version})'


def _get_session() -> aiohttp.ClientSession:
    global _cdn_session
    if _cdn_session:
        return _cdn_session
    _cdn_session = aiohttp.ClientSession()
    return _cdn_session


Content = bytes | str | bytearray | io.IOBase


def resolve_content(content: Content) -> bytes | io.IOBase:
    if isinstance(content, bytearray):
        return bytes(content)
    elif isinstance(content, str):
        return content.encode()
    else:
        return content


class Upload(Resource):
    """Represents a file upload.

    Attributes
    ----------
    content: Union[:class:`bytes`, :class:`~io.IOBase`]
        The file contents.
    tag: Optional[Tag]
        The attachment tag. If none, this is determined automatically.
    filename: :class:`str`
        The file name.
    """

    __slots__ = ('tag', 'content', 'filename')

    def __init__(self, content: Content, *, tag: Tag | None = None, filename: str) -> None:
        self.content = resolve_content(content)
        # Pyright sucks massive balls here.
        self.tag: Tag | None = tag
        self.filename = filename

    @classmethod
    def attachment(cls, content: Content, *, filename: str) -> Self:
        return cls(content, tag='attachments', filename=filename)

    @classmethod
    def avatar(cls, content: Content, *, filename: str) -> Self:
        return cls(content, tag='avatars', filename=filename)

    @classmethod
    def background(cls, content: Content, *, filename: str) -> Self:
        return cls(content, tag='backgrounds', filename=filename)

    @classmethod
    def banner(cls, content: Content, *, filename: str) -> Self:
        return cls(content, tag='banners', filename=filename)

    @classmethod
    def emoji(cls, content: Content, *, filename: str) -> Self:
        return cls(content, tag='emojis', filename=filename)

    @classmethod
    def icon(cls, content: Content, *, filename: str) -> Self:
        return cls(content, tag='icons', filename=filename)

    async def upload(self, cdn_client: CDNClient, tag: Tag, /) -> str:
        form = aiohttp.FormData()
        form.add_field('file', self.content, filename=self.filename)

        return await cdn_client.upload(self.tag or tag, form)


ResolvableResource = Resource | str | bytes | tuple[str, Content]


async def resolve_resource(state: State, resolvable: ResolvableResource, *, tag: Tag) -> str:
    if isinstance(resolvable, Resource):
        return await resolvable.upload(state.cdn_client, tag)
    elif isinstance(resolvable, str):
        return resolvable
    elif isinstance(resolvable, bytes):
        return await Upload(resolvable, filename='untitled0.png').upload(state.cdn_client, tag)
        # return await state.cdn_client.upload(Upload(resolvable, filename="untitled0"), tag)
    elif isinstance(resolvable, tuple):
        return await Upload(resolve_content(resolvable[1]), filename=resolvable[0]).upload(state.cdn_client, tag)
        # return await state.cdn_client.upload(Upload(resolve_content(resolvable[1]), filename=resolvable[0]), tag)
    else:
        return ''


class CDNClient:
    __slots__ = (
        '_base',
        '_session',
        'state',
        'user_agent',
    )

    def __init__(
        self,
        *,
        base: str | None = None,
        session: utils.MaybeAwaitableFunc[[CDNClient], aiohttp.ClientSession] | aiohttp.ClientSession,
        state: State,
        user_agent: str | None = None,
    ) -> None:
        if base is None:
            base = 'https://autumn.revolt.chat'

        self._base = base.rstrip('/')
        self._session: utils.MaybeAwaitableFunc[[CDNClient], aiohttp.ClientSession] | aiohttp.ClientSession = session
        self.state: State = state
        self.user_agent: str = user_agent or DEFAULT_USER_AGENT

    @property
    def base(self) -> str:
        return self._base

    async def request(self, method: str, route: str, **kwargs) -> aiohttp.ClientResponse:
        headers: dict[str, typing.Any] = kwargs.pop('headers', {})
        if not kwargs.pop('manual_accept', False):
            headers['accept'] = 'application/json'
        headers['user-agent'] = self.user_agent

        url = self._base + route

        session = self._session
        if callable(session):
            session = await utils._maybe_coroutine(session, self)
            # detect recursion
            if callable(session):
                raise TypeError(f'Expected aiohttp.ClientSession, not {type(session)!r}')
            # Do not call factory on future requests
            self._session = session

        _L.debug('Sending request to %s', route)

        response = await session.request(
            method,
            url,
            headers=headers,
            **kwargs,
        )
        if response.status >= 400:
            j = await utils._json_or_text(response)
            if isinstance(j, dict) and isinstance(j.get('error'), dict):
                error = j['error']
                code = error.get('code')
                reason = error.get('reason')
                description = error.get('description')
                j['type'] = 'Rocket error'
                j['err'] = f'{code} {reason}: {description}'

            from .http import _STATUS_TO_ERRORS

            raise _STATUS_TO_ERRORS.get(response.status, HTTPException)(response, j)
        return response

    def url_for(
        self,
        id: str,
        tag: Tag,
        *,
        size: int | None = None,
        width: int | None = None,
        height: int | None = None,
        max_side: int | None = None,
    ) -> str:
        """:class:`str`: Generates asset URL."""

        url = f'{self._base}/{tag}/{quote(id)}'

        params = []

        if size is not None:
            params.append(f'size={size}')

        if width is not None:
            params.append(f'width={width}')

        if height is not None:
            params.append(f'height={height}')

        if max_side is not None:
            params.append(f'max_side={max_side}')

        if params:
            url += '?' + '&'.join(params)

        return url

    async def read(
        self,
        tag: Tag,
        id: str,
        *,
        size: int | None = None,
        width: int | None = None,
        height: int | None = None,
        max_side: int | None = None,
    ) -> bytes:
        params = {}

        if size is not None:
            params['size'] = size

        if width is not None:
            params['width'] = width

        if height is not None:
            params['height'] = height

        if max_side is not None:
            params['max_side'] = max_side

        response = await self.request('GET', f'/{tag}/{quote(id)}', params=params)
        data = await response.read()
        response.close()
        return data

    async def upload(
        self,
        tag: Tag,
        data: typing.Any,
    ) -> str:
        response = await self.request('POST', f'/{tag}', data=data)
        data = await response.json(loads=utils.from_json)
        response.close()
        return data['id']


__all__ = (
    'AssetMetadata',
    'StatelessAsset',
    'Asset',
    'Tag',
    'Resource',
    '_cdn_session',
    'DEFAULT_USER_AGENT',
    '_get_session',
    'Content',
    'resolve_content',
    'Upload',
    'ResolvableResource',
    'resolve_resource',
    'CDNClient',
)
