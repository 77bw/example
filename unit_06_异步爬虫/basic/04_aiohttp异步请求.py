import asyncio
import aiohttp


async def fetch(session,url):
    async with session.get(url) as response:
         return await response.text(),response.status


async def main():
    async with aiohttp.ClientSession() as session:
        html,status = await fetch(session,'https://www.baidu.com/')
        print(f'html: {html[:100]}...')
        print(f'status: {status}')

if __name__ == '__main__':
    asyncio.run(main())