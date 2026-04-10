from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from sns_core import SocialPost, PostAuthor


async def fetch_data(url: str) -> SocialPost:
    """
    使用 Playwright 非同步爬取 Weverse 貼文資料

    Args:
        url: Weverse 貼文網址

    Returns:
        SnsPost 物件,包含貼文資訊
    """
    async with async_playwright() as p:
        # 啟動瀏覽器
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        )

        # 創建上下文
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # 創建頁面
        page = await context.new_page()

        try:
            # 訪問頁面
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # 等待關鍵元素載入
            await page.wait_for_selector('.WeverseViewer', timeout=30000)

            # 獲取頁面 HTML
            html = await page.content()

        finally:
            # 確保瀏覽器關閉
            await browser.close()

    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html, "lxml")

    # 發文者頭像
    avatar_tag = soup.select_one(".avatar-decorator-_-avatar img")
    avatar_url = avatar_tag["src"] if avatar_tag else None

    # 發文者名稱
    name_tag = soup.select_one(".avatar-decorator-_-title_area .avatar-decorator-_-title")
    author_name = name_tag.get_text(strip=True) if name_tag else None

    # 發文內容：抓所有 p.p，保留 <br> 換行
    text_blocks = []
    for p in soup.select("p.p"):
        text_blocks.append(p.get_text("\n", strip=True))
    post_text = "\n\n".join(text_blocks)

    # 照原始順序抓取所有 WidgetMedia (照片和影片縮圖)
    image_urls = []
    media_divs = soup.select("div.WidgetMedia")
    for div in media_divs:
        img_tag = div.find("img")
        if img_tag and img_tag.get("src"):
            image_urls.append(img_tag["src"])

    # 去除網址 query 參數，保持乾淨
    image_urls = [urlparse(link)._replace(query="").geturl() for link in image_urls]

    return SocialPost(
        post_link=url,
        author=PostAuthor(name=author_name, url=avatar_url),
        text=post_text,
        images=image_urls
    )


# 測試用
if __name__ == "__main__":
    import asyncio

    # 測試網址
    test_url = "https://weverse.io/stayc/artist/2-169128050"


    async def main():
        print("🚀 開始爬取 Weverse 貼文")
        try:
            result = await fetch_data(test_url)
            print("\n✅ 成功爬取資料:")
            print(result)
        except Exception as e:
            print(f"\n❌ 爬取失敗: {e}")


    asyncio.run(main())
