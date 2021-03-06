from flask import Flask, render_template, json, request

import requests, pdb, ast, os
import pprint
import pdb

import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
if 'gae' in os.environ:
    from google.appengine.ext import ndb
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
    balances = 'Coin Values: \n---------------------- \n'
    coin_price_string = '\nCoin Prices: \n---------------------- \n'
    coin_qty_string = '\nCoin Quantities: \n---------------------- \n'
    total_balance = 0

    #print 'cryptoid key: ' + os.environ['cryptoid_key']

    global coin_prices
    coin_prices = GetCoinPricesUSD()

    if request.args.get('btc'):
        price_dict['btc'] = GetCoinBalance('btc', request.args.get('btc'))
    if request.args.get('ltc'):
        price_dict['ltc'] = GetCoinBalance('ltc', request.args.get('ltc'))
    if request.args.get('xrp'):
        price_dict['xrp'] = GetXrpBalance(request.args.get('xrp'))
    if request.args.get('eth'):
        price_dict['eth'] = GetEthBalance(request.args.get('eth'))
    if request.args.get('zec'):
        price_dict['zec'] = GetZecBalance(request.args.get('zec'))
    if request.args.get('dcr'):
        price_dict['dcr'] = GetDcrBalance(request.args.get('dcr'))

    #pdb.set_trace()
    if price_dict:
        for key, value in price_dict.items():
            balances = balances + key + ' balance (USD): $' +  value[1] + '\n'
            total_balance = total_balance + float(value[1])
            coin_price_string = coin_price_string + key + '(USD): $' + filter(lambda coin_price: coin_price['symbol'] == key.upper(), coin_prices)[0]['price_usd'] + '\n'
            coin_qty_string = coin_qty_string + key + ': ' + value[0] +'\n'

        balances = balances + 'Total Balance (USD): $' + str(total_balance) + '\n' + coin_qty_string + coin_price_string

    else:
        return 'No valid wallet addresses privided'

    return balances

def GetCoinBalance(coinName, walletAddr):
    if 'gae' in os.environ:
        key = 'key=' + Settings.get('cryptoid_key')
    else:
        key = 'key=' + os.environ['cryptoid_key']
    url = 'https://chainz.cryptoid.info/' + coinName + '/api.dws?q=getbalance&' + key + '&a=' + walletAddr
    coin_balance = float(requests.get(url).text)
    floatPrice = float(filter(lambda coin_price: coin_price['symbol'] == coinName.upper(), coin_prices)[0]['price_usd'])
    balance = coin_balance * floatPrice
    return str(coin_balance), str(balance)

def GetEthBalance(walletAddr):
    if 'gae' in os.environ:
        key =  Settings.get('etherscan_key')
    else:
        key = os.environ['etherscan_key']
    url = 'https://api.etherscan.io/api?module=account&action=balance&tag=latest&apikey=' + key + '&address=' + walletAddr
    coin_balance = float(ast.literal_eval(requests.get(url).text)['result'])/10e17
    floatPrice = float(filter(lambda coin_price: coin_price['symbol'] == 'ETH', coin_prices)[0]['price_usd'])
    balance = coin_balance * floatPrice
    return str(coin_balance), str(balance)

def GetXrpBalance(walletAddr):
    url = 'https://data.ripple.com/v2/accounts/' + walletAddr + '/stats/value?limit=1&descending=true'
    coin_balance_request = ast.literal_eval(requests.get(url).text)
    if coin_balance_request['result'] in 'success':
        coin_balance = float(coin_balance_request['rows'][0]['account_value'])
    floatPrice = float(filter(lambda coin_price: coin_price['symbol'] == 'XRP', coin_prices)[0]['price_usd'])
    balance = coin_balance * floatPrice
    return str(coin_balance), str(balance)

def GetZecBalance(walletAddr):
    url = 'https://api.zcha.in/v2/mainnet/accounts/' + walletAddr
    request_data = ast.literal_eval(requests.get(url).text)
    coin_balance = float(request_data['balance'])
    floatPrice = float(filter(lambda coin_price: coin_price['symbol'] == 'ZEC', coin_prices)[0]['price_usd'])
    balance = coin_balance * floatPrice
    return str(coin_balance), str(balance)
    
def GetDcrBalance(walletAddr):
    url = 'https://mainnet.decred.org/api/addr/' + walletAddr + '/?noTxList=1'
    request_data = ast.literal_eval(requests.get(url).text)
    coin_balance = float(request_data['balance'])
    floatPrice = float(filter(lambda coin_price: coin_price['symbol'] == 'DCR', coin_prices)[0]['price_usd'])
    balance = coin_balance * floatPrice
    return str(coin_balance), str(balance)


def GetCoinPricesUSD():
    coin_price_url = 'https://api.coinmarketcap.com/v1/ticker/'

    coin_price_response = requests.get(coin_price_url)
    coin_prices_dict =  json.loads(coin_price_response.text)

    return coin_prices_dict


if 'gae' in os.environ:
    class Settings(ndb.Model):
        name = ndb.StringProperty()
        value = ndb.StringProperty()

        @staticmethod
        def get(name):
            NOT_SET_VALUE = "NOT SET"
            retval = Settings.query(Settings.name == name).get()
            if not retval:
                retval = Settings()
                retval.name = name
                retval.value = NOT_SET_VALUE
                retval.put()
            if retval.value == NOT_SET_VALUE:
                raise Exception(('Setting %s not found in the database. A placeholder record has been created.' +
                   ' Go to the Developers Console for your app in App Engine, look up the Settings record with ' +
                   'name=%s and enter its value in that records value field.') % (name, name))
            return retval.value

if __name__ == "__main__":
	app.run(host='0.0.0.0')
