import os
import re
import random

DATA_PATH = './data'
TRAIN_RATIO = 0.8

if __name__ == '__main__':
  datafiles = []
  rows = []
  for file in os.listdir(DATA_PATH):
    if file.endswith('.tsv'):
      f = open(f'{DATA_PATH}/{file}', 'r', encoding='utf-8')
      rows.extend(f.readlines())
      f.close()
  
  random.shuffle(rows)

  splitIndex = int(len(rows) * TRAIN_RATIO)

  f = open(f'{DATA_PATH}/train.tsv', 'w', encoding='utf-8')
  trainArticle = ['news\tsummary\tscore']
  trainArticle.extend(rows[:splitIndex])
  f.write(re.sub('\n+', '\n', '\n'.join(trainArticle)).strip())
  f.close()

  f = open(f'{DATA_PATH}/test.tsv', 'w', encoding='utf-8')
  testArticle = ['news\tsummary\tscore']
  testArticle.extend(rows[splitIndex:])
  f.write(re.sub('\n+', '\n', '\n'.join(testArticle)).strip())
  f.close()

  
  