import scrapy
import re
import time
class IslamWeb(scrapy.Spider):

    def __init__(self):
        super(IslamWeb, self)
        self.domain_url = "https://www.islamweb.net"
        self.fatwa_counter = 0
        self.page_counter = 0
        self.counter_test = 0

    name = 'islamweb'

    start_urls = [
        "https://www.islamweb.net/ar/fatwa/",
        # "https://www.islamweb.net/ar/fatwa/65492/%D9%85%D9%86-%D8%A3%D8%AC%D9%85%D8%B9-%D8%A7%D9%84%D9%83%D8%AA%D8%A8-%D8%A7%D9%84%D9%85%D8%B9%D8%A7%D8%B5%D8%B1%D8%A9-%D9%81%D9%8A-%D8%A3%D8%B5%D9%88%D9%84-%D8%A7%D9%84%D8%A8%D8%AF%D8%B9-%D9%88%D9%81%D8%B1%D9%88%D8%B9%D9%87%D8%A7%D8%A7%D9%84%D8%A5%D8%A8%D8%AF%D8%A7%D8%B9-%D9%81%D9%8A-%D9%85%D8%B6%D8%A7%D8%B1-%D8%A7%D9%84%D8%A7%D8%A8%D8%AA%D8%AF%D8%A7%D8%B9",
        # "https://www.islamweb.net/ar/fatwa/300193/%D8%AD%D9%83%D9%85-%D8%AD%D9%84%D9%82-%D8%B4%D8%B9%D8%B1-%D8%A7%D9%84%D8%B9%D8%A7%D9%86%D8%A9-%D9%88%D8%A7%D9%84%D8%A5%D8%A8%D8%B7-%D9%88%D8%AD%D9%83%D9%85-%D8%A7%D9%84%D8%BA%D8%B3%D9%84-%D8%AF%D9%88%D9%86-%D8%AD%D9%84%D9%82%D9%87%D9%85%D8%A7",
        # "https://www.islamweb.net/ar/fatawa/1218/%D8%B3%D9%86%D9%86-%D8%A7%D9%84%D9%81%D8%B7%D8%B1%D8%A9",
        # "https://www.islamweb.net/ar/fatawa/1224/إعفاء-اللحية",
        # "https://www.islamweb.net/ar/fatawa/1224/%D8%A5%D8%B9%D9%81%D8%A7%D8%A1-%D8%A7%D9%84%D9%84%D8%AD%D9%8A%D8%A9?pageno=1&order="
    ]

    def parse_error(self, failure):
        yield {
            "ticketNumber": failure.request.url,
            "title": None,
            "publishDate": None,
            "navigation": None,
            "viewCount": None,
            "question": None,
            "answer": None,
            "related_questions": None
        }

    def appendDomain(self, urls):
        return list(map(lambda url: self.domain_url.strip("/") + url, urls))

    def parseQuestionDetails(self, response):
        # print("__________QUESTION DETAILS__________________")
        ticketNumber = response.request.url.split("/")[-2]

        title = response.css(".top-item h2::text").get()
        if title:
            title = re.sub(r"\n|\t|\r", "", title)

        # publishDate = response.css("meta[itemprop='datePublished']::attr(content)").get()
        metadata = response.css(".footer-item a::text").extract()
        publishDate = metadata[-1]

        navigation = response.css("li[itemprop='itemListElement'] a span::text").extract()
        if navigation:
            navigation = " > ".join(navigation)

        # viewCount = response.css(".iteminfo span::text")
        viewCount = metadata[1]
        if viewCount:
            viewCount = int(viewCount)
        else:
            viewCount = None

        texts = response.css("div[itemprop='text']")
        question = answer = None
        if len(texts) > 0:
            question = texts[0].css("p::text").extract()
            if question:
                question = " ".join(question).replace("\xa0","").replace("\u200c", "").replace("\r","")
                question = re.sub(r"\\n{2,}", " ", question)
                question = re.sub("[ً-ْ]", "", question)
            answer = texts[1].xpath("p//text()").extract()
            ignore_numbers_regex = "(" + "|".join(texts[1].xpath("p/a/text()").extract()) + ")"
            print(ignore_numbers_regex)
            if answer:
                answer = "".join(answer).replace("\xa0","").replace("\u200c", "").replace("\r","")
                answer = re.sub(r"\\n{2,}", " ", answer)
                answer = re.sub("[ً-ْ]", "", answer)
                answer = re.sub(ignore_numbers_regex, "", answer)
                answer = re.sub("( ، )+", "", answer)

                
        related_questions_texts = response.css(".tab_content.tab_1.tab_active.itemslist h2 a::text").extract()
        if related_questions_texts:
            related_questions_texts = "|".join(related_questions_texts)
        
        self.fatwa_counter += 1
        print(f"Page #{self.page_counter} | Fatwa #{self.fatwa_counter}", end='\r')

        yield {
            "ticketNumber": ticketNumber,
            "title": title,
            "publishDate": publishDate,
            "navigation": navigation,
            "viewCount": viewCount,
            "question": question,
            "answer": answer,
            "related_questions": related_questions_texts
        }


    def parseQuestionsPage(self, response):
        # print("__________QUESTION PAGE__________________")
        # Extract questions URLs from all pages
        questions_urls = response.css(".oneitems a::attr(href)").extract()
        questions_urls = self.appendDomain(questions_urls)
        
        next_page_query = response.css(".pagination li.active + li a::attr(href)").get()
        if next_page_query:
                url = response.request.url
                url = url[:url.index("?")] if "pageno" in url else url
                url += next_page_query
                yield scrapy.Request(url, errback=self.parse_error,callback=self.parseQuestionsPage)
        
        for url in questions_urls:
            request = scrapy.Request(
                url,
                # dont_filter=True,
                errback=self.parse_error,
                callback=self.parseQuestionDetails
                )
            yield request
        
       


    def parseTree(self, response):
        # print("__________TREE__________________")
        nodes_with_scripts = response.css(".tree a::attr(onclick)").extract()
        nodes_with_urls = response.css(".tree a::attr(href)").extract()
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
        print(f"Page #{self.page_counter} | Fatwa #{self.fatwa_counter}",end='\r')
        self.page_counter += 1
        # Scrape subnodes
        for url in urls:
            request = scrapy.Request(url,self.parseTree,dont_filter=False)
            # print(url,"\n\n")
            yield request
            # self.crawler.engine.crawl(request)
        if len(urls) > 0:
            request = scrapy.Request(response.request.url,self.parseQuestionsPage, dont_filter=True)
            # print(url,"\n\n")
            # self.crawler.engine.crawl(request,self)
            yield request

    def parse(self, response):
        # print("__________MAIN__________________")
        time.sleep(1)
        fatwaSectionsURLs = response.css(".fatCatleft ul li a::attr(href)").extract()
        fatwaSectionsURLs = self.appendDomain(fatwaSectionsURLs)
        for url in fatwaSectionsURLs:
            request = scrapy.Request(
                url,
                self.parseTree,
                # dont_filter=True,
                errback=self.parse_error,
                )
            yield request
        
