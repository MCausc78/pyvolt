import asyncio

import json
import pyvolt

import revolt
import revolt.http
import revolt.state

import timeit
import typing
import voltage
import voltage.internals

async def bench_users():
    with open('./tests/data/users/user.json', 'r') as fp:
        payload = json.load(fp)

    state = pyvolt.State()
    parser = pyvolt.Parser(state=state)
    state.setup(parser=parser)

    def using_pyvolt():
        return parser.parse_user(payload)

    import aiohttp
    session = aiohttp.ClientSession()

    api_info: typing.Any = {
        'features': {
            'autumn': {
                'url': 'https://autumn.revolt.chat/'
            }
        }
    }
    rpy_http = revolt.http.HttpClient(
        session,
        '',
        'https://api.revolt.chat/',
        api_info
    )
    rpy_state = revolt.state.State(rpy_http, api_info, 1000)

    def using_revoltpy():
        return revolt.User(data=payload, state=rpy_state)

    vpy_http = voltage.internals.http.HTTPHandler(session, '')
    vpy_cache = voltage.internals.cache.CacheHandler(vpy_http, asyncio.get_event_loop())

    def using_voltage():
        return voltage.User(data=payload, cache=vpy_cache)

    time_pyvolt = timeit.timeit(using_pyvolt,     number=100_000)
    time_revoltpy = timeit.timeit(using_revoltpy, number=100_000)
    time_voltage = timeit.timeit(using_voltage,   number=100_000)

    print(f"[User] Time using pyvolt ----: {time_pyvolt:.6f} seconds")
    print(f"[User] Time using revolt.py -: {time_revoltpy:.6f} seconds")
    print(f"[User] Time using voltage ---: {time_voltage:.6f} seconds")

    await session.close()