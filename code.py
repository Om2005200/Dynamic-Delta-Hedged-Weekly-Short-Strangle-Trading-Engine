import requests as rq
import pandas as pd
import csv
import json
import pyotp
from logzero import logger
from datetime import datetime
import time
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import threading


class WEEKLY_STRADLE:
    def __init__(self):
        self.API_KEY = # YOUR API KEY PROVIDED BY THE BROKER 
        self.username = # YOUR CLIENT ID 
        self.password = # YOUR PASSWORD 
        self.token_file = "iron_fly_credentials.json"
        self.qr_token = # YOUR QR TOKEN
        self.live_prices = {}
        self.subscribed_tokens = set()
        self.ws_connected = False
        self.sws = None
        self.buy_greeks_last_fetched_date = None

    def default_order_json(self, path="weekly_stradle_orderbook.json"):
        data = []
        with open(path, "w") as x:
            json.dump(data, x, indent=4)
        return data

    def saving_the_order_log(self, orders, path="weekly_stradle_orderbook.json"):
        with open(path, "w") as c:
            json.dump(orders, c, indent=4)

    def initializing_the_client(self):
        try:
            totp = pyotp.TOTP(self.qr_token).now()
        except Exception as k:
            logger.error("Unavle to initailzie")
        try:
            smartapi = SmartConnect(api_key=self.API_KEY)
            session_data = smartapi.generateSession(self.username, self.password, totp)
            if not session_data.get("status", "False"):
                logger.error("Logoin failed {}".format(session_data))
            else:
                authtoken = session_data["data"]["jwtToken"]
                refreshtoken = session_data["data"]["refreshToken"]
                feedtoken = smartapi.getfeedToken()
                clientcode = self.username
                token_data = {
                    "authtoken": authtoken,
                    "apiKey": self.API_KEY,
                    "clientcode": clientcode,
                    "feedtoken": feedtoken,
                    "refreshtoken": refreshtoken,
                    "qrtoken": self.qr_token,
                    "totp": totp,
                }
                with open(self.token_file, "w") as k:
                    json.dump(token_data, k, indent=4)
                logger.info("Token data file created")
        except Exception as l:
            logger.error("Failed to get the token")
            raise l
        return token_data



    def start_websocket(self):

        if self.sws is not None:
            return
        data = self.getting_the_token_file()

        AUTH_TOKEN = data["authtoken"]
        API_KEY = data["apiKey"]
        CLIENT_CODE = data["clientcode"]
        FEED_TOKEN = data["feedtoken"]

        self.sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, FEED_TOKEN)

        def on_open(ws):
            print("WebSocket Connected")
            self.ws_connected = True

        def on_data(ws, message):
            try:
                data = message
                



                token = data.get("token")
                ltp = data.get("last_traded_price")

                if token is not None and ltp is not None:
                    ltp=float(ltp)/100 if float(ltp)>10000 else float(ltp)
                    self.live_prices[str(token)] = ltp
                    print(f"WS: Updated LTP -> Token: {token}, LTP: {ltp}")  
            except Exception as e:
                print("Data Error:", e)

        def on_error(ws, error):
            print("WebSocket Error:", error)

        def on_close(ws):
            print("WebSocket Closed")
            self.ws_connected = False

        self.sws.on_open = on_open
        self.sws.on_data = on_data
        self.sws.on_error = on_error
        self.sws.on_close = on_close

        threading.Thread(target=self.sws.connect, daemon=True).start()

    

    def subscribe_token(self, token):

        token = str(token)

        if token in self.subscribed_tokens:
            return
        if not self.ws_connected:
            print("WebSocket not connected yet")
            return
        self.sws.subscribe(
            correlation_id="abc123",
            mode=1,
            token_list=[{"exchangeType": 2, "tokens": [token]}],
        )

        self.subscribed_tokens.add(token)
        print(f"Subscribed to {token}")

    

    def get_ltp(self, token):
        return self.live_prices.get(str(token))

    def getting_the_angelone_master(
        self, path="angelone_weekly_stradle_banknifty_options.json"
    ):
        with open(path, "r") as j:
            return json.load(j)

    def getting_the_sell_leg_options_greek(self):
        with open(self.token_file) as j:
            data = json.load(j)

            auth_token = data["authtoken"]
        api_acess_point = "https://apiconnect.angelone.in/rest/secure/angelbroking/marketData/v1/optionGreek"

        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "117.199.220.240",
            "X-ClientPublicIP": "117.199.220.204",
            "X-MACAddress": "58-CD-C9-37-C7-65",
            "X-PrivateKey": self.API_KEY,
        }
        payload = {"name": "NIFTY", "expirydate": "02JUN2026"}
        # response1=session.get(api_acess_point,headers=headers)
        # print(response1.status_code)

        response2 = rq.post(api_acess_point, headers=headers, json=payload)
        json_data = response2.json()
        with open("sell_options_greeks.json", "w") as x:
            json.dump(json_data, x, indent=4)
        print(response2.text)
        return json_data

    def getting_the_buy_leg_options_greek(self, path="buy_options_greeks.json"):

        today = datetime.now().date()

        if self.buy_greeks_last_fetched_date == today:
            print("Buy Greeks already fetched today. Skipping API call.")
            return
        with open(self.token_file) as d:
            data = json.load(d)
            auth_token = data["authtoken"]
        api_endpoint = "https://apiconnect.angelone.in/rest/secure/angelbroking/marketData/v1/optionGreek"

        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "117.199.220.240",
            "X-ClientPublicIP": "117.199.220.204",
            "X-MACAddress": "58-CD-C9-37-C7-65",
            "X-PrivateKey": self.API_KEY,
        }

        payload = {"name": "NIFTY", "expirydate": "09JUN2026"}

        response = rq.post(api_endpoint, headers=headers, json=payload)

        if response.status_code != 200:
            print("Greek API failed:", response.status_code, response.text)
            return
        if not response.text.strip():
            print("Greek API returned empty response")
            return
        json_data = response.json()

        with open(path, "w") as j:
            json.dump(json_data, j, indent=4)
        

        return json_data

    def opening_the_buy_options_greeks(self, path=r"C:\Users\dasho\updated_weekly_straddle_options_greeks.json"):
        with open(path, "r") as n:
            return json.load(n)

    def getting_the_token_file(self, path="iron_fly_credentials.json"):
        with open(path, "r") as s:
            return json.load(s)

    def opening_the_sell_options_greeks_data_file(
        self, path="sell_options_greeks.json"
    ):
        with open(path, "r") as x:
            return json.load(x)

    def getting_the_ltp(self):
        data = self.getting_the_token_file()
        auth_token = data["authtoken"]
        api_endpoint = (
            "https://apiconnect.angelone.in/rest/secure/angelbroking/market/v1/quote/"
        )
        

        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "117.199.220.240",
            "X-ClientPublicIP": "117.199.220.204",
            "X-MACAddress": "58-CD-C9-37-C7-65",
            "X-PrivateKey": self.API_KEY,
        }
        payload = {"mode": "LTP", "exchangeTokens": {"NSE": ["99926000"]}}
        response = rq.post(api_endpoint, headers=headers, json=payload)
        json_data = response.json()
        print(json_data)
        with open("nifty_atm.json", "w") as x:
            json.dump(json_data, x, indent=4)
        return json_data
    def opening_the_order_log(self, path="weekly_stradle_orderbook.json"):

       try:
         with open(path, "r") as k:
            return json.load(k)

       except FileNotFoundError:
        print("Orderbook file not found. Creating new one.")
        self.default_order_json(path)
        return []

       except json.JSONDecodeError:
        print("Orderbook corrupted. Resetting file.")
        self.default_order_json(path)
        return []

    def loading_the_ltp_files(self, path="nifty_atm.json"):
        with open(path, "r") as x:
            return json.load(x)

    def logging_the_sell_legs(self, path="weekly_stradle_orderbook.json"):

     data = self.loading_the_ltp_files()
     new_data = self.opening_the_sell_options_greeks_data_file()
     order_log = self.opening_the_order_log()
     angelone_master = self.getting_the_angelone_master()
     live_prices = self.live_prices
     option_type = None

    
     

     sell_master_data = new_data["data"]
     open_sells=[o for o in order_log if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='SELL']
     if len(open_sells)>=2:
         print('An open order exists skipping the system ')
         return 
     

     for stocks in sell_master_data:

        today = datetime.now().date()
        expiry_string = stocks["expiry"]
        expiry_date = datetime.strptime(expiry_string, "%d%b%Y").date()

        if today < expiry_date:

            ltp_map = data["data"]
            ltp_map_main = ltp_map["fetched"]

            for ltps in ltp_map_main:

                ltp = float(ltps["ltp"])

                threshold = 50
                max_threshold = ltp + threshold
                min_threshold = ltp - 30

                raw_strikes = []

                for datas in sell_master_data:

                    new_strike = float(datas["strikePrice"])

                    if new_strike <= max_threshold and new_strike >= min_threshold:
                        raw_strike = datas["strikePrice"]
                        raw_strikes.append(raw_strike)

                if raw_strikes:

                    raw_atm = min(raw_strikes)

                    for atms in sell_master_data:

                        raw_strike_price = atms["strikePrice"]

                        
                        if (
                            float(raw_atm) == float(raw_strike_price)
                            and atms["optionType"] == "CE"
                        ):

                            name = atms["name"]
                            delta = atms["delta"]
                            expiry = atms["expiry"]
                            option_type = atms["optionType"]
                            strike_price = atms["strikePrice"]

                            for angels in angelone_master:

                                symbol = angels["symbol"]
                                strike = int(float(strike_price))
                                #mapping = name + expiry + str(strike) + option_type
                                expiry_formatted = datetime.strptime(expiry, "%d%b%Y").strftime("%d%b%y").upper()
                                mapping = name + expiry_formatted + str(strike) + option_type

                                if mapping == symbol:
                                    for existing in order_log:
                                        if (
                                           existing["STATUS"] == "OPEN"
                                           and existing["POSITION_TYPE"] == "SELL"
                                           and existing["SYMBOL"] == symbol and existing['OPTION_TYPE'] in ['CE','PE']
                                        ):
                                           print(f"{symbol} already open. Skipping.")
                                           break
                                          # stop function completely
                                    else:
                                      

                                      token = angels["token"]
                                      premium = live_prices.get(str(token))


                                      if premium is None:

                                        self.subscribe_token(token)
                                        continue

                                      lots_value = 35
                                      lot = 1

                                      total_premium_paid = (
                                        lot * lots_value
                                      ) * premium

                                      new_trade = {
                                        "POSITION_TYPE": "SELL",
                                        "OPTION_TYPE": option_type,
                                        "LOT": lot,
                                        "LOT_VALUE": lots_value,
                                        "ENTRY_TIME": datetime.now().isoformat(),
                                        "EXIT_TIME": None,
                                        "PREMIUM": premium,
                                        "STRIKE_PRICE": strike_price,
                                        "DELTA": delta,
                                        "TOTAL_PREMIUM_PAID": total_premium_paid,
                                        "EXPIRY": expiry,
                                        "SYMBOL": symbol,
                                        "TOKEN": token,
                                        "PNL": None,
                                        "NET_PNL": None,
                                        "STATUS": "OPEN",
                                      }

                                      order_log.append(new_trade)
                                      self.subscribe_token(token)
                                      self.saving_the_order_log(order_log)
                                      open_sells=[o for o in order_log if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='SELL']
                                      if len(open_sells)>=2:
                                          print('2 sell legs already opened skipping the process for now ')
                                          return 
                                          
                                    

                        
                        if (
                            float(raw_atm) == float(raw_strike_price)
                            and atms["optionType"] == "PE"
                        ):

                            name = atms["name"]
                            delta = atms["delta"]
                            option_type = atms["optionType"]
                            strike_price = atms["strikePrice"]
                            expiry = atms["expiry"]

                            for angel in angelone_master:

                                symbol = angel["symbol"]
                                strike = int(float(strike_price))
                                #mapping = name + expiry + str(strike) + option_type
                                expiry_formatted = datetime.strptime(expiry, "%d%b%Y").strftime("%d%b%y").upper()
                                mapping = name + expiry_formatted + str(strike) + option_type
                                if mapping == symbol:
                                    for existing in order_log:
                                        if (
                                           existing["STATUS"] == "OPEN"
                                           and existing["POSITION_TYPE"] == "SELL"
                                        ):
                                           print(f"{symbol} already open. Skipping.")
                                           break   # stop function completely
                                    else:
                                         
                                      token = angel["token"]
                                      premium = live_prices.get(str(token))

                                      if premium is None:
                                        self.subscribe_token(token)
                                        continue

                                      lots_value = 35
                                      lot = 1

                                      total_premium_paid = (
                                        lot * lots_value
                                      ) * premium

                                      new_trade = {
                                        "POSITION_TYPE": "SELL",
                                        "OPTION_TYPE": option_type,
                                        "LOT": lot,
                                        "LOT_VALUE": lots_value,
                                        "ENTRY_TIME": datetime.now().isoformat(),
                                        "EXIT_TIME": None,
                                        "PREMIUM": premium,
                                        "STRIKE_PRICE": strike_price,
                                        "DELTA": delta,
                                        "TOTAL_PREMIUM_PAID": total_premium_paid,
                                        "EXPIRY": expiry,
                                        "SYMBOL": symbol,
                                        "TOKEN": token,
                                        "PNL": None,
                                        "NET_PNL": None,
                                        "STATUS": "OPEN",
                                      }

                                      order_log.append(new_trade)
                                      self.subscribe_token(token)
                                      self.saving_the_order_log(order_log) 
                                      open_sells=[o for o in order_log if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='SELL']
                                      if len(open_sells)>=2:
                                          print('An open order eixtss ')
                                          return 
                                      


                                    
                                    
                                        
                                            

    def logging_the_buy_legs(self, path="weekly_stradle_orderbook.json"):
        data = self.loading_the_ltp_files()
        new_data = self.opening_the_buy_options_greeks()
        orderbook = self.opening_the_order_log()
        angelone_master = self.getting_the_angelone_master()
        live_prices = self.live_prices
        open_buys=[o for o in orderbook if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='BUY']
        if len(open_buys)>=2:
            print('open position exists skipping the process')
            return 
        

        stock_master = new_data["data"]
        content = []
        for stocks in stock_master:
            expiry_str = stocks["expiry"]
            expiry_date = datetime.strptime(expiry_str, "%d%b%Y").date()
            today = datetime.now().date()
            if today < expiry_date:

                deltas = abs(float(stocks["delta"]))
                target = 0.10
                threshold = 0.02
                max_threshold = target + threshold
                min_threshold = target - threshold
                
                if deltas >= min_threshold and deltas <= max_threshold:
                    content.append(stocks)
        if not content:
            return
        # Find max strike CE and PE separately within the filtered content
        ce_candidates = [s for s in content if s["optionType"] == "CE"]
        pe_candidates = [s for s in content if s["optionType"] == "PE"]
        
        raw_strike_ce = min(
            ce_candidates,
            key=lambda x: abs(abs(float(x["delta"])) - target)
        )["strikePrice"] if ce_candidates else None

        raw_strike_pe = min(
            pe_candidates,
            key=lambda x: abs(abs(float(x["delta"])) - target)
        )["strikePrice"] if pe_candidates else None

        for atms in stock_master:
            raw_strike = atms["strikePrice"]
            option_type = atms["optionType"]
            if raw_strike_ce is not None and float(raw_strike) == float(raw_strike_ce) and option_type == "CE":
                name = atms["name"]
                delta = atms["delta"]
                option_type = atms["optionType"]
                strike_price = atms["strikePrice"]
                expiry = atms["expiry"]
                expiry_formatted = datetime.strptime(
                expiry, "%d%b%Y"
                ).strftime("%d%b%y").upper()
                for angels in angelone_master:
                    symbol = angels["symbol"]
                    na = name
                    option = option_type
                    strike = int(float(strike_price))
                    strike_str = str(strike)
                    exp = expiry
                    mapping = na + expiry_formatted + strike_str + option
                    if mapping == symbol:
                        for existing in orderbook:
                            if (
                                existing["STATUS"] == "OPEN"
                                and existing["POSITION_TYPE"] == "BUY"

                            ):
                                print(f"{symbol} BUY already open. Skipping.")
                                break
                        else:



                            symboli = angels["symbol"]
                            token = angels["token"]
                            premium = live_prices.get(str(token))
                            if premium is None:
                                self.subscribe_token(token)
                                print(f"SIGNAL GENERATED: SELL CE | Strike: {strike_price} | Delta: {delta} | Symbol: {symboli} | Premium: {premium}")

                                continue


                            lot_value = 35
                            lot = 2
                            total_quantity = lot * lot_value
                            total_premium_paid = total_quantity * premium
                            new_trade = {
                              "POSITION_TYPE": "BUY",
                              "OPTION_TYPE": option_type,
                              "LOT": lot,
                              "LOT_VALUE": lot_value,
                              "ENTRY_TIME": datetime.now().isoformat(),
                              "EXIT_TIME": None,
                              "PREMIUM": premium,
                              "STRIKE_PRICE": strike_price,
                              "DELTA": delta,
                              "TOTAL_PREMIUM_PAID": total_premium_paid,
                              "EXPIRY": exp,
                              "SYMBOL": symboli,
                              "TOKEN": token,
                              "PNL": None,
                              "NET_PNL": None,
                              "STATUS": "OPEN",
                            }
                            orderbook.append(new_trade)
                            self.saving_the_order_log(orderbook)
                            self.subscribe_token(token)
                            open_buys=[o for o in orderbook if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='BUY']
                            if len(open_buys)>=2:
                                print('An open position aleady exiuts')
                                return 
                            


                            break

                        
                    
            #if float(raw_strike_price) == float(raw_strike) and option_type == "PE":
            if raw_strike_pe is not None and float(raw_strike) == float(raw_strike_pe) and option_type == "PE":
                
                name = atms["name"]
                delta = atms["delta"]
                option_type = atms["optionType"]
                strike_price = atms["strikePrice"]
                expiry = atms["expiry"]

                trade_created = False
                for angles in angelone_master:
                    symbol = angles["symbol"]
                    na = name
                    option = option_type
                    strike = int(float(strike_price))
                    strike_str = str(strike)
                    exp = expiry
                    expiry_formatted = datetime.strptime(
                        expiry, "%d%b%Y"
                    ).strftime("%d%b%y").upper()
                    mapping = na + expiry_formatted + strike_str + option
                    if mapping == symbol:
                        for existing in orderbook:
                            if (
                                  existing["STATUS"] == "OPEN"
                                  and existing["POSITION_TYPE"] == "BUY"
                                 
                                ):
                                   print(f"{symbol} BUY already open. Skipping.")
                                   break
                        else:


                            
                            symboli = angles["symbol"]
                            token = angles["token"]
                            premium = live_prices.get(str(token))
                            if premium is None:
                              self.subscribe_token(token)

                              print(f"SIGNAL GENERATED: SELL CE | Strike: {strike_price} | Delta: {delta} | Symbol: {symboli} | Premium: {premium}")
                              continue

                            
                            lot_value = 35
                            lot = 1

                            total_premium_paid = (lot_value * lot) * premium
                            new_trade = {
                              "POSITION_TYPE": "BUY",
                              "OPTION_TYPE": option_type,
                              "LOT": lot,
                              "LOT_VALUE": lot_value,
                              "ENTRY_TIME": datetime.now().isoformat(),
                              "EXIT_TIME": None,
                              "PREMIUM": premium,
                              "STRIKE_PRICE": strike_price,
                              "DELTA": delta,
                              "TOTAL_PREMIUM_PAID": total_premium_paid,
                              "EXPIRY": expiry,
                              "SYMBOL": symboli,
                              "TOKEN": token,
                              "PNL": None,
                              "NET_PNL": None,
                             "STATUS": "OPEN",
                            }
                        #orders = self.opening_the_order_log()
                            orderbook.append(new_trade)
                            self.subscribe_token(token)
                            trade_created = True
                            self.saving_the_order_log(orderbook)
                            open_buys=[o for o in orderbook if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='BUY']
                            if len(open_buys)>=2:
                                print('Buy legs crated ')
                                return 
                            

                            break

                    
                        

                    

    def exiting_the_trades(self):

        orderbook = self.opening_the_order_log()
        buy_greeks = self.opening_the_buy_options_greeks()
        sell_greeks = self.opening_the_sell_options_greeks_data_file()
        live_prices = self.live_prices
        angelone_master = self.getting_the_angelone_master()
        master_data_for_buy = buy_greeks["data"]
        master_data_for_sell = sell_greeks["data"]
        today = datetime.now().date()
        for order in orderbook:
            open_sells=[o for o in orderbook if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='SELL']
            open_buys=[o for o in orderbook if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='BUY']
            status = order["STATUS"]
            position_type = order["POSITION_TYPE"]
            option_type = order["OPTION_TYPE"]
            delta = order["DELTA"]
            premium_paid = order["PREMIUM"]
            total_premium_paid = order["TOTAL_PREMIUM_PAID"]
            quantity = order["LOT_VALUE"]
            lot = order["LOT"]
            position_expiry = datetime.strptime(order["EXPIRY"], "%d%b%Y").date()
            symbol = order["SYMBOL"]
            token = order["TOKEN"]
            strike_price = order["STRIKE_PRICE"]
            new_target_ce = []
            new_target_pe = []
            today = datetime.now().date()
            if (
                status == "OPEN"
                and position_type == "BUY"
                and option_type in ["CE", "PE"]
            ):
                if today == position_expiry:
                    current_ltp = live_prices.get(str(token))
                    current_value = (quantity * lot) * current_ltp
                    net_profit = current_value - total_premium_paid
                    order["STATUS"] = "CLOSED"
                    order["EXIT_TIME"] = today
                    order["PNL"] = current_value
                    order["NET_PNL"] = net_profit
                    #order = self.opening_the_order_log()
                    self.saving_the_order_log(orderbook)
            if (
                status == "OPEN"
                and position_type == "SELL"
                and option_type in ["CE", "PE"]
            ):
                if today == position_expiry:
                    current_ltp = live_prices.get(str(token))
                    current_value = (quantity * lot) * current_ltp
                    net_profit = current_value - total_premium_paid
                    order["STATUS"] = "CLOSED"
                    order["EXIT_TIME"] = today
                    order["PNL"] = current_value
                    order["NET_PNL"] = net_profit
                    #order = self.opening_the_order_log()
                    self.saving_the_order_log(orderbook)
            if status == "OPEN" and position_type == "SELL" and option_type == "CE":
                if today != position_expiry:
                    for numers in master_data_for_sell:
                        numers_strike = numers["strikePrice"]
                        numers_option_type = numers["optionType"]
                        numers_expiry = datetime.strptime(
                            numers["expiry"], "%d%b%Y"
                        ).date()
                        if (
                            float(numers_strike) == float(strike_price)
                            and numers_option_type == option_type
                            and numers_expiry == position_expiry
                        ):
                            updated_delta = float(numers["delta"])
                            target_delta = 0.15
                            if updated_delta >= target_delta:
                                current_premium = live_prices.get(str(token))
                                if current_premium is None:
                                    self.subscribe_token(token)

                                    
                                    continue
                                current_value = (quantity * lot) * current_premium

                                print("the existing position will be exited shortly")
                                order["STATUS"] = "CLOSED"
                                order["EXIT_TIME"] = datetime.now()
                                order["PNL"] = current_value
                                order["NET_PNL"] = current_value - total_premium_paid
                                for hedge_order in orderbook:
                                    if (
                                        hedge_order["STATUS"] == "OPEN"
                                        and hedge_order["POSITION_TYPE"] == "SELL"
                                        and hedge_order["OPTION_TYPE"] == "PE"
                                        and hedge_order["EXPIRY"] == position_expiry
                                    ):
                                        pe_token = hedge_order["TOKEN"]
                                        pe_symbol = order["SYMBOL"]
                                        pe_qant = 35
                                        pe_lots = hedge_order["LOT"]

                                        pe_total_premium = order["TOTAL_PREMIUM_PAID"]
                                        current_premium = live_prices.get(str(pe_token))
                                        current_val = (
                                            pe_qant * pe_lots
                                        ) * current_premium
                                        net_profit = current_val - pe_total_premium

                                        hedge_order["STATUS"] = "CLOSED"
                                        hedge_order["PNL"] = current_val
                                        hedge_order["NET_PNL"] = net_profit

                                        hedge_order["EXIT_TIME"] = datetime.now()
                        new_delta = 0.40
                        threshold = 0.02
                        max_threshold = new_delta + threshold
                        min_threshold = new_delta - threshold
                        delta_value = float(numers["delta"])
                        if min_threshold <= delta_value <= max_threshold:
                            # new_target_pe.append(numers)

                            if numers["optionType"] == "CE":
                                new_target_ce.append(numers)
                            elif numers["optionType"] == "PE":
                                new_target_pe.append(numers)
                    if new_target_ce and new_target_pe:
                        best_stock_ce = sorted(
                            new_target_ce,
                            key=lambda x: abs(float(x["delta"])),
                            reverse=True,
                        )[0]
                        best_stock_pe = sorted(
                            new_target_pe,
                            key=lambda x: abs(float(x["delta"])),
                            reverse=True,
                        )[0]
                        for best_stock in [best_stock_ce, best_stock_pe]:
                            trade_created = False
                            open_sells=[o for o in orderbook if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='SELL']
                            open_buys=[o for o in orderbook if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='BUY']
                            if len(open_sells)>=2 or len(open_buys)>=2:
                                break

                            for angel in angelone_master:
                                expiry_formatted=datetime.strptime(best_stock['expiry'],'%d%b%Y').strftime('%d%b%y').upper()

                                mapping = (
                                    best_stock["name"]
                                    + expiry_formatted
                                    + str(int(float(best_stock["strikePrice"])))
                                    + best_stock["optionType"]
                                )

                                if mapping == angel["symbol"]:

                                    token_new = angel["token"]
                                    premium = live_prices.get(str(token_new))
                                    if premium is None:
                                        self.subscribe_token(token)
                                        continue
                                    

                                    lots = 2
                                    lot_value = 35
                                    premium_paid = (lots * lot_value) * premium

                                    new_order = {
                                        "POSITION_TYPE": "SELL",
                                        "OPTION_TYPE": best_stock["optionType"],
                                        "LOT": lots,
                                        "LOT_VALUE": lot_value,
                                        "ENTRY_TIME": datetime.now(),
                                        "EXIT_TIME": None,
                                        "PREMIUM": premium,
                                        "STRIKE_PRICE": best_stock["strikePrice"],
                                        "DELTA": best_stock["delta"],
                                        "TOTAL_PREMIUM_PAID": premium_paid,
                                        "EXPIRY": best_stock["expiry"],
                                        "PNL": None,
                                        "SYMBOL": angel["symbol"],
                                        "TOKEN": token_new,
                                        "NET_PNL": None,
                                        "STATUS": "OPEN",
                                    }

                                    orderbook.append(new_order)
                                    self.subscribe_token(token_new)
                                #if trade_created:

                                    self.saving_the_order_log(orderbook)
                                    break

                                    
            elif status == "OPEN" and position_type == "SELL" and option_type == "PE":

                if today != position_expiry:

                    for numers in master_data_for_sell:
                        numers_expiry = datetime.strptime(
                            numers["expiry"], "%d%b%Y"
                        ).date()
                        if (
                            numers["strikePrice"] == strike_price
                            and numers["optionType"] == option_type
                            and numers_expiry == position_expiry
                        ):

                            if float(numers["delta"]) >= 0.15:

                                current_premium = live_prices.get(str(token))
                                if current_premium is None:
                                    self.subscribe_token(token)
                                    continue


                                current_value = (quantity * lot) * current_premium

                                order["STATUS"] = "CLOSED"
                                order["EXIT_TIME"] = datetime.now()
                                order["PNL"] = current_value
                                order["NET_PNL"] = current_value - total_premium_paid

                                for hedge_order in orderbook:
                                    if (
                                        hedge_order["STATUS"] == "OPEN"
                                        and hedge_order["POSITION_TYPE"] == "SELL"
                                        and hedge_order["OPTION_TYPE"] == "CE"
                                        and hedge_order["EXPIRY"] == position_expiry
                                    ):

                                        ce_token = hedge_order["TOKEN"]
                                        ce_ltp = live_prices.get(str(ce_token))
                                        if ce_ltp is None:
                                            self.subscribe_token(token)
                                            continue
                                        
                                        ce_value = (
                                            order["LOT_VALUE"] * order["LOT"]
                                        ) * ce_ltp

                                        hedge_order["STATUS"] = "CLOSED"
                                        hedge_order["EXIT_TIME"] = datetime.now()
                                        hedge_order["PNL"] = ce_value
                                        hedge_order["NET_PNL"] = (
                                            ce_value - order["TOTAL_PREMIUM_PAID"]
                                        )
                        delta_value=float(numers['delta'])
                        if 0.38 <= delta_value <= 0.42:
                            if numers["optionType"] == "CE":
                                new_target_ce.append(numers)
                            elif numers["optionType"] == "PE":
                                new_target_pe.append(numers)
                    if new_target_ce and new_target_pe:

                        best_ce = sorted(
                            new_target_ce,
                            key=lambda x: abs(float(x["delta"])),
                            reverse=True,
                        )[0]
                        best_pe = sorted(
                            new_target_pe,
                            key=lambda x: abs(float(x["delta"])),
                            reverse=True,
                        )[0]

                        for best_stock in [best_ce, best_pe]:
                            open_sells=[o for o in orderbook if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='SELL']
                            open_buys=[o for o in orderbook if o['STATUS']=='OPEN' and o['POSITION_TYPE']=='BUY']
                            if len(open_sells)>=2 or len(open_buys)>=2:
                                break


                            for angel in angelone_master:
                                expiry_formatted=datetime.strptime(best_stock['expiry'],'%d%b%Y').strftime('%d%b%y').upper()
                                mapping = (
                                    best_stock["name"]
                                    + expiry_formatted
                                    + str(int(float(best_stock["strikePrice"])))
                                    + best_stock["optionType"]
                                )  # FIXED

                                if mapping == angel["symbol"]:

                                    token_new = angel["token"]
                                    premium = live_prices.get(str(token_new))
                                    if premium is None:
                                        self.subscribe_token(token)
                                        continue

                                    
                                    lots = 2
                                    lot_value = 35
                                    premium_paid = (lots * lot_value) * premium

                                    new_order = {
                                        "POSITION_TYPE": "SELL",
                                        "OPTION_TYPE": best_stock["optionType"],
                                        "LOT": lots,
                                        "LOT_VALUE": lot_value,
                                        "ENTRY_TIME": datetime.now(),
                                        "EXIT_TIME": None,
                                        "PREMIUM": premium,
                                        "STRIKE_PRICE": best_stock["strikePrice"],
                                        "DELTA": best_stock["delta"],
                                        "TOTAL_PREMIUM_PAID": premium_paid,
                                        "EXPIRY": best_stock["expiry"],
                                        "PNL": None,
                                        "SYMBOL": angel["symbol"],
                                        "TOKEN": token_new,
                                        "NET_PNL": None,
                                        "STATUS": "OPEN",
                                    }

                                    orderbook.append(new_order)
                                    self.subscribe_token(token_new)
                                    self.saving_the_order_log(orderbook)
                                    
                                

