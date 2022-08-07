import asyncio
import json
import time

import aiohttp
import logging

from aiohttp import ContentTypeError
from motor.motor_asyncio import AsyncIOMotorClient

# 先定义一些基本配置参数
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')
#列表页url
INDEX_URL = 'https://spa5.scrape.center/api/book/?limit=18&offset={offset}'
#详情页url
DETAIL_URL = 'https://spa5.scrape.center/api/book/{id}'
#每一页的详情页数量
PAGE_SIZE = 18
#列表页的页码数量
PAGE_NUMBER = 1
#并发数量
CONCURRENCY = 5

#异步mongdb连接
MONGO_CONNECTION_STRING = 'mongodb://localhost:27017'
MONGO_DB_NAME = 'books'
MONGO_COLLECTION_NAME = 'books'

client = AsyncIOMotorClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DB_NAME]
collection = db[MONGO_CONNECTION_STRING]

#创建事件循环
loop = asyncio.get_event_loop()


class Spider(object):

    def __init__(self):
        self.semaphore = asyncio.Semaphore(CONCURRENCY)

    # 定义通用爬取方法
    async def scrape_api(self, url):
        async with self.semaphore:  #引入信号量
            try:
                logging.info('scraping %s', url)
                async with self.session.get(url) as response:
                    await asyncio.sleep(1)
                    return await response.json()
            except ContentTypeError as e:
                logging.error('error occurred while scraping %s', url, exc_info=True)

    async def scrape_index(self, page):
        url = INDEX_URL.format(offset=PAGE_SIZE * (page - 1))
        return await self.scrape_api(url)

    # 爬取详情页的方法
    async def scrape_detail(self, id):
        url = DETAIL_URL.format(id=id)
        data = await self.scrape_api(url)
        await self.save_data(data)

    #保存数据的方法
    async def save_data(self, data):
        logging.info('saving data %s', data)
        if data:
            return await collection.update_one({
                'id': data.get('id')
            }, {
                '$set': data
            }, upsert=True)

    # 主入口
    async def main(self):
        # 定义异步爬取方法session
        self.session = aiohttp.ClientSession()
        # 定义爬取列表页的方法
        #定义scrape_index_tasks用于爬取列表页的所有任务
        scrape_index_tasks = [asyncio.ensure_future(self.scrape_index(page)) for page in range(1, PAGE_NUMBER + 1)]
        # 使用gather方法获取 scrape_index_tasks 的返回结果并有序的保存在列表中
        results = await asyncio.gather(*scrape_index_tasks)
        # detail tasks
        print('results', results)
        # 解析results列表中的列表页，获取id，并将其保存在列表中
        ids = []
        for index_data in results:
            if not index_data: continue
            for item in index_data.get('results'):
                ids.append(item.get('id'))
        # 定义爬取详情页的方法和保存数据到mongdb的方法，其中爬取详情页中会调用保存数据的方法
        # 定义 scrape_detail_tasks 用于爬取所有详情页的任务
        scrape_detail_tasks = [asyncio.ensure_future(self.scrape_detail(id)) for id in ids]
        # 使用gather 方法获取scrape_detail_tasks 的返回结果并有序的保存在列表中，由于这里无需有序的列表进行提取，所以使用asyncio 的await方法，效果是一样的，只不过顺序有所差异
        await asyncio.wait(scrape_detail_tasks)
        # 在关闭session爬取异步的方法
        await self.session.close()


if __name__ == '__main__':
    spider = Spider()
    loop.run_until_complete(spider.main())
