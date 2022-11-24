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

BROWSER = webdriver.Chrome(executable_path='chromedriver', options=browserOptions)
EXPLICIT_DELAY=0.2
RETRY = 20

def get_news(articleUrl):
  # Config
  rawdata = requests.get(articleUrl, headers={'User-Agent':'Mozilla/5.0'})
  soup = BeautifulSoup(rawdata.content, "html.parser")

  # Get article
  BROWSER.get(articleUrl)
  time.sleep(EXPLICIT_DELAY)

  # Dynamically waiting fetch
  for _ in range(RETRY):
    try:
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
      continue


def create_dataset(officeId, startDate, endDate, savePath):
  startDate = parseDate(startDate)
  endDate = parseDate(endDate)
  startDateString = startDate.strftime("%Y%m%d")
  endDateString = endDate.strftime("%Y%m%d")
  print(endDate)

  oneday = datetime.timedelta(days=1)

  # Get ranked articles
  print(COLTEX['YELLOW'] + f'[{officeId}] Get rankings...' + COLTEX['WHITE'])
  articleUrls = set()

  # Check cached url
  if not os.path.exists(f'{savePath}/rankurl-{officeId}-{startDateString}-{endDateString}.txt'):
    
    # Fetch ranked articles
    BROWSER.get(f'https://media.naver.com/press/{officeId}/ranking?type=comment&date={endDateString}')
    time.sleep(EXPLICIT_DELAY) 

    with tqdm(total= (endDate - startDate).days) as pbar:
      iterDate = endDate
      while startDate <= iterDate:
        for i in range(10):
          try:
            rankUrls = [li.find_element(By.TAG_NAME, 'a').get_attribute('href') for li in BROWSER.find_elements(By.CLASS_NAME, 'as_thumb')]
            articleUrls.update(rankUrls)
            break
          except:
            time.sleep(EXPLICIT_DELAY)
            
        iterDate = iterDate - oneday
        pbar.update(1)
        pbar.set_postfix({'searching date': iterDate, 'articles': len(articleUrls)})

        while True:
          try:
            BROWSER.find_element(By.CLASS_NAME, 'button_date_prev').click()
            time.sleep(EXPLICIT_DELAY)
            break
          except:
            continue
    
    # Cache rank urls
    with open(f'{savePath}/rankurl-{officeId}-{startDateString}-{endDateString}.txt', 'wb') as rf:
      rf.write('\n'.join(articleUrls).encode('utf-8'))
  
  else:
    with open(f'{savePath}/rankurl-{officeId}-{startDateString}-{endDateString}.txt', 'rb') as urlf:
      articleUrls.update(urlf.readlines())

  # Get articles
  print(COLTEX['YELLOW'] + f'[{officeId}] Get Articles...' + COLTEX['WHITE'])
  articles = []
  for articleUrl in tqdm(articleUrls):
    article = get_news(articleUrl)
    if article is not None:
      articles.append(article)
  
  # Save articles
  with open(f'{savePath}/rankurl-{officeId}-{startDateString}-{endDateString}.tsv', 'wb') as f:
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
  startDate = '20221120'
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



