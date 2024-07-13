import asyncio

from .bench_member import bench_members
from .bench_server import bench_servers
from .bench_user import bench_users

async def main():
    print('Benchmarking Member parsing.')
    await bench_members()

    print('Benchmarking Server parsing.')
    await bench_servers()

    print('Benchmarking User parsing.')
    await bench_users()


asyncio.run(main())
