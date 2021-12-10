from threading import Thread
from bs4 import BeautifulSoup
import re
import requests
import time
import logging


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


f = open('log.log', 'w')
f.close()
logger = logging.getLogger('digi')
logger.setLevel(logging.INFO)

f_handler = logging.FileHandler('log.log', encoding='utf-8')

f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

f_handler.setFormatter(f_format)

logger.addHandler(f_handler)

logger.warning('STARTING NEW SESSION')

PRODUCT_URLS = []
FAILED_URLS = []

SEEN_PRODS = []
with open('SEEN-PRODUCTS.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for line in lines:
        SEEN_PRODS.append(line.strip())


def get_images(prod_url, prod_name, pageno):
    try:
        prod_req = requests.get(
            prod_url
        )
        if prod_req.status_code != 200:
            logger.warning(
                f'PRODUCT FAILURE: page number {pageno}, product {prod_name[:20]}, status_code = {prod_req.status_code}')
            raise Exception
        DOM_elements = BeautifulSoup(prod_req.content, 'html.parser')
        image_tags = DOM_elements.select(
            f'#content > div.o-page.js-product-page.c-product-page > div > article > section.c-product__gallery > div.c-gallery > ul > li > div > img')
        count_image = 1
        for image_tag in image_tags:
            b = re.search('data-src=".+"', str(image_tag))
            b = b.group(0)
            b = b.split("\"")
            image_url = b[1].split('?')[0]
            image_req = requests.get(image_url, timeout=5)
            if image_req.status_code != 200:
                logger.warning(
                    f'IMAGE FAILURE: page number {pageno}, product {prod_name[:20]}, image no {count_image} status_code = {prod_req.status_code}')
                raise Exception
            with open(f'pics/{pageno}/page-{pageno}-{prod_name}-{count_image}.jpg', 'wb') as f:
                f.write(image_req.content)
            count_image += 1
        with open('SEEN-PRODUCTS.txt', 'a+', encoding='utf-8') as f:
            f.write(prod_url + '\n')
        logger.info(f'SUCCESS for product {prod_name[:20]}')
        return
    except Exception as e:
        print(e)
        logger.error(f'Failed for product \n {prod_url}')
        with open('FAILED_URLS.txt', 'a+', encoding='utf-8') as f:
            f.write(prod_url + '\n')


page_list = list(range(23, 48))
products_pages = {}
for i in range(1, 48):
    products_pages[i] = []
for pageno in page_list:
    try:
        s = time.time()
        payload = {
            'pageno': pageno,
            'sortby': 4
        }
        res = requests.get(
            f'https://www.digikala.com/ajax/treasure-hunt/products/?pageno={pageno}&sortby=4',
            params=payload
        )
        json_res = res.json()

        products = json_res['data']['click_impression']
        for prod in products:
            prod_name = prod['name']
            prod_url = prod['product_url']
            if prod_url in SEEN_PRODS:
                continue
            PRODUCT_URLS.append(prod_url)
            prod_thread = Thread(target=get_images, args=(prod_url, prod_name, pageno))
            products_pages[pageno].append(prod_thread)
        e = time.time()
        print(f'finished threading for page NO {pageno}')
        logger.info(f'finished threading for page No {pageno}')
        print(e - s)
    except Exception as e:
        print("Over all failure for page " + str(e))
        logger.error(f'over all failure for page: {pageno}')
# with open('SEEN-PRODUCTS.txt', 'a+', encoding='utf-8') as f:
#     for item in PRODUCT_URLS:
#         f.write(item + '\n')
for page, product_list in reversed(products_pages.items()):
    s = time.time()
    groups = chunks(product_list, 10)
    for group in groups:
        for product_thread in group:
            product_thread.start()
        for product_thread in group:
            product_thread.join()
    # for product_thread in product_list:
    # product_thread.join()
    e = time.time()
    elapsed = e - s
    print(f'Finished for page NO {page}')
    logger.info(f'Finished for page NO {page}')
    logger.info(f'elapsed time for page {e - s}')