if __name__ == "__main__":

    W = WEEKLY_STRADLE()

    print("Initializing client...")
    W.initializing_the_client()

    print("Creating fresh orderbook...")
    
    print("Starting WebSocket...")
    W.start_websocket()
    W.subscribe_token("99926000")

    time.sleep(3)  # Give WS time to connect

    print("Fetching master & initial Greeks...")
    W.getting_the_angelone_master()
    W.getting_the_sell_leg_options_greek()
    W.getting_the_buy_leg_options_greek()  # Fetch buy Greeks initially

    print("Starting 1 minute strategy loop...")

    while True:
        try:
            print("Running strategy cycle at:", datetime.now())

            # Fetch ATM LTP (index price)
            W.getting_the_ltp()

            # Fetch Greeks every loop (both sell and buy)
            W.getting_the_sell_leg_options_greek()
            #W.getting_the_buy_leg_options_greek()  # <-- Now updates every loop
            W.opening_the_buy_options_greeks()
            # Strategy Execution
            W.logging_the_sell_legs()
            W.logging_the_buy_legs()
            W.exiting_the_trades()

            print("Cycle completed.")
            print("Sleeping 60 seconds...\n")
            

            time.sleep(60)
        except Exception as e:
            print("ERROR IN LOOP:", e)
            time.sleep(5)
