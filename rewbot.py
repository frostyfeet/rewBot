import bs4
import requests
import json
from slackclient import SlackClient
import pickle
import datetime
import urllib
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

print(datetime.datetime.now())
slack_token = config['slack']['slack_token']

url_list = ['https://www.rew.ca/properties/search/869746565/sort/latest/desc/page/1',    # Vancouver
            'https://www.rew.ca/properties/search/869836757/sort/latest/desc/page/1',    # Burnaby
            'https://www.rew.ca/properties/search/869839683/sort/latest/desc/page/1',    # Port Moody
            'https://www.rew.ca/properties/search/869844572/sort/latest/desc/page/1',    # Coquitlam
            'https://www.rew.ca/properties/search/869847257/sort/latest/desc/page/1',    # New Westminster
            'https://www.rew.ca/properties/search/869850668/sort/latest/desc/page/1',    # Port Coquitlam
            'https://www.rew.ca/properties/search/869854096/sort/latest/desc/page/1',    # North Vancouver
            ]


def send_slack(content):
    sc = SlackClient(slack_token)
    print(content)
    #sc.api_call(
    #    "chat.postMessage",
    #    channel="#general",
    #    text=content,
    #    as_user=True,
    #    mrkdwn=True,
    #    username="RewBot"
    #    )


def create_file(data):
    new_dict = {}
    new_dict[data['id']] = data
    pickle_out = open("dict.pickle", "wb")
    pickle.dump(new_dict, pickle_out)
    pickle_out.close()


def check_new_listing(data):
    try:
        pickle_in = open("dict.pickle", "rb")
        old_listings = pickle.load(pickle_in)
        # comparing dics
        if data['id'] in old_listings:
            #print("No changes")
            return False
        else:
            old_listings[data['id']] = data
            pickle_out = open("dict.pickle", "wb")
            pickle.dump(old_listings, pickle_out)
            pickle_out.close() 
            print("{} - New townhouses found".format(datetime.datetime.now()))
            return True
    except Exception:
    #except FileNotFoundError as e:
        print("File not found, creating it")
        create_file(data)
        return True


def get_property_assessment(address):
    try:
        r = requests.get("https://www.bcassessment.ca/Property/Search/GetByAddress?addr={}".format(address))
        if r.status_code == 200:
            code = json.loads(r.content)[0]['value']
            r = requests.get("https://www.bcassessment.ca/Property/Info/{}".format(code))
            html = bs4.BeautifulSoup(r.content, 'html.parser')
            bc = {}
            bc['url'] = "https://www.bcassessment.ca/Property/Info/{}".format(code) 
            bc['value'] = html.find('span', {'id': "lblTotalAssessedValue"}).getText()
            return bc 
    except Exception: 
        print("Error assessing the property")


def scrape_rew(url):
    response = requests.get(url)
    html = bs4.BeautifulSoup(response.content, 'html.parser')
    iltags = html.find('div', {'class': 'organiclistings'}).findAll(lambda tag: tag.name == 'article' and tag.get('class') == ['listing'])
    return iltags


all_listings = []
for url in url_list:
    all_listings.extend(scrape_rew(url))
    print('Done scraping, starting to parse')
for listing in all_listings:
    data = {}
    data['url'] = "https://www.rew.ca{}".format(listing.find('div', {'class': 'listing-photo_container'}).find('a')['href'])
    data['title'] = listing.find('div', {'class': 'listing-header'}).find('a')['title']
    data['area'] = listing.find('div', {'class': 'listing-body'}).find('ul', {'class': 'hidden-xs listing-subheading'}).find('li').getText()
    data['price'] = listing.find('div', {'class': 'listing-body'}).find('div', {'class': 'row'}).find('div', {'class': 'listing-price'}).getText()
    data['details'] = [(lambda x: str(x.getText()))(x) for x in listing.find('div', {'class': 'listing-body'}).find('ul', {'class': 'listing-information'}).findAll('li')]
    data['id'] = listing.find('div', {'class': 'listing-body'}).find('dl', {'class': 'listing-extras hidden-xs'}).find('dd').getText()
    if check_new_listing(data):
        try:
            bc_assessed = (get_property_assessment(data['title'].split(", BC,")[0]))
            data['assessed_value'] = bc_assessed['value'] 
            data['assessed_url'] = bc_assessed['url'] 
        except Exception:
            print("Error parsing the script")
        send_slack(":house: {} - {} - :moneybag: *{}* - :mag: {} `{}` `{}` {}".format(data['title'], data['area'], data['price'], data.get('assessed_value'), data.get('assessed_url'), data['details'], data['url']))

print("{} - Script finished".format(datetime.datetime.now()))
