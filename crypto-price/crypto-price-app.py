import streamlit as st
from PIL import Image
import pandas as pd
import base64
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
import json
import time

#page expands to full width
st.set_page_config(layout="wide")

#title
image = Image.open('cryptologo.jpg')
st.image(image,width=500)

st.title('Crypto Price App')
st.markdown("""
This simple app I made retrieves cryptocurrency prices for the top 100 cryptocurrencies from coinmarketcap
""")

#about
expander_bar = st.beta_expander("About")
expander_bar.markdown("""
* **Python libraries:** base64,pandas,streamlit,matplotlib,beautifulsoup,requests,json,time
* **Data source:** [CoinMarketCap](http://coinmarketcap.com).
""")

#page layout
##divide page to 3 columns, col1=sidebar, col2 and col3 = page contents
col1 = st.sidebar
col2,col3 = st.beta_columns((2,1)) #col 2 to col 3 ratio is 2:1

#sidebar + main panel
col1.header('Input Options')

#sidebar - currency price unit
currency_price_unit = col1.selectbox('Select currency for price',('USD','BTC','ETH'))

#web scraping for coinmarketcap Data
@st.cache
def load_data():
    cmc = requests.get('https://coinmarketcap.com')
    soup = BeautifulSoup(cmc.content, 'html.parser')

    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    coins = {}
    coin_data = json.loads(data.contents[0])
    #st.markdown(coin_data)
    listings = coin_data['props']['initialState']['cryptocurrency']['listingLatest']['data']
    for i in listings:
      coins[str(i['id'])] = i['slug']

    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []

    for i in listings:
      coin_name.append(i['slug'])
      coin_symbol.append(i['symbol'])
      price.append(i['quote'][currency_price_unit]['price'])
      percent_change_1h.append(i['quote'][currency_price_unit]['percentChange1h'])
      percent_change_24h.append(i['quote'][currency_price_unit]['percentChange24h'])
      percent_change_7d.append(i['quote'][currency_price_unit]['percentChange7d'])
      market_cap.append(i['quote'][currency_price_unit]['marketCap'])
      volume_24h.append(i['quote'][currency_price_unit]['volume24h'])

    df = pd.DataFrame(columns=['coin_name', 'coin_symbol', 'market_cap', 'percent_change_1h', 'percent_change_24h', 'percent_change_7d', 'price', 'volume_24h'])
    df['coin_name'] = coin_name
    df['coin_symbol'] = coin_symbol
    df['price'] = price
    df['percent_change_1h'] = percent_change_1h
    df['percent_change_24h'] = percent_change_24h
    df['percent_change_7d'] = percent_change_7d
    df['market_cap'] = market_cap
    df['volume_24h'] = volume_24h
    return df

df = load_data()

##sidebar - crypto selections
sorted_coin = sorted(df['coin_symbol'])
selected_coin = col1.multiselect('Cryptocurrency',sorted_coin,sorted_coin)

df_selected_coin = df[(df['coin_symbol'].isin(selected_coin))] #filtering the data

#sidebar - number of coins to display
num_coin = col1.slider('Display Top N Coins',1,100,100)
df_coins = df_selected_coin[:num_coin]

#sidebar - percent change timeframe
percent_timeframe = col1.selectbox('Percent change timeframe',['7d','24h','1h'])
percent_dict={"7d":'percent_change_7d',"24h":'percent_change_24h',"1h":'percent_change_1h'}
selected_percent_timeframe = percent_dict[percent_timeframe]

#sidebar - sorting values
sort_values = col1.selectbox('Sort values?',['Yes','No'])

col2.subheader('Price Data of Selected Cryptocurrency')
col2.write('Data Dimension: '+str(df_selected_coin.shape[0])+' rows and '+str(df_selected_coin.shape[1])+' columns.')

col2.dataframe(df_coins)

#download csv data
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode() #string <-> bytes conversion
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File</a>'
    return href

col2.markdown(filedownload(df_selected_coin),unsafe_allow_html=True)

#prepare data for bar plot of %price change
col2.subheader('Table of % Price Change')
df_change = pd.concat([df_coins.coin_symbol,df_coins.percent_change_1h,df_coins.percent_change_24h,df_coins.percent_change_7d],axis=1)
df_change = df_change.set_index('coin_symbol')
df_change['positive_percent_change_1h'] = df_change['percent_change_1h'] > 0
df_change['positive_percent_change_24h'] = df_change['percent_change_24h'] > 0
df_change['positive_percent_change_7d'] = df_change['percent_change_7d'] > 0
col2.dataframe(df_change)

#conditional creation of bar plot ( time frame )
col3.subheader('Bar plot of % Price Change')

if percent_timeframe == '7d':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_7d'])
    col3.write('*7 days period*')
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top=1,bottom=0)
    df_change['percent_change_7d'].plot(kind='barh',color=df_change.positive_percent_change_7d.map({True:'g',False:'r'}))
    col3.pyplot(plt)
elif percent_timeframe=='24h':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_24h'])
    col3.write('*24 hour period*')
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top=1,bottom=0)
    df_change['percent_change_24h'].plot(kind='barh',color=df_change.positive_percent_change_7d.map({True:'g',False:'r'}))
    col3.pyplot(plt)
else:
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_1h'])
    col3.write('*1 hour period*')
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top=1,bottom=0)
    df_change['percent_change_1h'].plot(kind='barh',color=df_change.positive_percent_change_7d.map({True:'g',False:'r'}))
    col3.pyplot(plt)
