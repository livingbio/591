import requests
import logging
import re
from bs4 import BeautifulSoup
import csv
import time
import jinja2

re_num = re.compile(r"([\d]+)")
re_url = re.compile(r"rent\-detail\-([\d]+)")
re_links = re.compile(r'rent\-detail\-[\d]+\.html')

kind = (6, 12) # office, or mix

def parse(kind, offset=0):
    url = "http://rent.591.com.tw/index.php?module=search&action=rslist&is_new_list=1&type=1&searchtype=1&region=1&orderType=desc&listview=img&kind=%s&firstRow=%s"
    url = url % (kind, offset*20)

    content = requests.get(url).json()

    # main is for list, recom is recommandation
    soup = BeautifulSoup(content['main'])
    for index, div in enumerate(soup.find_all("div", class_="shList")):
        a = div.find('a', class_='imgbd')
        title = a['title']
        link = a['href']
        address = div.find('div', class_='right')
        address = "\n".join(k.text for k in address.findChildren()).strip()

        size = div.find('li', class_='area').text.strip()
        price = div.find('li', class_='price').text.strip()

        img = div.find('img')['src']
        yield {
            'title': title.encode('utf8'),
            'link': link.encode('utf8'),
            'address': address.encode('utf8'),
            'size': size.encode('utf8'),
            'price': price.encode('utf8'),
            'img': img.encode('utf8')
        }

    time.sleep(5)
    if index == 19:
        for i in parse(kind, offset+1):
            yield i

def render(filename):
    with open(filename) as ifile:
        reader = csv.DictReader(ifile)

        template = jinja2.Template('591.html')
        template.render({'rows': reader})

def main():
    with open('results.csv', 'w') as ofile:
        writer = csv.DictWriter(ofile, ('title', 'link', 'address', 'size', 'price', 'img'))
        for i in parse(6):
            writer.writerow(i)
        for i in parse(12):
            writer.writerow(i)

if __name__ == '__main__':
    import clime; clime.start(debug=True)
