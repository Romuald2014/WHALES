# Import packages
import numpy as np
import pandas as pd
import requests
import json
from datetime import datetime
import streamlit as st
import matplotlib.pyplot as plt

st.write("""
# Million Token Whales Monitor
Show Holders with balance over 5000 tokens!
""")


# Create a function to get request from ethplorer ether api https://ethplorer.io/
def api(url):
    return requests.get(url).json()


# Set constants
token_address = '0x6b4c7a5e3f0b99fcd83e9c089bddd6c7fce5c611'  # Million token address
server = 'https://api.ethplorer.io'  # Ethereum Tokens Explorer server
api_key = 'EK-apFd1-LfyHfCL-QydoE'  # My Ethereum ethplorer api key (you can get yours free one on site
# https://ethplorer.io/ or use word "freekey" for limited information request)

# Get token info
url_token_info = server + '/getTokenInfo/' + token_address + '?apiKey=' + api_key
token_info_dict = api(url_token_info)
token_info_dict.keys()

# Get constants
decimals = int(token_info_dict['decimals'])
holders_count = int(token_info_dict['holdersCount'])
total_supply = int(token_info_dict['totalSupply']) / 10 ** decimals
rate = round(token_info_dict['price']['rate'], ndigits=2)

# Get top 1000 token holders
url_holders = server + '/getTopTokenHolders/' + token_address + '?apiKey=' + api_key + '&limit=1000'
request_dict = api(url_holders)
holders = request_dict['holders']

# Create a dataframe
holders_df = pd.DataFrame.from_dict(holders)
holders_df.balance = holders_df.balance * 10 ** -18  # Calculate balance field
holders_df.balance = holders_df.balance.round(decimals=2)  # For convenience leave 2 digits

# Set the Whales Treshold for ballance over 5000  (excluding TL)
whales = holders_df[holders_df.balance > 5000]
# For convenience, set balance as integers
whales.balance = whales.balance.round().astype(int)
whales.reset_index(drop=True, inplace=True)

#st.write("""
### Total Whales Today:  """ + str(len(whales)) + """ Total Holders Today: """ + str(holders_count))

actual = pd.DataFrame([[len(whales), holders_count, rate]], columns=['WHALES', 'TOTAL HOLDERS', 'RATE'])
actual = actual.set_index([['']])

st.header("""
ACTUAL DATA
""")
st.write(actual)

# Calculate total whales and TL balance
tl_balance = holders_df.iloc[0].balance.round().astype(int)
whales_balance = whales.balance.sum() - tl_balance

labels = ['Other Whales', 'TL', 'Other holders']
shares = [whales_balance, tl_balance, (total_supply - whales_balance - tl_balance)]

st.header("""
Tokens Balance Share
""")
fig1, ax1 = plt.subplots()
ax1.pie(shares, labels=labels, autopct='%1.1f%%')
ax1.axis('equal')

# Plot
st.pyplot(fig1)


# Function to get list of all holder's operations
def get_operations(holder_address, api_key=api_key, token_address=token_address):
    #url_operations_info = server + '/getAddressHistory/' + holder_address + '?apiKey=' + api_key + '&limit=1000'
    url_operations_info = server + '/getAddressHistory/' + holder_address + '?apiKey=' + api_key + \
                          '&limit=1000&type=transfer&token=' + token_address
    operations_info_list = api(url_operations_info)
    return operations_info_list['operations']


# Function to get list of holder's operations with token
def token_operations(token_address, holder_address, operations):
    """
    Returns List of pairs for each operation:
    numbers ot the days ago and quantity transferred
    """
    t_operations = []
    for operation in operations:
        if operation['tokenInfo']['address'] == token_address and operation['type'] == 'transfer':
            sign = 1 if operation['to'] == holder_address.lower() else -1  # define sign of transactions (in or out)
            da = (datetime.now() - datetime.fromtimestamp(operation['timestamp'])).days  # Calculate operation days ago
            days_ago = da if da > 0 else 0  # Fixing da <0 because of time zone
            t_operations.append([days_ago, sign * round((float(operation['value']) * 10 ** -18), ndigits=2)])
    return t_operations


# Function for calculate Today's sells
def sum_today(tops):
    S = 0
    for top in tops:
        if top[0] == 0:
            S += top[1]
    return S


# Create list with information about operations for each whale
ops_list = []
for i, addr in enumerate(whales.address):
    ops = get_operations(addr)
    tops = token_operations(token_address, addr, ops)
    ops_list.append(
        [addr, tops[-1][0], tops[-1][1], tops[0][0], tops[0][1], sum_today(tops), len(tops)])

# Transform to dataframe with propped field names (DA - abbreviation for "days ago")
operations_df = pd.DataFrame(ops_list,
                             columns=['address', 'FIRST TRANSFER DA*', 'First Op Q-ty', 'LAST TRANSFER DA*',
                                      'Last Op Q-ty', "24H VOLUME", 'TOTAL TRANSACTIONS'])

# Whales Names
whales_names = pd.read_csv('whales_names.csv', index_col=0)
whales = whales.merge(whales_names, how="left", left_on="address", right_on="address")

# Merge with whales table
whales = whales.merge(operations_df, on='address')
whales.columns = ['ADDRESS', 'BALANCE', 'SHARE', 'NAME', 'FIRST*',
                  'First Op Q-ty', 'LAST*', 'Last Op Q-ty', "24H VOLUME",
                  'TOTAL TRANSACTIONS']

st.header("""
Whales Table
""")
st.write(whales[['NAME', 'BALANCE', 'SHARE', 'FIRST*', 'LAST*', "24H VOLUME", 'TOTAL TRANSACTIONS', 'ADDRESS']])

st.write("""
*FIRST / LAST - the number of days since first / last token's transfer 
(for whales with transactions number over 500 not relevant)
""")

# TODAY'S IN
td_in = whales[whales["24H VOLUME"] > 0]["24H VOLUME"].sum()
# TODAY'S OUT
td_out = whales[whales["24H VOLUME"] < 0]["24H VOLUME"].sum()

in_out = pd.DataFrame([[td_in, td_out]], columns=['IN', 'OUT'])
in_out = in_out.set_index([['Tokens']])

st.header("24H WHALES TRANSACTIONS VOLUMES")
st.bar_chart(in_out)