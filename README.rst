pyvolt
======

A simple, flexible API wrapper for Revolt.

.. warning::
    This is alpha software. Please report bugs on GitHub issues if you will find any.

Key Features
-------------

- Built on ``asyncio``.
- Probably handles ratelimiting.
- Fast. Really faster than Revolt.py and voltage.
- Low memory usage.
- Customizable architecture. Build object parser in Rust to achieve high speeds.
- Focuses on supporting both, bot and user accounts.

Installing
----------

**Python 3.10 or higher is required**

To install the library, you can just run the following command:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U git+https://github.com/MCausc78/pyvolt@master

    # Windows
    py -3 -m pip install -U git+https://github.com/MCausc78/pyvolt@master

Quick Example
--------------

.. code:: py

    from pyvolt import Client

    class MyClient(Client):
        async def on_ready(self, _, /):
            print('Logged on as', self.me)

        async def on_message(self, message, /):
            # don't respond to ourselves
            if message.author_id == self.me.id:
                return

            if message.content == 'ping':
                await message.channel.send('pong')

    # You can pass ``bot=False`` to run as user account
    client = MyClient(token='token')
    client.run()

Links
------

- `Documentation <https://pyvolt.readthedocs.io/en/latest/index.html>`_
- `Official Revolt Server <https://rvlt.gg/ZZQb4sxx>`_
- `Revolt API <https://rvlt.gg/API>`

Why Not
-------

- `pyrevolt <https://github.com/GenericNerd/pyrevolt>`_ - Doesn't follow PEP8 and does a ton of requests on startup (not member list).
- `voltage <https://github.com/EnokiUN/voltage>`_ - Slow and simply copypasta from ``revolt.py``.
- `revolt.py <https://github.com/revoltchat/revolt.py>`_ - Slow and unable to disable member list loading.
- `luster <https://github.com/nerdguyahmad/luster>`_ - Unmaintained library.
