import  asyncio
import time
import aiohttp

satrt = time.time()

async def get(url):
    session = aiohttp.ClientSession()
    response = await  session.get(url)
    await response.text()
    await session.close()
    return response

async def request():
    url = 'https://www.baidu.com/'
    print('Waiting for', url)
    response = await get(url)
    print('Get response from', url, 'response')


tasks = [asyncio.ensure_future(request()) for _ in range(10)]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))

end = time.time()
print('Cost time',end-satrt)