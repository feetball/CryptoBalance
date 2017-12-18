from flask import Flask, render_template, json, request
import requests, pdb, ast, os
import pprint

import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return 'Please send coin and wallet addresses via URL.  Example: https://.../balance?ltc=<ltc_wallet_address>&btc=<btc_wallet_address>&xrp=<xrp_wallet_address> \n  Only ltc, btc and xrp are supported at this time.'

@app.after_request
def treat_as_plain_text(response):
    response.headers["content-type"] = "text/plain"
    return response


@app.route('/balance', methods=['GET'])
def show_balance():
    price_dict = {}
    balances = ""
    coin_price_string = '\nCoin Prices: \n'
    total_balance = 0

    #print 'cryptoid key: ' + os.environ['cryptoid_key']

    global coin_prices 
    coin_prices = GetCoinPricesUSD()

    if request.args.get('btc'):
        price_dict["btc"] =  GetCoinBalance('btc', request.args.get('btc'))
    if request.args.get('ltc'):
        price_dict["ltc"] = GetCoinBalance('ltc', request.args.get('ltc'))
    if request.args.get('xrp'):
        price_dict["xrp"] = GetCoinBalance('xrp', request.args.get('xrp'))

    #pdb.set_trace()
    if price_dict:
        for key, value in price_dict.items():
            balances = balances + key + ' balance (USD): $' +  value + '\n'
            total_balance = total_balance + float(value)
            coin_price_string = coin_price_string + key + '(USD) $: ' + filter(lambda coin_price: coin_price['symbol'] == key.upper(), coin_prices)[0]['price_usd'] + '\n'

        balances = balances + 'Total Balance (USD): $' + str(total_balance) + '\n' + coin_price_string         

    else:
        return 'No valid wallet addresses privided'

    return balances


def GetCoinBalance(coinName, walletAddr):

    if coinName == 'xrp' :
        url = 'https://data.ripple.com/v2/accounts/' + walletAddr
        #pdb.set_trace()
        coin_balance_request = ast.literal_eval(requests.get(url).text)
        if coin_balance_request['result'] in 'success':
            coin_balance = float(coin_balance_request['account_data']['initial_balance'])

    else:
        key = 'key=' + os.environ['cryptoid_key']
        url = 'https://chainz.cryptoid.info/' + coinName + '/api.dws?q=getbalance&' + key + '&a=' + walletAddr
        coin_balance = float(requests.get(url).text)


    floatPrice = float(filter(lambda coin_price: coin_price['symbol'] == coinName.upper(), coin_prices)[0]['price_usd'])

    balance = coin_balance * floatPrice

    return str(balance)


def GetCoinPricesUSD():
    coin_price_url = 'https://api.coinmarketcap.com/v1/ticker/'

    coin_price_response = requests.get(coin_price_url)
    coin_prices_dict =  json.loads(coin_price_response.text)

    return coin_prices_dict


if __name__ == "__main__":
	app.run()
