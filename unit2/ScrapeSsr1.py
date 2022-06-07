import requests
import re
from urllib.parse import urljoin
import logging
import json
from os import makedirs
from os.path import exists


#定义日志级别的输出格式
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s:%(message)s' )
#当前站点的根url
BASE_URL  = 'https://ssr1.scrape.center'
#需要爬取的总页数
TOTAL_PAGE = 10
#定义保存数据的文件夹
RESULTS_DIR  = 'results'
#判断这个文件夹是否存在，如果不存在则重新创建一个
exists(RESULTS_DIR) or makedirs(RESULTS_DIR)   #判读文件是否存在，不存在重新创建一个

#保存数据为json格式
def save_data(data):
    name = data.get('name')
    data_path = f'{RESULTS_DIR}/{name}.json'
    #dump将数据保存成文本格式，ensure_ascii=False 保证中文字符再文件中能以正常的中文文本呈现，而不是unicode字符；indent设置了json数据再文本中显示的格式
    json.dump(data,open(data_path,'w',encoding = 'utf-8'),ensure_ascii=False,indent=2)

#爬取页面（考虑到不仅要爬取列表页，还要爬取详情页，这样字定义一个方法使其他可以调用，做到了代码的复用性）
def scrape_page(url):
    """
    :param url:
    :return: 页面的html代码
    """
    logging.info('scraping %s...',url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        logging.error('get invalid status code %s while scraping %s',response.status_code,url)
    except requests.RequestException:
        logging.error('error occurred while scraping %s',url,exc_info=True)

#爬取列表页
def scrape_index(page):
    """
    :param page: 接收列表页的页码
    :return: 列表页的html代码
    """
    index_url = f'{BASE_URL}/page/{page}'
    return scrape_page(index_url)

#解析列表页
def parse_index(html):
    """
    :param html: 列表页的html
    :return: 每部电影的详情页url
    """
    pattern = re.compile('<a.*?href="(.*?)".*?class="name">')
    items = re.findall(pattern,html)
    if not items:
        return []
    for item in items:
        detail_url = urljoin(BASE_URL,item)
        logging.info('get detail url %s',detail_url)
        yield detail_url

#爬取详情页
"""这个scrape_detail方法里面只调用scrape_page方法，而没有别的功能，那么爬取详情页直接用scrape_page方法不就好了，还有必要再单独定义scrape_detail
方法吗？有必要，单独定义一个scrape_detail方法再逻辑上会显得更清晰，而且以后如果想对scrape_detail方法进行改动(例如添加日志输出，增加预处理)，都可以再
scrape_detail里面实现的，而不用改动scrape_page方法，灵活性更好。
"""
def scrape_detail(url):
    """
    :param url:
    :return:返回详情页的源代码
    """
    return scrape_page(url)

#详情页的解析
def parse_detail(html):
    """
    parse detail page
    :param html: html of detail page
    :return: data
    """

    cover_pattern = re.compile(
        'class="item.*?<img.*?src="(.*?)".*?class="cover">', re.S)
    name_pattern = re.compile('<h2.*?>(.*?)</h2>')
    categories_pattern = re.compile(
        '<button.*?category.*?<span>(.*?)</span>.*?</button>', re.S)
    published_at_pattern = re.compile('(\d{4}-\d{2}-\d{2})\s?上映')
    drama_pattern = re.compile('<div.*?drama.*?>.*?<p.*?>(.*?)</p>', re.S)
    score_pattern = re.compile('<p.*?score.*?>(.*?)</p>', re.S)

    cover = re.search(cover_pattern, html).group(
        1).strip() if re.search(cover_pattern, html) else None
    name = re.search(name_pattern, html).group(
        1).strip() if re.search(name_pattern, html) else None
    categories = re.findall(categories_pattern, html) if re.findall(
        categories_pattern, html) else []
    published_at = re.search(published_at_pattern, html).group(
        1) if re.search(published_at_pattern, html) else None
    drama = re.search(drama_pattern, html).group(
        1).strip() if re.search(drama_pattern, html) else None
    score = float(re.search(score_pattern, html).group(1).strip()
                  ) if re.search(score_pattern, html) else None

    return {
        'cover': cover,
        'name': name,
        'categories': categories,
        'published_at': published_at,
        'drama': drama,
        'score': score
    }




def main():
    #先遍历所有的页码
    for page in range(1,TOTAL_PAGE + 1):
        #获取列表页的html
        index_html = scrape_index(page)
        #解析列表页并获取所有详情电影的url
        detail_urls = parse_index(index_html)  #得到一个生成器，方便输出
        # logging.info('detail urls %s',list(detail_urls))
        #遍历生成器获取每个详情页的url
        for detail_url in detail_urls:
            #获取详情页的html
            detail_html = scrape_detail(detail_url)
            #获取到电影爬取的内容
            data = parse_detail(detail_html)
            logging.info('get detail data %s',data)
            logging.info('saving data to json file')
            save_data(data)
            logging.info('data saved successfully')


if __name__ == '__main__':
    main()



