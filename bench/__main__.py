import asyncio

from .bench_member import bench_members
from .bench_message import bench_messages
from .bench_server import bench_servers
from .bench_user import bench_users

async def main():
    print('Benchmarking Member parsing.')
    await bench_members()

    print('Benchmarking Message parsing.')
    await bench_messages()

    print('Benchmarking Server parsing.')
    await bench_servers()

    print('Benchmarking User parsing.')
    await bench_users()


asyncio.run(main())
