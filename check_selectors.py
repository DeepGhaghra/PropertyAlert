from bs4 import BeautifulSoup
import re

html = open('99acres_stealth_test.html', 'r', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

cards1 = soup.select('div[class*="tupleNew__tupleContainer"]')
cards2 = soup.select('div.tuple')
cards3 = soup.select('div[class*="srpTuple__tupleTable"]')
cards4 = soup.select('div[class*="projectTuple__"]')
cards5 = soup.find_all('div', attrs={'data-label': 'SEARCH'})

print("cards1 (tupleNew__tupleContainer):", len(cards1))
print("cards2 (div.tuple):", len(cards2))
print("cards3 (srpTuple__tupleTable):", len(cards3))
print("cards4 (projectTuple__):", len(cards4))
print("cards5 (data-label SEARCH):", len(cards5))

if len(cards3) > 0:
    print("Example card 3 title:", cards3[0].select_one('a.srpTuple__propertyName').text if cards3[0].select_one('a.srpTuple__propertyName') else 'no title')
if len(cards4) > 0:
    print("Example card 4 title:", cards4[0].select_one('a.projectTuple__projectName').text if cards4[0].select_one('a.projectTuple__projectName') else 'no title')
if len(cards5) > 0:
    print("Example card 5 class:", cards5[0].get('class'))
    print("Example card 5 title:", cards5[0].find('a').text if cards5[0].find('a') else 'no a tag')

