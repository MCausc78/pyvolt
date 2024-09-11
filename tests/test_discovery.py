from aiohttp import ClientSession, web
import json
import pytest
import pyvolt

with open('./tests/data/discovery/bots.json', 'r') as fp:
    bots = json.load(fp)

with open('./tests/data/discovery/servers.json', 'r') as fp:
    servers = json.load(fp)

with open('./tests/data/discovery/themes.json', 'r') as fp:
    themes = json.load(fp)


def related_tags_for(entities: list) -> list[str]:
    related_tags = []
    for entity in entities:
        for tag in entity['tags']:
            if tag not in related_tags:
                related_tags.append(tag)
    return related_tags


routes = web.RouteTableDef()


@routes.get('/discover/bots.json')
async def discover_bots(_request: web.Request) -> web.Response:
    return web.json_response(
        {
            'pageProps': bots,
            '__N_SSP': True,
        }
    )


@routes.get('/discover/servers.json')
async def discover_servers(_request: web.Request) -> web.Response:
    return web.json_response(
        {
            'pageProps': servers,
            '__N_SSP': True,
        }
    )


@routes.get('/discover/themes.json')
async def discover_themes(_request: web.Request) -> web.Response:
    return web.json_response(
        {
            'pageProps': themes,
            '__N_SSP': True,
        }
    )


async def run_discovery_site(port: int) -> web.TCPSite:
    app = web.Application()
    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='localhost', port=port)

    await site.start()
    return site


@pytest.mark.asyncio
async def test_bots():
    site = await run_discovery_site(5101)

    state = pyvolt.State()
    state.setup(parser=pyvolt.Parser(state=state))
    client = pyvolt.DiscoveryClient(base='http://127.0.0.1:5101/', session=ClientSession(), state=state)

    page = await client.bots()
    assert len(page.bots) == 21
    assert page.popular_tags == [
        'nsfw',
        'utility',
        'moderation',
        'revolt',
        'bridge',
        'mod',
        'logging',
        'multipurpose',
        'anime',
        '18',
    ]

    bot = page.bots[0]
    assert bot.id == '01GA9PC742D72BM6CNDNXS3X7D'
    assert bot.name == 'Reddit'
    assert bot.profile.content
    assert not bot.profile.background
    assert bot.tags == []
    assert bot.server_count == 318
    assert bot.usage is pyvolt.BotUsage.high

    bot = page.bots[1]
    assert bot.id == '01FHGJ3NPP7XANQQH8C2BE44ZY'
    assert bot.name == 'AutoMod'
    avatar = bot.avatar
    assert avatar
    assert avatar.id == 'pYjK-QyMv92hy8GUM-b4IK1DMzYILys9s114khzzKY'
    assert avatar.filename == 'cut-automod-gay.png'
    metadata = avatar.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 512
    assert metadata.height == 512
    assert avatar.content_type == 'image/png'
    assert avatar.size == 29618

    background = bot.profile.background
    assert background
    assert background.id == 'AoRvVsvP1Y8X_A4cEqJ_R7B29wDZI5lNrbiu0A5pJI'
    assert background.filename == 'banner.png'
    metadata = background.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 1366
    assert metadata.height == 768
    assert background.content_type == 'image/png'
    assert background.size == 151802
    assert bot.tags == []
    assert bot.server_count == 3287
    assert bot.usage is pyvolt.BotUsage.high

    await site.stop()


