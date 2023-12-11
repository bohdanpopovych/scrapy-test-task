# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class YelpReviewItem(Item):
    reviewer_name = Field()
    reviewer_location = Field()
    review_date = Field()
    review_rating = Field()
    review_content = Field()


class YelpScrapperItem(Item):
    business_name = Field()
    business_rating = Field()
    reviews_count = Field()
    business_yelp_url = Field()
    business_website = Field()
    reviews = Field()
