# Credit to sphinx.ext.extlinks for being a good starter
# Copyright 2007-2020 by the Sphinx team
# Licensed under BSD.

from __future__ import annotations

import typing

from docutils import nodes, utils
from docutils.nodes import Node, system_message
from docutils.parsers.rst.states import Inliner

import sphinx
from sphinx.application import Sphinx
from sphinx.util.nodes import split_explicit_title
from sphinx.util.typing import RoleFunction


if typing.TYPE_CHECKING:
    from collections.abc import Sequence

def make_link_role(resource_links: dict[str, str]) -> RoleFunction:
    def role(
        _name: str,
        _rawtext: str,
        text: str,
        _lineno: int,
        _inliner: Inliner,
        /,
        options: dict[str, typing.Any] | None = None,
        content: Sequence[str] = (),
    ) -> tuple[list[Node], list[system_message]]:
        _ = options
        _ = content

        text = utils.unescape(text)
        has_explicit_title, title, key = split_explicit_title(text)
        full_url = resource_links[key]
        if not has_explicit_title:
            title = full_url
        pnode = nodes.reference(title, title, internal=False, refuri=full_url)
        return [pnode], []
    
    return role


def add_link_role(app: Sphinx) -> None:
    app.add_role('resource', make_link_role(app.config.resource_links))

def setup(app: Sphinx) -> dict[str, typing.Any]:
    app.add_config_value('resource_links', {}, 'env')
    app.connect('builder-inited', add_link_role)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}