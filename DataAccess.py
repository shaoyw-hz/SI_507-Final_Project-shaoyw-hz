import requests
from bs4 import BeautifulSoup
import json

CACHE_FILENAME = "resturants.json"
CACHE_DICT = {}


base_url = 'https://www.yelp.com/search?find_desc=&find_loc=Detroit%2C+MI&ns=1'

def open_cache():
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 


def get_resturant_scrape(rest_name):
    url = 'https://www.yelp.com' + name_link_dic[rest_name]
    response = requests.get(url)
    rest_req = BeautifulSoup(response.text, 'html.parser')

    price = rest_req.find('span', class_="lemon--span__373c0__3997G text__373c0__2pB8f text-color--normal__373c0__K_MKN text-align--left__373c0__2pnx_ text-bullet--after__373c0__1ZHaA text-size--large__373c0__1568g")
    price_text = price.text

    rating = rest_req.find('div', class_="lemon--div__373c0__1mboc i-stars__373c0__Y2F3O i-stars--large-4-half__373c0__2rd5j border-color--default__373c0__2oFDT overflow--hidden__373c0__8Jq2I")
    rating_text = rating['aria-lable']

    info = rest_name + price_text + rating_text
    return info


def get_resturant_cache(rest_name):
    if rest_name in CACHE_DICT.keys():
        return CACHE_DICT[rest_name]
    else:
        rest_info = get_resturant_scrape(rest_name)
        CACHE_DICT[rest_name] = rest_info
        save_cache(CACHE_DICT)
        return CACHE_DICT[rest_info]
    pass

if __name__ == "__main__":

    detroit = requests.get(base_url)
    detroit_soup = BeautifulSoup(detroit.text, 'html.parser')
    headers = detroit_soup.find_all('a', class_="lemon--a__373c0__IEZFH link__373c0__1G70M link-color--inherit__373c0__3dzpk link-size--inherit__373c0__1VFlE")
    name_link_dic={}

    for l in headers:
        key = l.text.lower()
        link = l['href']
        name_link_dic[key]=link
    
    del name_link_dic['roasting plant detroit']

    num = 0

    name_dic = {}

    for i in name_link_dic.keys():
        num += 1
        if num <= 10:
            print(num, i)
            name_dic[num]=i
        else:
            break
    
    print(name_link_dic)