@pytest.mark.asyncio
async def test_servers():
    site = await run_discovery_site(5102)

    state = pyvolt.State()
    state.setup(parser=pyvolt.Parser(state=state))
    client = pyvolt.DiscoveryClient(base='http://127.0.0.1:5102/', session=ClientSession(), state=state)

    page = await client.servers()

    assert page.popular_tags == [
        'gaming',
        'revolt',
        'programming',
        'fun',
        'chill',
        'art',
        'linux',
        'politics',
        'chat',
        'music',
    ]
    assert len(page.servers) == 105

    server = page.servers[0]
    assert server.id == '01HZJX93WB0W6QMFFC2E5VNG23'
    assert server.name == 'peeps'
    assert server.description == 'peeps is an active chatting server with memes and more'
    icon = server.icon
    assert icon
    assert icon.id == 'JTnWjuOrDZw6-A0ey94dvfVtDIvydD7bisr_aU82v_'
    assert icon.filename == 'GSKz91QUnRHWnO92E697pRpDl7BBkHnBCVvQVHTppK.jpeg'
    metadata = icon.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 768
    assert metadata.height == 768
    assert icon.content_type == 'image/jpeg'
    assert icon.size == 96701
    banner = server.banner
    assert banner
    assert banner.id == 'ZDeq632SkOHK26Arq7j4uX0V_bbyD10g8NWd8l1eH_'
    assert banner.filename == 'il_fullxfull.2923896440_644n.jpg'
    metadata = banner.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 2750
    assert metadata.height == 2125
    assert banner.content_type == 'image/jpeg'
    assert banner.size == 453049
    assert server.flags.value == 0
    assert server.tags == []
    assert server.member_count == 71
    assert server.activity is pyvolt.ServerActivity.high

    server = page.servers[1]
    assert server.id == '01F80118K1F2EYD9XAMCPQ0BCT'
    assert server.name == 'Catgirl Dungeon'
    # What is the hell, Catgirl Dungeon?????
    # assert server.description
    icon = server.icon
    assert icon
    assert icon.id == 'XIwQosw_3USL_XIvzZDyIKSi9LlMryrOPJNKsTrqts'
    assert icon.filename == 'gaysex.png'
    metadata = icon.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 500
    assert metadata.height == 500
    assert icon.content_type == 'image/png'
    assert icon.size == 17439
    banner = server.banner
    assert banner
    assert banner.id == 'ZTPUKiZ6OP1Yqox2PNOBVx_q1U3u9hXBbn84tLJXzK'
    assert banner.filename == '20230626_221308-2.jpg'
    metadata = banner.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 5120
    assert metadata.height == 2880
    assert banner.content_type == 'image/jpeg'
    assert banner.size == 1321952
    assert server.flags.value == 2
    assert server.tags == []
    assert server.member_count == 6804
    assert server.activity is pyvolt.ServerActivity.high

    server = page.servers[2]
    assert server.id == '01HVKQBBQ3DQVVNK3M8DHXV30D'
    assert server.name == 'Femboy Kingdom'
    assert (
        server.description
        == '! **18+ ONLY** !\n\na comfy server for femboys, but also home to girllikers, boykissers, silly gays of all kinds, and everyone else, too!!'
    )
    icon = server.icon
    assert icon
    assert icon.id == '1tTV6RqTik3qntjw2tFXg-HfCW_Dtmp4cYBA385BzO'
    assert icon.filename == 'femdom logo small.png'
    metadata = icon.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 2500
    assert metadata.height == 2500
    assert icon.content_type == 'image/png'
    assert icon.size == 2082228
    banner = server.banner
    assert banner
    assert banner.id == 'LoBAfzfxv-0bObWR4pYpByG2joAQ_o1LeqZByOrLSY'
    assert banner.filename == 'Hyrule_Castlesmallimagesize.png'
    metadata = banner.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 3840
    assert metadata.height == 2160
    assert banner.content_type == 'image/png'
    assert banner.size == 7096268
    assert server.flags.value == 0
    assert server.tags == []
    assert server.member_count == 225
    assert server.activity is pyvolt.ServerActivity.high

    server = page.servers[3]
    assert server.id == '01F7ZSBSFHQ8TA81725KQCSDDP'
    assert server.name == 'Revolt'
    assert (
        server.description
        == 'Official server run by the team behind Revolt.\nGeneral conversation and support server.\n \nAppeals and reports: lounge@revolt.chat'
    )
    icon = server.icon
    assert icon
    assert icon.id == 'gtc0gJE2S3RvuDhrl2-JeakvgbqEGr2acvBnRTTh6k'
    assert icon.filename == 'logo_round.png'
    metadata = icon.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 500
    assert metadata.height == 500
    assert icon.content_type == 'image/png'
    assert icon.size == 7558
    banner = server.banner
    assert banner
    assert banner.id == 'G_Q-6Y8KiGFVBNY2qVtDS25bX9Dh14CK2Py3TmLN_P'
    assert banner.filename == 'Lounge_Banner_Old.png'
    metadata = banner.metadata
    assert metadata.type is pyvolt.AssetMetadataType.image
    assert metadata.width == 1920
    assert metadata.height == 1080
    assert banner.content_type == 'image/png'
    assert banner.size == 138982
    assert server.flags.value == 1
    assert server.tags == ['revolt']
    assert server.member_count == 39737
    assert server.activity is pyvolt.ServerActivity.medium

    await site.stop()


