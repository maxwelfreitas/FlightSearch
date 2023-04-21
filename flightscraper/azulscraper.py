import re

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from time import sleep
from datetime import datetime as dt

#%%

class AzulScrapper():
    
    def __init__(self, headless=True):
        
        options = Options()
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        
        options.add_argument("--window-size=515,800")            
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-crash-reporter")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-in-process-stack-traces")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        
        if headless==True:
            self.headless = True
            self.driver = webdriver.Chrome(options=options)
        else:
            self.headless = False
            self.driver = webdriver.Chrome()
            
        url = 'https://www.voeazul.com.br/br/pt/home'
        btn_cookies_xpath = '//button[@id="onetrust-accept-btn-handler"]'
        self.driver.get(url)
        try:
            wait = WebDriverWait(self.driver, 30)
            btn_cookies = wait.until(EC.element_to_be_clickable((By.XPATH, btn_cookies_xpath)))
        finally:
            btn_cookies.click()
            
    
    def search_flights(self, origin, destination, departure_date, miles=True):           

        flight_offers = []
        
        days_in_advance = dt.strptime(departure_date,'%Y-%m-%d')-dt.now()
        
        # se a data para pesquisa for com atencedência menor que 2 dias não faz a pesquisa
        if days_in_advance.days < 2:
            return flight_offers

        [y,m,d]=[x for x in departure_date.split('-')]   
        query_departure_date = '/'.join([m,d,y])

        url_base = """
        https://www.voeazul.com.br/br/pt/home/selecao-voo?
        c[0].ds={origin}&
        c[0].std={query_departure_date}&
        c[0].as={destination}&
        p[0].t=ADT&p[0].c=1&p[0].cp=false&f.dl=3&f.dr=3&cc={currency}
        """
        if miles:
            currency = 'PTS'
        else:
            currency = 'BRL'
                       
        url = url_base.replace('\n','').format(origin=origin, 
                                               destination=destination, 
                                               query_departure_date=query_departure_date,
                                               currency=currency)
        url = url.replace(' ','')
        if self.headless == False:
            self.driver.set_window_size(515,800)
        self.driver.get(url)

        try:
            wait = WebDriverWait(self.driver, 30)
            results = wait.until(EC.element_to_be_clickable((By.XPATH, '//p[@class="results"]'))).text
            results = int(results.split()[0])
        except:
            results = 0
               
        if results > 8:
            load_more = True
            wait = WebDriverWait(self.driver, 30)
            while load_more:
                try:
                    btn_load_more = wait.until(EC.element_to_be_clickable((By.ID,'load-more-button')))
                    btn_load_more.location_once_scrolled_into_view
                    sleep(1)
                    btn_load_more.send_keys(Keys.PAGE_DOWN)
                    btn_load_more.click()
                    wait = WebDriverWait(self.driver, 1)
                except:
                    load_more = False
        
        card_list_xpath = '//div[@class="trip-container"]/section/div'
        card_list = self.driver.find_elements_by_xpath(card_list_xpath)
        
        for card in card_list:
            departure, arrival = re.findall('\d{2}:\d{2}',card.text)
            flight_number = re.search('\d{4}',card.find_element_by_xpath('.//p[@class="flight-leg-info"]').text).group(0)
                                
            duration_xpath = './/div[@class="info"]/div[2]/button'
            duration = re.findall('\d+',card.find_element_by_xpath(duration_xpath).text)
            if len(duration) == 2:
                duration = ':'.join(duration)
            else:
                duration = duration[0]+':00' 
            try:
                price_css = 'h4[class^="current"]'
                price = re.sub('[^\d]','',card.find_element_by_css_selector(price_css).text)
                price = int(price)
                if currency == 'BRL':
                    price = price/100
            except:
                pass
            
            try:        
                _=card.location_once_scrolled_into_view
                sleep(1)
                card.click()
                sleep(1)
                
                legs_selector = '#select-fare > div > div.modal-content__body.css-0'
                legs_modal = self.driver.find_element_by_css_selector(legs_selector) 
                legs_text = legs_modal.text.split('\n')
                legs_flights = [(i,flight) for i,flight in enumerate(legs_text) if 'Voo' in flight]
                legs = []
                
                for leg in legs_flights:
                    i,leg_flight = leg
                    leg_flight_number = leg_flight.split(' ')[-1]
                    leg_flight_from = legs_text[i-2][1:-1]
                    leg_flight_to = legs_text[i+2][1:-1]
                    legs.append((leg_flight_number,leg_flight_from,leg_flight_to))       
                    route_flights = '-'.join([leg[0] for leg in legs])
                    route_stops = '-'.join([leg[1] for leg in legs[1:]])

                btn_close_selector = '#select-fare > div > div.modal-content__header.css-0 > button'
                wait = WebDriverWait(self.driver, 30)
                btn_close = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, btn_close_selector)))
                btn_close.click()
                sleep(1)
            except:
                pass
            
            sleep(0.0001)
            offer = {'id': dt.now().isoformat(),             
                    'from':origin, 
                    'to': destination, 
                    'date': departure_date.replace('/','-'), 
                    'departure': departure, 
                    'arrival':arrival, 
                    'airline': 'AD',
                    'flight': flight_number,
                    'route_flights': route_flights,
                    'via': route_stops, 
                    'duration': duration, 
                    'price': price,
                    'currency': currency}
            flight_offers.append(offer)
        return flight_offers
    