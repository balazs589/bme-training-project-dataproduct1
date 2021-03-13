from bokeh.io import curdoc
from bokeh.models.widgets import Tabs

from scripts.cryptochart import CryptoChart
from scripts.server import AssetPair


def main() :
    """
    Bokeh szerver inditasahoz szukseges main fuggveny.
    """
    chart = CryptoChart(
        url="https://api.kraken.com/0/public/Trades",
        asset_pairs={
            "XBTUSD" : AssetPair(name="XXBTZUSD", altname="XBTUSD"),
            "XBTEUR" : AssetPair(name="XXBTZEUR", altname="XBTEUR"),
            "OFFLINE DEMO" : AssetPair(name="DEMO", altname="DEMO"),
        },
        timestep=2500,  # [ms]
        server_timeout=4.0  # [s]
    )

    curdoc().add_root(chart.layout)
    curdoc().title = "Crypto Chart"


main()
