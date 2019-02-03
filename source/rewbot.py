import bs4
import requests
import json
from slackclient import SlackClient
import pickle
import datetime
import urllib
import os
import configparser
import boto3


slack_token = ""

url_list = ['https://www.rew.ca/properties/search/869746565/sort/latest/desc/page/1',    # Vancouver
            'https://www.rew.ca/properties/search/869836757/sort/latest/desc/page/1',    # Burnaby
            'https://www.rew.ca/properties/search/869839683/sort/latest/desc/page/1',    # Port Moody
            'https://www.rew.ca/properties/search/869844572/sort/latest/desc/page/1',    # Coquitlam
            'https://www.rew.ca/properties/search/869847257/sort/latest/desc/page/1',    # New Westminster
            'https://www.rew.ca/properties/search/869850668/sort/latest/desc/page/1',    # Port Coquitlam
            'https://www.rew.ca/properties/search/869854096/sort/latest/desc/page/1',    # North Vancouver
            ]


client = boto3.client('s3')
s3_bucket = "temp-lambda-files"
filename = "rewbot.pickle"
path = "/tmp/"
full_path = "{}{}".format(path, filename)


def send_slack(content):
    sc = SlackClient(slack_token)
    sc.api_call(
        "chat.postMessage",
        channel="#general",
        text=content,
        as_user=True,
        mrkdwn=True,
        username="RewBot"
        )


def create_file(data):
    try:
        pickle_out = open(full_path, "wb")
        pickle.dump(data, pickle_out)
        pickle_out.close()
        client.upload_file(full_path, s3_bucket, filename)
    except Exception:
        print("Error creating key")


def download_from_s3():
    try:
        client.download_file(s3_bucket, filename, full_path)
    except Exception:
        print("File not found in s3")


def load_pickle():
    if not os.path.isfile(full_path):
        download_from_s3()
    try:
        pickle_in = open(full_path, "rb")
        print("loaded file")
        old_listings = pickle.load(pickle_in)
        return old_listings
    except FileNotFoundError:
        print("File not found in disk")
        return {}


def check_new_listing(data, old_listings):
    # comparing dics
    if data['id'] in old_listings:
        return False
    else:
        old_listings[data['id']] = data
        print("{} - New townhouses found".format(datetime.datetime.now()))
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
    organic_listings = html.find('div', {'class': 'organiclistings'})
    if organic_listings:
        return organic_listings.findAll(lambda tag: tag.name == 'article' and tag.get('class') == ['listing'])


def handler(event, context):
    all_listings = []
    old_listings = load_pickle()
    new_listings = []

    for url in url_list:
        listings = scrape_rew(url)
        if listings:
            all_listings.extend(listings)
    for listing in all_listings:
        data = {}
        data['url'] = "https://www.rew.ca{}".format(listing.find('div', {'class': 'listing-photo_container'}).find('a')['href'])
        data['title'] = listing.find('div', {'class': 'listing-header'}).find('a')['title']
        data['area'] = listing.find('div', {'class': 'listing-body'}).find('ul', {'class': 'hidden-xs listing-subheading'}).find('li').getText()
        data['price'] = listing.find('div', {'class': 'listing-body'}).find('div', {'class': 'row'}).find('div', {'class': 'listing-price'}).getText()
        data['details'] = [(lambda x: str(x.getText()))(x) for x in listing.find('div', {'class': 'listing-body'}).find('ul', {'class': 'listing-information'}).findAll('li')]
        data['id'] = listing.find('div', {'class': 'listing-body'}).find('dl', {'class': 'listing-extras hidden-xs'}).find('dd').getText()
        if check_new_listing(data, old_listings):
            try:
                old_listings[data['id']] = data
                bc_assessed = (get_property_assessment(data['title'].split(", BC,")[0]))
                data['assessed_value'] = bc_assessed['value']
                data['assessed_url'] = bc_assessed['url']
                new_listings.append(data)
            except Exception:
                print("Error parsing the script")
    print("{} new listings found".format(len(new_listings)))
    for data in new_listings:
        print(send_slack(":house: {} - {} - :moneybag: *{}* - :mag: {} `{}` `{}` {}".format(data['title'], data['area'], data['price'], data.get('assessed_value'), data.get('assessed_url'), data['details'], data['url'])))
    if (len(new_listings) > 0): 
        create_file(old_listings)