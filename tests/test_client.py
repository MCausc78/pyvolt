from __future__ import annotations

from attrs import define, field
import asyncio
import pytest
import pyvolt


@define(slots=True)
class AddEvent(pyvolt.BaseEvent):
    a: int = field(repr=True, kw_only=True)
    b: int = field(repr=True, kw_only=True)


@define(slots=True)
class SubtractEvent(pyvolt.BaseEvent):
    a: int = field(repr=True, kw_only=True)
    b: int = field(repr=True, kw_only=True)


@pytest.mark.asyncio
async def test_events():
    queue: asyncio.Queue[int] = asyncio.Queue()

    client = pyvolt.Client()

    async def on_add(event: AddEvent, /) -> None:
        await queue.put(event.a + event.b)

    async def on_subtract(event: SubtractEvent, /) -> None:
        await queue.put(event.a - event.b)

    client.subscribe(AddEvent, on_add)
    client.subscribe(SubtractEvent, on_subtract)

    await client.dispatch(AddEvent(a=1, b=2))
    await client.dispatch(SubtractEvent(a=13, b=7))

    response = await asyncio.wait_for(queue.get(), timeout=1)
    assert response == 3

    response = await asyncio.wait_for(queue.get(), timeout=1)
    assert response == 6

    subscription = client.wait_for(AddEvent, check=lambda event, /: event.a == 0xDEAD, count=1, timeout=3)
    await client.dispatch(AddEvent(a=0xDEAD, b=11))

    number = await subscription
    assert number.a + number.b == 57016

    subscription = client.wait_for(AddEvent, check=lambda event, /: event.a == 0xBEEF, count=3, timeout=3)

    await client.dispatch(AddEvent(a=0xBEEF, b=11))
    await client.dispatch(AddEvent(a=0xBEEF, b=12))
    await client.dispatch(AddEvent(a=0xBEEF, b=13))

    numbers = [event.b async for event in subscription]

    assert sum(numbers) == 36
