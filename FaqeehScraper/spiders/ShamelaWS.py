import scrapy
import json
import os
# https://www.youtube.com/watch?v=iCbQuajzShs&ab_channel=PrayerPray
class ShamelaWS(scrapy.Spider):

    def __init__(self):
        super(ShamelaWS ,self)
        # self.booksJson = json.load(open("books.json", encoding="utf-8"))
        self.bookTitles = []
        self.bookFiles = []
        self.pages_count = 0

    def closed(self, response):
        print("CLOSED")
        for file in self.bookFiles:
            file.close()
        # with open('books.json', 'w',encoding="utf-8") as f:
        #     json.dump(self.booksJson, f,ensure_ascii=False)

    name = "shamela"

    start_urls = [
        # "https://shamela.ws/category/12" # Done
        # "https://shamela.ws/category/14",
        # "https://shamela.ws/category/15",
        # "https://shamela.ws/category/16",
        # "https://shamela.ws/category/17",
        "https://shamela.ws/category/3",
        "https://shamela.ws/category/4"
    ]

    def writeToFile(self, filename, content):
        if filename in self.bookTitles:
            self.bookFiles[self.bookTitles.index(filename)].write(content)
        else:
            self.bookTitles.append(filename)
            file = open(filename, "a", encoding="utf-8")
            self.bookFiles.append(file)

    def parseBook(self, response):
        bookTitle = response.css("h1 a::text").get()
        author = response.css("h1 + div a::text").get()            
        bookKey = f"{response.request.meta['bookCategory']}-{author}-{bookTitle}"

        paragraphs = response.css(".nass.margin-top-10 p::text").extract()
        paragraph = ""
        if len(paragraphs) > 0:
            paragraph = " ".join(paragraphs).strip(" ")
            self.writeToFile(bookKey, paragraph)

        # if bookKey in self.booksJson:
        #     self.booksJson[bookKey] += " " + paragraph
        # else:
        #     self.booksJson[bookKey] = paragraph
        
        

        self.pages_count += 1
        print(f"Extracted #{self.pages_count} Pages", end='\r')

        nextBtnUrl = response.css("#fld_goto_top + a::attr(href)").get()
        if nextBtnUrl:
            request = response.follow(nextBtnUrl, callback=self.parseBook)
            request.meta['bookCategory'] = response.request.meta['bookCategory']
            yield request
        else:
            self.bookFiles[bookKey].close()
        # yield {
        #     "author":author,
        #     "title":bookTitle,
        #     "text": paragraph
        # }

    def parse(self, response):
        books_urls = response.css(".book_title::attr(href)").extract()
        category = response.request.url.split("/")[-1]
        for url in books_urls:
            request = response.follow(url+"/1", callback=self.parseBook)
            request.meta['bookCategory'] = category
            yield request
