import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import plotly.graph_objs as go
from flask import Flask, render_template, request

CACHE_FILENAME = "population.json"
CACHE_DICT = {}

url = 'https://worldpopulationreview.com/'
conn = sqlite3.connect("population.sqlite", check_same_thread=False)
cur = conn.cursor()

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

def get_country_inset_table():
    url = 'https://worldpopulationreview.com/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    all_country = soup.find('tbody')
    countries = all_country.find_all('tr')
    for c in countries:
        lists = []
        names = c.find('a')
        tds = c.find_all('td')
        population = tds[3]
        area = tds[4]
        density = tds[5]
        growth = tds[6]
        rank = tds[8]
        lists.append(names.text.lower())
        lists.append(rank.text)
        lists.append(population.text)
        lists.append(area.text)
        lists.append(density.text)
        lists.append(growth.text)
        add_country_data_sql(lists)

def get_country_links():
    url = 'https://worldpopulationreview.com/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    all_country = soup.find('tbody')
    countries = all_country.find_all('tr')
    links_dic = {}
    for c in countries:
        names = c.find('a')
        link = names['href']
        key = names.text.lower()
        links_dic[key] = link
    return links_dic

def get_link(name):
    links_dic = get_country_links()
    return links_dic[name]

def get_country_link_cache(name):
    if name in CACHE_DICT.keys():
        return CACHE_DICT[name]
    else:
        url = get_link(name)
        CACHE_DICT[name] = url
        save_cache(CACHE_DICT)
        return CACHE_DICT[name]

def add_country_data_sql(lists):
    create_Countrylist = '''
    CREATE TABLE IF NOT EXISTS "CountryList" (
	"Name"	TEXT,
	"Rank"	INTEGER,
	"2019 Population"	INTEGER,
	"Area"	INTEGER,
	"2019 Density"	TEXT,
	"Growth Rate"	TEXT,
    PRIMARY KEY("Name")
);
'''
    insert_Countrylist = '''
    REPLACE INTO Countrylist
    VALUES (?, ?, ?, ?, ?, ?)
'''
    cur.execute(create_Countrylist)
    cur.execute(insert_Countrylist, lists)
    conn.commit()


def add_city_data_sql(lists):
    create_TopCity = '''
    CREATE TABLE IF NOT EXISTS "TopCity" (
	"Country"	TEXT,
	"Top1"	TEXT,
	"Top1Population"	INTEGER,
	"Capital"	TEXT,
	"Region"	TEXT,
    PRIMARY KEY("Country")
);
'''
    replace_TopCity = '''
    REPLACE INTO TopCity
    VALUES (?, ?, ?, ?, ?)
'''
    insert_TopCity = '''
    REPLACE INTO TopCity
    VALUES (?, ?, ?, ?, ?)
'''
    cur.execute(create_TopCity)
    cur.execute(replace_TopCity,lists)
    cur.execute(insert_TopCity,lists)
    conn.commit()


def get_cities(name):
    url = get_country_link_cache(name)
    full_url = 'https://worldpopulationreview.com'+ url
    response = requests.get(full_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    body = soup.find('tbody')
    trs = body.find_all('tr')
    city_list = [name]
    top = trs[0]
    tds = top.find_all('td')
    city_name = tds[0].text
    city_population = tds[1].text
    city_list.append(city_name)
    city_list.append(city_population)
    cols = soup.find_all('div', class_='col-md-4')
    div = cols[2]
    div = div.find_all('div', class_="SidebarRowDiv__StyledRow-llp1s-0 kZsnKL")
    capital = div[7]
    capital_text = capital.find('a').text
    city_list.append(capital_text)
    region = div[8]
    region_text = region.find('a').text
    city_list.append(region_text)
    add_city_data_sql(city_list)
    return city_list

def drop_all_table():
    drop_Countrylist = '''
        DROP TABLE IF EXISTS "Countrylist";
    '''
    drop_TopCity = '''
        DROP TABLE IF EXISTS "TopCity";
    '''
    conn.execute(drop_Countrylist)
    conn.execute(drop_TopCity)
    conn.commit()

def get_city_for_plot(name):
    url = get_country_link_cache(name)
    full_url = 'https://worldpopulationreview.com'+ url
    response = requests.get(full_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    body = soup.find('tbody')
    trs = body.find_all('tr')
    city_list = []
    for t in trs:
        pair = []
        tds = t.find_all('td')
        city_name = tds[0].text
        population = tds[1].text
        pair.append(city_name)
        pair.append(population)
        city_list.append(pair)
    return city_list

def get_country_by_name():
    conn = sqlite3.connect('population.sqlite')
    cur = conn.cursor()
    q = '''
        SELECT *
        FROM CountryList
        '''
    results = cur.execute(q).fetchall()
    return results

def get_cities_by_name(name):
    get_cities(name)
    conn = sqlite3.connect('population.sqlite')
    cur = conn.cursor()
    q= '''
        SELECT *
        FROM TopCity
        '''
    q2 = 'WHERE Country ="'+ name.lower() + '"'
    full_q = q+q2
    results = cur.execute(full_q).fetchall()
    results = results[0]
    return results

def get_country_history(name):
    url = get_country_link_cache(name)
    full_url = 'https://worldpopulationreview.com'+ url
    response = requests.get(full_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    his_table = soup.find_all('table', class_="datatableStyles__StyledTable-bwtkle-1 hOnuWY table table-striped")
    his_table= his_table[1]
    his_body = his_table.find('tbody')
    trs = his_body.find_all('tr')
    his_list = []
    for t in trs:
        pair = []
        tds = t.find_all('td')
        year = tds[0].text
        population = tds[1].text
        pair.append(year)
        pair.append(population)
        his_list.append(pair)
    return his_list


app = Flask(__name__)

@app.route('/')
def homepage():
    results = get_country_by_name()
    return render_template('Homepage.html', results = results)

@app.route('/chosen', methods=['POST'])
def chosen_country():
    chosen = request.form['name']
    chosen = chosen.lower()
    
    try:
        result = get_cities_by_name(chosen)
    except KeyError:
        return render_template('error.html')
    else:
        pass

    try:
        option = request.form['option']
    except KeyError:
        return render_template('error.html')
    else:
        pass

    if option == 'general':
        result = get_cities_by_name(chosen)
        chosen = chosen.capitalize()
        return render_template("country.html", chosen =chosen, result=result)

    elif option == 'cities':
        pair = get_city_for_plot(chosen)
        city_val = []
        population_val = []
        for i in pair:
            city = i[0]
            population = i[1]
            city_val.append(city)
            population_val.append(population)
        x_vals = city_val
        y_vals = population_val
        bars_data = go.Bar(
            x =x_vals,
            y =y_vals
        )
        fig = go.Figure(data = bars_data)
        div = fig.to_html(full_html=False)

        return render_template("city.html", chosen =chosen, plot_div=div)

    elif option == 'history':
        year_val = []
        his_val = []
        his_list = get_country_history(chosen)
        for i in his_list:
            year = i[0]
            his = i[1]
            year_val.append(year)
            his_val.append(his)
        x_vals_his = year_val
        y_vals_his = his_val
        scatter_data = go.Scatter(x=x_vals_his, y= y_vals_his)
        scatter_layout = go.Layout(title= "Population History")
        his_fig = go.Figure(data = scatter_data, layout = scatter_layout)
        div2 = his_fig.to_html(full_html = False)
        chosen = chosen.capitalize()
        return render_template("history.html", chosen =chosen, plot_div_history = div2)


if __name__ == '__main__':
    CACHE_DICT = open_cache()
    get_country_inset_table()
    app.run(debug=True)





