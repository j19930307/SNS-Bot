from selenium import webdriver

options = webdriver.ChromeOptions()

options.add_argument("--headless")

driver = webdriver.Chrome('chromedriver', options=options)

driver.get('https://twitter.com/home')

cookies=[] #你的cookies
for cookie in cookies:
    driver.add_cookie(cookie)

url = f"https://twitter.com/search?q=hello&src=typed_query"
driver.get(url)

from bs4 import BeautifulSoup
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

tweets = soup.find_all("div", {'data-testid': "cellInnerDiv"})

for tweet in tweets:
 	content = tweet.find('div', {'data-testid': "tweetText"}).text
 	print(content)
