import pyvolt

client = pyvolt.Client(token='token', bot=False)


def sort_private_channel(channel: pyvolt.DMChannel | pyvolt.GroupChannel) -> str:
    return channel.last_message_id or '0'


@client.on(pyvolt.ReadyEvent)
async def on_ready(event: pyvolt.ReadyEvent):
    event.process()
    event.cancel()

    for channel in client.ordered_private_channels:
        if isinstance(channel, pyvolt.DMChannel):
            target_id = channel.recipient_id
            target = client.get_user(target_id) or await client.fetch_user(target_id)
            if channel.active:
                print('DM with', target.display_name or target.name)
            else:
                print('Inactive DM with', target.display_name or target.name)
        elif isinstance(channel, pyvolt.GroupChannel):
            print('Group', channel.name)


client.run()
