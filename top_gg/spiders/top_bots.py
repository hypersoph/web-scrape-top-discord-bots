# -*- coding: utf-8 -*-
import scrapy
import cfscrape
from scrapy.loader import ItemLoader
from ..items import TopGgItem
import logging
from ..loader import ItemLoader

class TheLoader(ItemLoader):
    pass

class TopBotsSpider(scrapy.Spider):
    name = 'top_bots'
    allowed_domains = ['top.gg']

    scraper = cfscrape.create_scraper()

    proxy = 'http://116.202.234.235:3128'

    def start_requests(self):
        current_page = 554
        url = f'https://top.gg/list/top?page={current_page}'
        token = self.scraper.get_tokens(url)
        
        yield scrapy.Request(
            url=url,
            cookies=token[0],
            headers={
                'User-Agent':token[1]
            },
            callback = self.parse,
            meta= {
                'currentPage':current_page,
                'token':token,
                'proxy':self.proxy,
            }
            )

    def parse(self, response):
        token = response.meta['token']
        current_page = response.meta['currentPage']
        bot_listings = response.xpath("//li[contains(@class,'bot-card')]")

        for listing in bot_listings:
            sponsored = listing.xpath(".//div[@class='content sponsored']")
            if sponsored:
                continue

            loader = TheLoader(item=TopGgItem(), selector=listing, response=response)
            loader.add_xpath("bot_name", "normalize-space(.//a[@class='bot-name']/text())")
            loader.add_xpath("votes","normalize-space(.//button[contains(@class,'btn-like')]/span/text())")
            loader.add_xpath("num_servers","normalize-space(.//span[contains(@class,'servers btn')]/text())")
            loader.add_xpath("short_description","normalize-space(.//p[@class='bot-description']/text())")
            loader.add_xpath("tags","normalize-space(.//span[@class='lib']/text())")
            loader.add_xpath("img_url",".//div[@class='bot-img']/img/@src")

            relative_bot_url = listing.xpath(".//a[@class='bot-name']/@href").get()
            abs_url = f"https://top.gg{relative_bot_url}"

            print(abs_url)

            yield scrapy.Request(
                url = abs_url,
                cookies = token[0],
                headers = {
                    'User-Agent':token[1]
                },
                callback = self.parse_bot_page,
                meta = {
                    'loader':loader,
                    'proxy':self.proxy,
                    'currentPage':current_page
                }
            )

        # PAGINATION
        
        # next_page_btn = response.xpath("//div[@class='pagenumbers']")

        # if next_page_btn:
        #     current_page+=1
        #     next_url = f'https://top.gg/list/top?page={current_page}'

        #     yield scrapy.Request(
        #         url = next_url,
        #         callback = self.parse,
        #         cookies = token[0],
        #         headers = {
        #             'User-Agent':token[1]
        #         },
        #         meta = {
        #             'currentPage': current_page,
        #             'token':token,
        #             'proxy':self.proxy
        #         }
        #     )

    def parse_bot_page(self, response):
        loader = response.meta['loader']
        current_page = response.meta['currentPage']
        print(f"current page: {current_page}")
        # rebind ItemLoader to new Selector instance
        #loader.reset(selector=response.selector, response=response)
        # skipping the selector will default to response.selector, like ItemLoader
        loader.reset(response=response)
        loader.add_xpath("bot_creator","//p[@id='createdby']/b/a/span")
        loader.add_xpath("bot_prefix","//span[@id='prefix']/code/text()")
        loader.add_xpath("bot_website","//a[@id='websitelink']/@href")
        loader.add_xpath("support_server","//a[@id='support']/@href")
        loader.add_xpath("invite_link","//div[@class='titleandvote']/a/@href")
        loader.add_xpath("long_description","//div[@class='longdescription']")

        yield loader.load_item()
        

