from django.shortcuts import render

# Create your views here.
from django.shortcuts import render,HttpResponse
from bs4 import BeautifulSoup
import requests
import requests
import time
import re
from bs4 import BeautifulSoup
import csv
import datetime

import numpy as np 

# def simple_crawl(request):
#      url = "https://www.maxlist.xyz/"
#      res = requests.get(url)
#      soup = BeautifulSoup(res.text,"html.parser")
#      title = soup.select('title')
#      return render(request,'home/simple_crawl.html',locals())

def simple_crawl(request):
	return render(request, 'simple_crawl.html')



def get_web_page(url):
    resp = requests.get(
        url=url,
        cookies={'over18': '1'}
    )
    if resp.status_code != 200:
        print('Invalid url:', resp.url)
        return None
    else:
        return resp.text


def get_articles(dom, date):
    soup = BeautifulSoup(dom, 'html5lib')

    # 取得上一頁的連結
    paging_div = soup.find('div', 'btn-group btn-group-paging')
    prev_url = paging_div.find_all('a')[1]['href']

    articles = []  # 儲存取得的文章資料
    authortotal=[]
    divs = soup.find_all('div', 'r-ent')
    for d in divs:
        if d.find('div', 'date').text.strip() == date:  # 發文日期正確
            # 取得推文數
            push_count = 0
            push_str = d.find('div', 'nrec').text
            if push_str:
                try:
                    push_count = int(push_str)  # 轉換字串為數字
                except ValueError:
                    # 若轉換失敗，可能是'爆'或 'X1', 'X2', ...
                    # 若不是, 不做任何事，push_count 保持為 0
                    if push_str == '爆':
                        push_count = 99
                    elif push_str.startswith('X'):
                        push_count = -10

            # 取得文章連結及標題
            if d.find('a'):  # 有超連結，表示文章存在，未被刪除
                href = d.find('a')['href']
                title = d.find('a').text
                author = d.find('div', 'author').text if d.find('div', 'author') else ''
                articles.append({
                    'title': title,
                    'href': href,
                    'push_count': push_count,
                    'author': author
                })
                authortotal.append(author)
    return articles, prev_url,authortotal


def get_ip(dom):
    # e.g., ※ 發信站: 批踢踢實業坊(ptt.cc), 來自: 27.52.6.175
    pattern = '來自: \d+\.\d+\.\d+\.\d+'
    match = re.search(pattern, dom)
    if match:
        return match.group(0).replace('來自: ', '')
    else:
        return None


def get_country(ip):
    if ip:
        url = 'http://api.ipstack.com/{}?access_key={}'.format(ip, API_KEY)
        data = requests.get(url).json()
        country_name = data['country_name'] if data['country_name'] else None
        return country_name
    return None






def POST_crawl(request):


	APIkey = request.POST.get('APIkey', None)
	PTT_URL = 'https://www.ptt.cc'
	API_KEY = APIkey
	def get_country(ip):
		if ip:
			url = 'http://api.ipstack.com/{}?access_key={}'.format(ip, API_KEY)
			data = requests.get(url).json()
			country_name = data['country_name'] if data['country_name'] else None
			return country_name
		return None

	data = request.POST.get('title', None)
	print(data)
	number=data
	print('取得今日文章列表...')
	current_page = get_web_page(PTT_URL + '/bbs/Gossiping/index.html')
	if current_page:
		articles = []  # 全部的今日文章
		author=[]
		countryT=[]
		title=[]
		iptotal=[]
		today = time.strftime('%m/%d').lstrip('0')
		current_articles, prev_url,authortotal = get_articles(current_page, today)  # 目前頁面的今日文章
		
		for i in range(int(number)):
			articles += current_articles
			current_page = get_web_page(PTT_URL + prev_url)
			current_articles, prev_url,authortotal = get_articles(current_page, today)
		print('共 %d 篇文章' % (len(articles)))

		# 已取得文章列表，開始進入各文章尋找發文者 IP
		print('取得前 100 篇文章 IP')
		country_to_count = dict()
		for article in articles[:len(articles)]:
			# print('查詢 IP:', article['title'])
			page = get_web_page(PTT_URL + article['href'])
			if page:
				ip = get_ip(page)
				country = get_country(ip)
				if country in country_to_count.keys():
					country_to_count[country] += 1
				else:
					country_to_count[country] = 1
			# print("來自",country, end='')
			# print("   ","作者是",article['author'])
			author.append(article['author'])
			title.append(article['title'])
			countryT.append(country)
			iptotal.append(ip)

			
		# 印出各國 IP 次數資訊
		print('各國 IP 分布')
		for k, v in country_to_count.items():
			print(k, v)
		countryT=np.array(countryT)
		countryT.reshape(countryT.shape[0],1)
		articlenumber=len(articles)

	with open('產生的文件檔案.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';') 
            writer.writerow(['文章標題', '作者', 'IP','國家'])
            for i in range(len(author)):
                writer.writerow([title[i],author[i],iptotal[i],countryT[i]])


	return render(request, 'simple_crawl_result.html',locals())



# def POST_crawl(request):
#     url = request.POST["title"]
#     print(url)
#     res = requests.get(url)
#     # print(res)
#     soup = BeautifulSoup(res.text, "html.parser")
#     post = []
#     H_tag = soup.find_all('h2')
#     for h in H_tag:
#         post.append(h.text)

#     return render(request, 'simple_crawl_result.html',locals())
