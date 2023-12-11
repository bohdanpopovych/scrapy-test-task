from urllib.parse import quote_plus
import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError
from .. import YelpScrapperItem, YelpReviewItem


class YelpSpider(scrapy.Spider):
    name = "Yelp"

    def start_requests(self):
        category = quote_plus(getattr(self, 'category', 'Contractors'))
        location = quote_plus(getattr(self, 'location', 'San+Francisco, CA'))
        start_url = f'https://www.yelp.com/search?find_desc={category}&find_loc={location}'
        yield scrapy.Request(url=start_url, callback=self.parse)

    def parse(self, response):
        elements = response.xpath('.//div/h3/span/a')
        for element in elements:
            yield scrapy.Request('https://www.yelp.com' + element.attrib['href'], callback=self.get_business_id)

        next_page = response.xpath('//a[@aria-label="Next"]/@href').extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def get_business_id(self, response):
        yelp_biz_id = response.xpath('.//*[@name="yelp-biz-id"]/@content').extract_first()
        overall_rating = response.xpath(
            '//a[@href="#reviews"]/..//preceding-sibling::span[1]/text()').extract_first()
        website = response.xpath(
            '//p[contains(text(), "Business website")]//following-sibling::p/a/text()').extract_first()
        api_url = f'https://www.yelp.com/biz/{yelp_biz_id}/props'
        business_url = f'https://www.yelp.com/biz/{yelp_biz_id}'
        return scrapy.Request(
            api_url,
            callback=self.get_business_details,
            meta={
                'rating': overall_rating,
                'url': business_url,
                'website': website
            })

    def get_business_details(self, response):
        response_json = response.json()
        # website_value = response_json['bizDetailsPageProps']['bizPortfolioProps']['ctaProps']['raqProps']['website']
        item = YelpScrapperItem()
        item['business_yelp_url'] = response.meta.get('url')
        item['business_rating'] = response.meta.get('rating')
        item['business_name'] = response_json['bizDetailsPageProps']['businessName']
        item['business_website'] = response.meta.get('website')
        reviews = []

        try:
            for review_json in response_json['bizDetailsPageProps']['reviewFeedQueryProps']['reviews']:
                review = YelpReviewItem()
                review['reviewer_name'] = review_json['user']['markupDisplayName']
                review['reviewer_location'] = review_json['user']['displayLocation']
                review['review_date'] = review_json['localizedDate']
                review['review_rating'] = review_json['rating']
                review['review_content'] = review_json['comment']['text']
                reviews.append(review)
                if len(reviews) >= 5:
                    break
        except KeyError as ex:
            print('No reviews')

        item['reviews'] = reviews
        return item

    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
