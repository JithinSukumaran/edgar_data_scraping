import scrapy
import json
from scrapy import Request

class MainSpider(scrapy.Spider):
    name = 'main'

    def start_requests(self):
        url = 'https://efts.sec.gov/LATEST/search-index'

        for x in range(1,11):
            form1 = {
                "category":"form-cat2",
                "filter_forms":"4",
                "page":x,
                "from":(x-1)*100,
                "forms":["3","4","5"],
                "startdt":"2016-10-26",
                "enddt":"2021-10-26"
                } 
            form = json.dumps(form1)
            
            yield Request(url, callback=self.parse, 
                            body=form,method='POST',
                            dont_filter=True)
        
    def parse(self, response):
        resp = json.loads(response.body)
        hits = resp.get('hits').get('hits')
        for hit in hits:
            one = hit.get('_source').get('ciks')[1]
            two = hit.get('_source').get('adsh').replace('-','')
            three = hit.get('_source').get('xsl')
            four = hit.get('_id').split(':')[-1]

            link = f'https://www.sec.gov/Archives/edgar/data/{one}/{two}/{three}/{four}'

            yield Request(
                link,
                callback=self.parse_page,
                dont_filter=True,
                meta={'l':link}
            )

    def parse_page(self,response):
        link = response.meta.get('l')

        rows = response.xpath('//html/body/table[3]/tbody/tr')

        total = []
        if len(rows)>0:
            for row in rows:
                commmon_stock = row.xpath('.//td[1]/span/text()').extract_first()
                code = row.xpath('.//td[4]/span/text()').extract_first()
                if  commmon_stock == 'Common Stock' and code == 'P':
                    amount = row.xpath('.//td[6]/span/text()').extract_first()
                    price = row.xpath('.//td[8]/span/text()').extract()[1]
                    amount = float(amount.replace(',',''))
                    price = float(price.replace(',',''))
                    total.append(amount*price)
           
                else:
                    continue

        company_name = response.xpath('//html/body/table[2]/tr[1]/td[2]/a/text()').extract_first()

        if len(total)>= 1:
            yield {
                'From URL':link,
                'Issuer Name': company_name,
                'Purchase Price': sum(total)
            }
