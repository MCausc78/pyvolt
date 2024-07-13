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

async def bench_members():
    with open('./test/data/servers/member.json', 'r') as fp:
        payload = json.load(fp)

    with open('./test/data/servers/server.json', 'r') as fp:
        server_payload = json.load(fp)
    
    with open('./test/data/users/user.json', 'r') as fp:
        user_payload = json.load(fp)

    state = pyvolt.State()
    parser = pyvolt.Parser(state)
    state.setup(parser=parser)

    def using_pyvolt():
        return parser.parse_member(payload)

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
    rpy_state.add_user(user_payload)

    rpy_server = revolt.Server(data=server_payload, state=rpy_state)

    def using_revoltpy():
        return revolt.Member(data=payload, server=rpy_server, state=rpy_state)

    vpy_http = voltage.internals.http.HTTPHandler(session, '')
    vpy_cache = voltage.internals.cache.CacheHandler(vpy_http, asyncio.get_event_loop())
    vpy_cache.add_user(user_payload)

    vpy_server = voltage.Server(data=server_payload, cache=vpy_cache)

    def using_voltage():
        return voltage.Member(data=payload, server=vpy_server, cache=vpy_cache)

    time_pyvolt = timeit.timeit(using_pyvolt,     number=10000)
    time_revoltpy = timeit.timeit(using_revoltpy, number=10000)
    time_voltage = timeit.timeit(using_voltage,   number=10000)

    print(f"[Member] Time using pyvolt ----: {time_pyvolt:.6f} seconds")
    print(f"[Member] Time using revolt.py -: {time_revoltpy:.6f} seconds")
    print(f"[Member] Time using voltage ---: {time_voltage:.6f} seconds")

    await session.close()