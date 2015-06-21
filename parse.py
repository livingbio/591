# -*- coding: utf-8 -*-

import requests
import logging
import re
from bs4 import BeautifulSoup
import csv
import time
import jinja2
import sqlite3
from math import *
from geopy import geocoders
g = geocoders.GoogleV3()

re_num = re.compile(r"([\d]+)")
re_url = re.compile(r"rent\-detail\-([\d]+)")
re_links = re.compile(r'rent\-detail\-[\d]+\.html')

kind = (6, 12) # office, or mix

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def address_filter(address):
    patterns = address.split('\n')
    results = []
    for p in patterns[3:]:
        if u'黃金曝光' in p: continue
        if len(results) < 3 and p.strip():
            results.append(p)

    return results

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

        address, _type, contact = address_filter(address)

        try:
            place, (lat, lng) = g.geocode(address)
        except:
            place, lat, lng = "", 0, 0

        yield {
            'title': title.encode('utf8'),
            'link': link.encode('utf8'),
            'address': address.encode('utf8'),
            'type': _type.encode('utf8'),
            'contact': contact.encode('utf8'),
            'place': place.encode('utf8'),
            'lat': lat,
            'lng': lng,
            'size': size.encode('utf8'),
            'price': price.encode('utf8'),
            'img': img.encode('utf8')
        }

    time.sleep(5)
    if index == 19:
        for i in parse(kind, offset+1):
            yield i


def img(imgurl):
    return imgurl.split("_")[0] + "_600x600.jpg"

def render(filename):
    with open(filename,'r') as ifile, open('results.html', 'w') as ofile:
        reader = csv.DictReader(ifile)

        rows = list(reader)
        rows = [{
            k:v.decode('utf8') for k, v in row.items()
        } for row in rows]

        new_rows = []
        for row in rows:
            size = float(row['size'].replace(u'坪',''))
            price = int(row['price'].replace(u'元', '').replace(',',''))

            print len(row['address'].split('\n'))
            # if not 20 < size < 100: continue
            # if price > 40000: continue
            # if not any(k in row['address'] for k in (u'松山', u'信義', u'大安', u'中正', u'中山')): continue

            # if not u'捷運' in row['title'] or not u'捷運' in row['address']: continue
            # if not u'南京復興' in row['title'] or not u'南京復興' in row['address']: continue

            row['size'] = size
            row['address'] = '<br/>'.join(address_filter(row['address']))
            row['price'] = price
            new_rows.append(row)

        new_rows.sort(key=lambda i: i['price'] / i['size'])

        template = jinja2.Template(open('591.html').read())
        ofile.write(template.render({
            'img': img,
            'rows': new_rows
        }).encode('utf8'))

def main():
    with open('results.csv', 'w') as ofile:
        writer = csv.DictWriter(ofile, (
            'title',
            'link',
            'type',
            'contact',
            'place',
            'lat',
            'lng',
            'address',
            'size',
            'price',
            'img')
        )
        writer.writeheader()
        for i in parse(6):
            writer.writerow(i)
        for i in parse(12):
            writer.writerow(i)

if __name__ == '__main__':
    import clime; clime.start(debug=True)