@pytest.mark.asyncio
async def test_themes():
    site = await run_discovery_site(5103)

    state = pyvolt.State()
    state.setup(parser=pyvolt.Parser(state=state))
    client = pyvolt.DiscoveryClient(base='http://127.0.0.1:5103/', session=ClientSession(), state=state)

    page = await client.themes()
    assert page.popular_tags == [
        'dark',
        'light',
        'purple',
        'pastel',
        'soothing',
        'blue',
        'orange',
        'blur',
        'discord',
        'grey',
    ]
    assert len(page.themes) == 61

    theme = page.themes[0]

    assert theme.name == 'Amethyst'
    assert theme.version == '1.0.1'
    assert theme.slug == 'amethyst'
    assert theme.creator == 'Meow'
    assert theme.description == "Purple... based on spinfish's amethyst betterdiscord theme."
    assert theme.tags == ['dark', 'purple']
    assert theme.overrides == {
        'accent': '#ff9100',
        'background': '#230431',
        'foreground': '#ffffff',
        'block': '#1c0028',
        'mention': '#310c44',
        'message-box': '#2d0f3d',
        'success': '#4dd75e',
        'warning': '#FAA352',
        'error': '#ed3f43',
        'hover': 'rgba(0, 0, 0, 0.2)',
        'tooltip': '#000000',
        'scrollbar-thumb': '#361741',
        'scrollbar-track': 'transparent',
        'primary-background': '#230431',
        'primary-header': '#150020',
        'secondary-background': '#1c0028',
        'secondary-foreground': '#d2d2d2',
        'secondary-header': '#1c0028',
        'tertiary-background': '#8b8b8b',
        'tertiary-foreground': '#8b8b8b',
        'status-online': '#3ba55d',
        'status-away': '#faa81a',
        'status-busy': '#ed4245',
        'status-invisible': '#747f8d',
    }
    assert not theme.custom_css

    theme = page.themes[1]
    assert theme.name == 'AMOLED'
    assert theme.version == '0.0.1'
    assert theme.slug == 'amoled'
    assert theme.creator == 'insert'
    assert theme.description == 'Pure black, perfect for mobile.'
    assert theme.tags == ['oled', 'dark']
    assert theme.overrides == {
        'accent': '#FD6671',
        'background': '#000000',
        'foreground': '#FFFFFF',
        'block': '#1D1D1D',
        'message-box': '#000000',
        'mention': 'rgba(251, 255, 0, 0.06)',
        'success': '#65E572',
        'warning': '#FAA352',
        'error': '#F06464',
        'hover': 'rgba(0, 0, 0, 0.1)',
        'scrollbar-thumb': '#CA525A',
        'scrollbar-track': 'transparent',
        'primary-background': '#000000',
        'primary-header': '#000000',
        'secondary-background': '#000000',
        'secondary-foreground': '#DDDDDD',
        'secondary-header': '#1A1A1A',
        'tertiary-background': '#000000',
        'tertiary-foreground': '#AAAAAA',
        'status-online': '#3ABF7E',
        'status-away': '#F39F00',
        'status-busy': '#F84848',
        'status-streaming': '#977EFF',
        'status-invisible': '#A5A5A5',
    }
    assert not theme.custom_css

    await site.stop()
