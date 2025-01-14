from flask import (
    Flask,
    jsonify,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
    
)
from datetime import datetime
import requests
import threading
import time
import robin_stocks.robinhood as r
class User: 
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User: {self.username}>'

users = []
users.append(User(id=1, username='Avinash', password='Shivanna'))
users.append(User(id=2, username='Becca', password='secret'))
users.append(User(id=3, username='Carlos', password='somethingsimple'))


app = Flask(__name__)
app.secret_key = 'fnyhwrbc1fyfulg3opt6pkj25nagxphi'

# Replace with your actual API key and access token
api_key = "nou76gvyfsugbu6q"
access_token = "vUNA5Rax5fZf8patweFpahXnJKGzUo3x"
BASE_URL = 'https://kite.zerodha.com/'


@app.before_request 
def before_request():
    g.user = None

    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        g.user = user
        

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)

        username = request.form['username']
        password = request.form['password']
        
        user = [x for x in users if x.username == username][0]
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('profile'))

        return redirect(url_for('login'))

    return render_template('login.html')
# Breathing page
@app.route('/breathing1')
def breathing1():
 return render_template('breathing.html')

# Feedback page
@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/trade')
def profile():
    if not g.user:
        return redirect(url_for('login'))

    return render_template('trade.html')

executed_orders = []
position_details = []  # Replace with your actual symbols


def get_actual_executed_price(order_id):
    endpoint = f'{BASE_URL}oms/orders/trades?order_id={order_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        order_data = response.json()
        return order_data['data']['average_price']
    else:
        raise Exception(response)




def get_last_traded_price(stock_symbol):

    # Replace with the actual API endpoint provided by Zerodha for last traded price
    api_url = f"https://api.kite.trade/quote/ltp?i=NSE:{stock_symbol}"
    
    # Include your API key in the headers
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {api_key}:{access_token}"
    }

    # Make an API request
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        last_traded_price = data["data"]["NSE:" + stock_symbol]["last_price"]
        return last_traded_price
    else:
        return None


def p_n_l():

    # Replace with the actual API endpoint provided by Zerodha for last pnl price
    api_url = f"https://api.kite.trade/portfolio/positions"

    # Include your API key in the headers
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {api_key}:{access_token}"
    }

    # Make an API request
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        p_n_l = data["net"]["pnl"]
        return p_n_l
    else:
        return None

def quantity():

    # Replace with the actual API endpoint provided by Zerodha for last pnl price
    api_url = f"https://api.kite.trade/portfolio/positions"

    # Include your API key in the headers
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {api_key}:{access_token}"
    }

    # Make an API request
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        quantity = data["net"]["quantity"]
        return quantity
    else:
        return None

@app.route('/get_last_traded_price_and_profit_loss')
def get_last_traded_price_and_profit_loss():
    stock_symbol = request.args.get('symbol')
    last_traded_price = get_last_traded_price(stock_symbol)
    profit_loss = p_n_l
    quantity = quantity

    # Fetch the average price from the position details
    position = next((p for p in position_details if p['symbol'] == stock_symbol), None)
    if position:
        average_price = position['average_price']
        #quantity = position['quantity']
        # Calculate profit/loss and change percentage
        if position['type'] == 'Buy':
            profit_loss = (last_traded_price - average_price) * quantity
        elif position['type'] == 'Sell':
            profit_loss = (average_price - last_traded_price) * quantity
        else:
            profit_loss = (average_price - last_traded_price) * quantity
        # Calculate change percentage
        if average_price != 0:
            change_percentage = ((last_traded_price - average_price) / average_price) * 100
        else:
            change_percentage = 0.0

        # Update the position details with profit/loss and change percentage
        #position['profit_loss'] = profit_loss
        position['change_percentage'] = change_percentage

        data = {
            "last_traded_price": last_traded_price,
            "profit_loss": profit_loss,
            "quantity": quantity,
            "change_percentage": change_percentage
        }
        return jsonify(data)
    else:
        return ('', 404)
@app.route('/place_buy_order', methods=['POST'])
def place_buy_order():
    stock_symbol = request.form['stockSymbolBuy']
    quantity = int(request.form['quantity'])
    # Define order details for a market buy orde
    try:
        order_id = r.order_buy_market(stock_symbol, quantity )
        return render_template('trade.html', order_confirmation=f"Buy order placed successfully. Order ID: {order_id}")
    except Exception as e:
        result = f"Error placing buy order: {e}"
    return render_template('trade.html', error_message=result)


@app.route('/place_sell_order', methods=['POST'])
def place_sell_order():
    stock_symbol = request.form['stockSymbolSell']
    quantity = int(request.form['quantity'])
    # Define order details for a market buy orde
    try:
        order_id = r.order_sell_market(stock_symbol, quantity )
        return render_template('trade.html', order_confirmation=f"Buy order placed successfully. Order ID: {order_id}")
    except Exception as e:
        result = f"Error placing buy order: {e}"
    return render_template('trade.html', error_message=result)


@app.route('/position_details')
def position_details_page():
    return render_template('position_details.html', positions=position_details)

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/executed_orders')
def executed_orders_page():
    return render_template('executed_orders.html', orders=executed_orders)

@app.route('/logout')
def logout():
     session.pop('user_id',None)
     return render_template('login.html')

def run_app(port):
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

if __name__ == "__main__":
    run_app(9000)
