"""
    aiohttp异步爬取实战：
        实现思路：
            1.异步爬取所有的列表页，将所以的列表页的爬取任务集合到一起，将其声明为task组成的列表，并进行异步爬取
            2.将列表页的所有内容解析拼接url组合成详情页的爬取任务集合，并声明为task组成的列表，并进行异步爬取，同时将结果进行以异步的方式存储到mingdb上
        两个阶段之间的过程是串行同步的方式执行。

        实现步骤：
            1.基本配置参数
                index_url，detail_url,concurrency并发量，page_size,page_number,日志参数等
            2.爬取列表页
                构建一个通用的采集方法
                列表页的方法
            3.爬取详情页
"""

import asyncio
import json
import aiohttp
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')
#列表页url
INDEX_URL = 'https://spa5.scrape.center/api/book/?limit=18&offset={offset}'
#详情页url
DETAIL_URL = 'https://spa5.scrape.center/api/book/{id}'
#每一页的详情页数量
PAGE_SIZE = 18
#列表页的页码数量
PAGR_NUMBER = 1
#并发数量
CONCURRENCY = 10

#定义通用爬取方法
semaphore = asyncio.Semaphore(CONCURRENCY)
session = None
async def scrape_api(url):
    async with  semaphore:  #引入信号量
        try:
            logging.info('scraping %s', url)
            async with session.get(url) as response:
                return await response.json()
        except aiohttp.ClientError:
            logging.error('error occurred while scraping %s',url,exc_info=True)

#爬取列表页
async def scrape_index(page):
    url = INDEX_URL.format(offset=PAGE_SIZE * (page - 1))
    return await scrape_api(url)

#定义异步保存mongdb的方法
MONGO_CONNECTION_STRING = 'mongodb://localhost:27017'
MONGO_DB_NAME = 'books'
MONGO_COLLECTION_NAME = 'books'
client = AsyncIOMotorClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DB_NAME]
collection = db[MONGO_COLLECTION_NAME]

async def save_data(data):
    logging.info('saving data %s', data)
    if data:
        return await collection.update_one({
            'id': data['id']
        }, {
            '$set': data
        }, upsert=True)

#爬取详情页的方法
async def scrape_detail(id):
    url = DETAIL_URL.format(id=id)
    data = await scrape_api(url)
    await save_data(data)

#主入口
async def main():
    #先定义一些基本配置参数
    #定义异步爬取方法赋值给全局变量 session ,这样的话就不需要在各个方法中进行参数的传递
    global session
    session = aiohttp.ClientSession()
    #定义爬取列表页的方法
    #定义scrape_index_tasks用于爬取列表页的所有任务
    scrape_index_tasks = [asyncio.ensure_future(scrape_index(page)) for page in range(1,PAGR_NUMBER+1) ]
    #使用gather方法获取 scrape_index_tasks 的返回结果并有序的保存在列表中
    results = await asyncio.gather(*scrape_index_tasks)
    logging.info('results %s',json.dumps(results,ensure_ascii=False,indent=2))
    #解析results列表中的列表页，获取id，并将其保存在列表中
    ids = []
    for index_data in results:
        if not index_data : continue
        for item in index_data['results']:
            ids.append(item['id'])
    #定义爬取详情页的方法和保存数据到mongdb的方法，其中爬取详情页中会调用保存数据的方法
    #定义 scrape_detail_tasks 用于爬取所有详情页的任务
    scrape_detail_tasks = [asyncio.ensure_future(scrape_detail(id)) for id in ids]
    #使用gather 方法获取scrape_detail_tasks 的返回结果并有序的保存在列表中，由于这里无需有序的列表进行提取，所以使用asyncio 的await方法，效果是一样的，只不过顺序有所差异
    await asyncio.wait(scrape_detail_tasks)
    #在关闭session爬取异步的方法
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())