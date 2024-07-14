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

async def bench_dm_channels():
    with open('./test/data/channels/dm.json', 'r') as fp:
        payload = json.load(fp)
    
    state = pyvolt.State()
    parser = pyvolt.Parser(state)
    state.setup(parser=parser)

    def using_pyvolt():
        return parser.parse_direct_message_channel(payload)

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
        return revolt.DMChannel(data=payload, state=rpy_state)

    vpy_http = voltage.internals.http.HTTPHandler(session, '')
    vpy_cache = voltage.internals.cache.CacheHandler(vpy_http, asyncio.get_event_loop())

    def using_voltage():
        return voltage.DMChannel(data=payload, cache=vpy_cache)

    time_pyvolt = timeit.timeit(using_pyvolt,     number=100_000)
    time_revoltpy = timeit.timeit(using_revoltpy, number=100_000)
    time_voltage = timeit.timeit(using_voltage,   number=100_000)

    print(f"[DMChannel] Time using pyvolt ----: {time_pyvolt:.6f} seconds")
    print(f"[DMChannel] Time using revolt.py -: {time_revoltpy:.6f} seconds")
    print(f"[DMChannel] Time using voltage ---: {time_voltage:.6f} seconds")

    await session.close()

async def bench_group_channels():
    with open('./test/data/channels/group.json', 'r') as fp:
        payload = json.load(fp)
    
    state = pyvolt.State()
    parser = pyvolt.Parser(state)
    state.setup(parser=parser)

    def using_pyvolt():
        return parser.parse_group_channel(payload, (True, payload['recipients']))

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
        return revolt.GroupDMChannel(data=payload, state=rpy_state)

    vpy_http = voltage.internals.http.HTTPHandler(session, '')
    vpy_cache = voltage.internals.cache.CacheHandler(vpy_http, asyncio.get_event_loop())
    
    with open('./test/data/users/me.json', 'r') as fp:
        me = json.load(fp)
        vpy_cache.add_user(me)

    with open('./test/data/users/mecha.json', 'r') as fp:
        me = json.load(fp)
        vpy_cache.add_user(me)


    def using_voltage():
        return voltage.GroupDMChannel(data=payload, cache=vpy_cache)

    time_pyvolt = timeit.timeit(using_pyvolt,     number=100_000)
    time_revoltpy = timeit.timeit(using_revoltpy, number=100_000)
    time_voltage = timeit.timeit(using_voltage,   number=100_000)

    print(f"[GroupChannel] Time using pyvolt ----: {time_pyvolt:.6f} seconds")
    print(f"[GroupChannel] Time using revolt.py -: {time_revoltpy:.6f} seconds")
    print(f"[GroupChannel] Time using voltage ---: {time_voltage:.6f} seconds")

    await session.close()

async def bench_text_channels():
    with open('./test/data/channels/rules_channel.json', 'r') as fp:
        payload = json.load(fp)
    
    with open('./test/data/servers/server.json', 'r') as fp:
        server_payload = json.load(fp)
    
    state = pyvolt.State()
    parser = pyvolt.Parser(state)
    state.setup(parser=parser)

    def using_pyvolt():
        return parser.parse_text_channel(payload)

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
        return revolt.TextChannel(data=payload, state=rpy_state)

    vpy_http = voltage.internals.http.HTTPHandler(session, '')
    vpy_cache = voltage.internals.cache.CacheHandler(vpy_http, asyncio.get_event_loop())
    server_id = payload['server']
    vpy_server = voltage.Server(data=server_payload, cache=vpy_cache)
    vpy_cache.servers[vpy_server.id] = vpy_server

    def using_voltage():
        return voltage.TextChannel(data=payload, cache=vpy_cache, server_id=server_id)

    time_pyvolt = timeit.timeit(using_pyvolt,     number=100_000)
    time_revoltpy = timeit.timeit(using_revoltpy, number=100_000)
    time_voltage = timeit.timeit(using_voltage,   number=100_000)

    print(f"[TextChannel] Time using pyvolt ----: {time_pyvolt:.6f} seconds")
    print(f"[TextChannel] Time using revolt.py -: {time_revoltpy:.6f} seconds")
    print(f"[TextChannel] Time using voltage ---: {time_voltage:.6f} seconds")

    await session.close()