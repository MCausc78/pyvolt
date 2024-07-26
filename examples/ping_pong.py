import pyvolt

import pyvolt

# Whether the example should be ran as a user account or not
self_bot = False

client = pyvolt.Client(token='token', bot=not self_bot)


@client.on(pyvolt.ReadyEvent)
async def on_ready(_) -> None:
    print('Logged on as', client.me)


@client.on(pyvolt.MessageCreateEvent)
async def on_message(event: pyvolt.MessageCreateEvent):
    message = event.message

    # don't respond to ourselves/others
    if not client.me or (client.me != message.author_id) ^ self_bot:
        return

    if message.content == 'ping':
        await message.channel.send('pong')


client.run()
