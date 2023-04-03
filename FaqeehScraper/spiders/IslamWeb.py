import scrapy
import re

class IslamWeb(scrapy.Spider):

    def __init__(self):
        super(IslamWeb, self)
        self.domain_url = "https://www.islamweb.net"

    name = 'islamweb'

    start_urls = [
        "https://www.islamweb.net/ar/fatwa/"
    ]

    def appendDomain(self, urls):
        return list(map(lambda url: self.domain_url.strip("/") + url, urls))

    def parseTree(self, response):
        nodes_with_scripts = response.css(".tree a::attr(onclick)").extract()
        nodes_with_urls = response.css(".tree a::attr(href)").extract
        urls = []

        for node in nodes_with_scripts:
            url_list = re.findall(r"/ar/fatawa/\d+/.+,", node)
            if len(url_list) > 0:
                url = url_list[0]
                url = url.replace("',", '')
                url = self.domain_url.strip("/") + url
                urls.append(url)
        
        nodes_with_urls = self.appendDomain(nodes_with_urls)

        urls.extend(nodes_with_urls)
        # Scrape subnodes

    def parser(self, response):
        fatwaSectionsURLs = response.css(".fatCatleft ul li a::attr(href)").extract()
        fatwaSectionsURLs = self.appendDomain(fatwaSectionsURLs)

