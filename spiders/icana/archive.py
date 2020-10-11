import os
import scrapy
from datetime import datetime, timedelta
from scrapy.crawler import CrawlerProcess


class Spider(scrapy.Spider):
    name = "icana_archive"
    date_format = '%m-%d-%Y'

    report_link_css = ".BoxClass .row.NewsListMarginBottom h3 a"
    next_reports_link_href_css = "#ContentPlaceHolder1_lblPaging .Paging_Box " \
                                 "a.Paging_Item.Paging_Left_Side_Item::attr(href)"

    @staticmethod
    def _make_list_page_url(filter_date, page_number):
        return f"https://www.icana.ir/Fa/Archive/date={filter_date}%7Ccu={page_number}%7C"

    def __init__(self, date_from=None, date_to=None, **kwargs):
        self.date_from = datetime.strptime(date_from, self.date_format) if date_from else datetime.now()
        self.date_to = datetime.strptime(date_to, self.date_format) if date_to else datetime.now()
        super(Spider, self).__init__(**kwargs)

    def start_requests(self):
        # plus 1 to crawling "date_from" too.
        days = (self.date_to - self.date_from).days + 1

        for day in range(days):
            filter_date = self.date_to - timedelta(days=day)
            filter_date = filter_date.strftime(self.date_format)

            page_number = 1
            url = self._make_list_page_url(filter_date, page_number)

            callback_kwargs = {"filter_date": filter_date, "prev_page_number": page_number}
            yield scrapy.Request(url=url, callback=self.parse,
                                 cb_kwargs=callback_kwargs)

    def _parse_report(self, response):
        date_time = response.css('#ContentPlaceHolder1_lblDateTime .MT span::text').get()
        if not date_time:
            date_time = response.css('#ContentPlaceHolder1_lblDateTime::text').get()

        description = response.css('#ContentPlaceHolder1_litLead::text').get()
        if not description:
            description = response.css('#ContentPlaceHolder1_litLead .News_Lead::text').get()

        yield {
            'id': response.url.split("/")[5],
            'service': response.css('.Top_Menu_On::text').get(),
            'datetime': date_time,
            'title': response.css('h1 div.News_Title::text').get(),
            'description': description,
            'paragraphs': response.css('#ContentPlaceHolder1_litBody p *::text').getall(),
            'tags': response.css('#ContentPlaceHolder1_ucTag_Box a::attr(href)').getall(),
        }

    def parse(self, response, **kwargs):
        # handle items of this page
        reports_page_links = response.css(self.report_link_css)
        yield from response.follow_all(reports_page_links, self._parse_report)

        # if there is next page with same filter_date gets data of that and comebacks to 'parse' method.
        next_reports_link_href = response.css(self.next_reports_link_href_css).get()
        if next_reports_link_href and next_reports_link_href != "#":
            filter_date = kwargs.get("filter_date")
            page_number = kwargs.get("prev_page_number") + 1
            callback_kwargs = {"filter_date": filter_date, "prev_page_number": page_number}

            next_reports_link_url = self._make_list_page_url(filter_date, page_number)

            yield response.follow(next_reports_link_url, callback=self.parse,
                                  cb_kwargs=callback_kwargs)


def make_file_name_by_times(date_from=None, date_to=None):
    """

    :param date_from: date in format '%m-%d-%Y' like '01-28-2020'
    :param date_to: date in format '%m-%d-%Y' like '01-28-2020'
    :return: string like <date_from(may be blank)>_<date_to(may be blank)>_<timestamp>
    """
    file_name = ""
    if date_from:
        file_name += date_from

    file_name += f"_{date_to if date_to else ''}"

    return file_name + f"_{datetime.now().timestamp()}"


def execute_spider(date_from=None, date_to=None):
    """
    :param date_from: date in format '%m-%d-%Y' like '01-28-2020'
    :param date_to: date in format '%m-%d-%Y' like '01-28-2020'
    :return: None
    """
    file_name = make_file_name_by_times(date_from, date_to)

    files_dir = 'crawled_files/icana/archive/'
    if not os.path.isdir(files_dir):
        os.makedirs(files_dir)

    feeds_file_path = "%s%s.json" % (files_dir, file_name)

    process = CrawlerProcess(settings={
        # 'FEED_FORMAT': 'json',
        # 'FEED_URI': feeds_file_path,
        'FEEDS': {
            feeds_file_path: {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': None,
                'indent': 4,
            }
        }
    })

    process.crawl(Spider, date_from, date_to)
    process.start()
