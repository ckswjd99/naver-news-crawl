import time
import re
import datetime
from dateutil.parser import parse as parseDate
from threading import Thread
import os
from tqdm import tqdm

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import targetOffices, COLTEX

browserOptions = webdriver.ChromeOptions()
browserOptions.add_argument("headless")
browserOptions.add_argument("log-level=3")

BROWSER = webdriver.Chrome(executable_path='chromedriver', options=browserOptions)


def get_news(articleUrl):
  try:
    # Config
    rawdata = requests.get(articleUrl, headers={'User-Agent':'Mozilla/5.0'})
    soup = BeautifulSoup(rawdata.content, "html.parser")

    # Get article
    BROWSER.get(articleUrl)
    time.sleep(1)

    
    # Check comment num
    comment = BROWSER.find_element(By.CLASS_NAME, 'u_cbox_list')
    commentNum = int(BROWSER.find_element(By.ID, 'comment_count').text.replace(',', ''))
    if commentNum < 10:
      return None

    # Check comment like
    bestCommentLike = int(comment.find_element(By.CLASS_NAME, 'u_cbox_cnt_recomm').text.replace(',', ''))
    if bestCommentLike < 100:
      return None
    

    # Get best comment
    bestComment = re.sub(' +', ' ', comment.find_element(By.CLASS_NAME, 'u_cbox_contents').text.replace('\n', ' '))

    # Get article
    article = re.sub(' +', ' ', soup.find(attrs={'id': 'dic_area'}).get_text(separator=' ').strip().replace('\n', ' '))

    # Remove tab from strings
    bestComment = re.sub('\t+', ' ', bestComment)
    article = re.sub('\t+', ' ', article)
    
    
    # Formatted
    return f'{article}\t{bestComment}\t{bestCommentLike}'
  except Exception as e:
    print('error!', e)
    return None


def get_ranking(officeId, date):
  # Get article
  BROWSER.get(f'https://media.naver.com/press/{officeId}/ranking?type=comment&date={date}')
  time.sleep(1)

  rankAnchors = BROWSER.find_element(By.CLASS_NAME, 'press_ranking_list').find_elements(By.TAG_NAME, 'a')
  return [ra.get_attribute('href') for ra in rankAnchors]


def create_dataset(officeId, startDate, endDate, savePath):
  startDate = parseDate(startDate)
  endDate = parseDate(endDate)

  oneday = datetime.timedelta(days=1)

  # Get ranked articles
  print(COLTEX['YELLOW'] + f'[{officeId}] Get rankings...' + COLTEX['WHITE'])
  articleUrls = set()
  
  with tqdm(total= (endDate - startDate).days) as pbar:
    iterDate = startDate
    while iterDate <= endDate:
      pbar.update(1)
      pbar.set_postfix({'searching date': iterDate})
      dateString = iterDate.strftime("%Y%m%%d")
      rankArticles = get_ranking(officeId, dateString)
      articleUrls.update(rankArticles)
      
      iterDate = iterDate + oneday

  # Get articles
  print(COLTEX['YELLOW'] + f'[{officeId}] Get Articles...' + COLTEX['WHITE'])
  articles = []
  for articleUrl in tqdm(articleUrls):
    article = get_news(articleUrl)
    if article is not None:
      articles.append(article)
  
  # Save articles
  with open(f'{savePath}/{officeId}.tsv', 'wb') as f:
    f.write('\n'.join(articles).encode('utf-8'))



# print(get_news('015', '0004778828'))
# articlesUrl = get_ranking('015', '20221123')
# print(articlesUrl)
# for articleUrl in articlesUrl:
#   print(get_news(articleUrl))
# dset = create_dataset('015', '20221121', '20221123')
# print(dset)

# with open('./015.tsv', 'wb') as f:
#   f.write('\n'.join(dset).encode('utf-8'))


if __name__ == '__main__':
  startDate = '20200101'
  endDate =   '20221124'
  savePath =  './data'

  # threads = [
  #   Thread(
  #     target=create_dataset, 
  #     args=(targetId, startDate, endDate, savePath)
  #   )
  #   for targetId in targetIds
  # ]

  # for t in threads: t.start()
  # for t in threads: t.join()

  if not os.path.exists(savePath):
    os.makedirs(savePath, exist_ok=False)

  for targetOffice in targetOffices:
    print(COLTEX['GREEN'] + f'Start crawling {targetOffice}', COLTEX['WHITE'])
    targetId = targetOffices[targetOffice]
    create_dataset(targetId, startDate, endDate, savePath)



