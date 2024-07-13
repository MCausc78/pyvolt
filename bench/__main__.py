import asyncio
from .bench_user import bench_users

async def main():
    print('Benchmarking User objects.')
    await bench_users()

asyncio.run(main())
