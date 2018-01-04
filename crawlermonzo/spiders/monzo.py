from scrapy.spiders import Spider, Request
from scrapy import Selector
from scrapy import signals
from crawlermonzo.items import CrawlermonzoItem
import string
from sets import Set
import json

class MySpider(Spider):
    name = "monzo"
    allowed_domains = ["monzo.com"]
    sitemap = {}
    excludeAfterHome = Set([])

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        spider.logger.info('Spider closed: %s', spider.name)
        self.sitemapFile.write("]")

    def start_requests(self):
        self.starturl = self.getFullUrl(self.starturl)
        self.sitemapFile = open('sitemap.json', 'w')
        self.sitemapFile.write("[\n")
        urls = [ self.starturl ]
        for url in urls:
            yield Request(url=url, callback=self.parse)

    def getFullUrl(self, url):
        if (not url.endswith("/")):
            url = url + "/"
        if (url.startswith("/")):
            url = string.replace(url, "/", self.starturl, 1)
        return url

    def processHeadersAndFooters(self, response):
        for headerLink in response.xpath('//nav[@class="c-header__nav"]/a/@href'):
            self.excludeAfterHome.add(headerLink.extract())
        for footerLink in response.xpath('//div[@class="footer__nav-column footer__links-column"]/ul/li/a/@href'):
            self.excludeAfterHome.add(footerLink.extract())

    def parse(self, response):
        nextLinks = Set([])
        isHome = response.url == self.starturl
        if isHome:
            self.processHeadersAndFooters(response)
        for link in response.css('a::attr(href)'):
            url = str(link.extract())
            if '?' not in url and '#' not in url and (url.startswith("/") or url.startswith(self.starturl)):
                # print url
                if (isHome or url not in self.excludeAfterHome):
                    url = self.getFullUrl(url)
                    if (url != response.url):
                        nextLinks.add(url)
                        yield response.follow(url, self.parse)
        currentURL = {
            response.url: list(nextLinks)
        }
        self.sitemapFile.write(json.dumps(currentURL, separators=(',', ':')) + ",\n")