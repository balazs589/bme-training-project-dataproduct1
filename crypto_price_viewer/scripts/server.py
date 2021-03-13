import numpy
import pandas
import requests

import time, math, random


class AssetPair :
    """
    A kraken API altal hasznalt elnevezeseknek.
    """

    def __init__(self, name, altname) :
        self.name = name
        self.altname = altname


class DataPoint :
    """
    A szerver altal kuldott legutolso adatok osszegyujtesehez.
    """

    def __init__(self, price=None, volume=None, time=None) :
        self.price = price
        self.volume = volume
        self.time = time


class ServerResponseError(Exception) :
    pass


class ServerDataError(Exception) :
    pass


class ServerError(Exception) :
    pass


class Server :
    """
    Adatlekerest megvalosito osztaly.
    """

    def __init__(self, url, asset_pair, timeout) :
        self.__url = url
        self.__asset_pair = asset_pair
        self.__since = None
        self.__timeout = timeout

    def __fetch_data_from_server(self) :
        """
        JSON objektum lekerese a szerverrol.
        
        Amennyiben nem volt korabbi lekerdezes, akkor default az utolso 1000 db
        kereskedesi adat, egyebkent pedig az utolso lekeres ota tortent trade-ek adatai.
        """
        if self.__since is not None :
            params = {"pair" : self.__asset_pair.altname, "since" : self.__since}
        else :
            params = {"pair" : self.__asset_pair.altname}

        try :
            response = requests.get(self.__url, params=params, timeout=self.__timeout)
        except Exception as e :
            raise ServerResponseError("Server Response Error!\n" + str(e))

        if response.status_code != 200 :
            error_string = (
                    "Server Response Error!\n"
                    + self.__url
                    + " "
                    + str(params)
                    + "\n"
                    + f"Server response status code = {response.status_code}"
            )
            raise ServerResponseError(error_string)

        return response.json()

    def __decode_json(self, json_data) :
        """
        API leirasnak megfelelo JSON obejktum konvertalasa pandas DataFrame-e,
        illetve a most nem szukseges oszlopok eldobasa.
        """
        try :
            self.__since = json_data["result"]["last"]
            list_of_trades = json_data["result"][self.__asset_pair.name]
            prices = pandas.DataFrame(
                list_of_trades,
                columns=["price", "volume", "time", "buy_or_sell", "market_or_limit", "note"]
            )
            prices.drop(columns=["buy_or_sell", "market_or_limit", "note"], inplace=True)
            prices["price"] = prices["price"].astype(float)
            prices["volume"] = prices["volume"].astype(float)
            prices["time"] = prices["time"].astype(float)
        except :
            raise ServerDataError("Error in JSON data.")
        return prices

    def get_last_price(self) :
        """
        A Server osztaly egyetlen publikusan elerheto metodusa, az
        utolso lekerdezes adatainak osszegzese 1 darab DataPoint objektumban.

         - price tagvaltozo az araknak a sulyzott atlaga
         - volume tagvaltozo a kereskedett mennyiseg osszege
         - time tagvaltozo jelenleg nincs hasznalva
        
        Ha az utolso lekerdezes soran a szerver nem valaszol, vagy a valasz 
        barmilyen oknal fogva nem tartalmaz valodi kereskedesi adatot,
        akkor egy "None" obejektummal ter vissza a fuggveny.
        """
        # SZERVER HIBA ESETEN EGY "DEMO" NEVU VALUTAVAL LEHET AZ OSZTALY MUKODESET TESZTELNI.
        if self.__asset_pair.altname == "DEMO" :  # random tesztadatok generalasa:
            t = time.time()
            x = 45000.0 + 12345.6 * math.sin(0.05 * t) + random.uniform(-3000.0, +3000.0)
            v = min(random.random(), random.random(), random.random()) * (math.cos(1.0 * t) + 1.0)
            return DataPoint(price=x, volume=v)

        # NORMAL MUKODES:
        data_point = None
        try :
            json_data = self.__fetch_data_from_server()
            prices = self.__decode_json(json_data)
            if len(prices) > 0 :
                data_point = DataPoint(
                    price=numpy.round(numpy.average(prices["price"], weights=prices["volume"]), 2),
                    volume=prices["volume"].sum(),
                    # time=prices["time"].iloc[-1]
                )
        except (ServerResponseError, ServerDataError) as e :
            print(e)  # a grafikon frissiteset nem akasztjuk meg, csak hibauzenet kerul a konzolra
        return data_point
