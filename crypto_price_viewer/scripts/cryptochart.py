import numpy
from datetime import datetime

from bokeh.models import ColumnDataSource, Panel, Div, Column, Row, Legend, HoverTool
from bokeh.models.widgets import Select
from bokeh.plotting import figure, curdoc

from .server import AssetPair, DataPoint, Server


class CryptoChart :
    def __init__(self, url, asset_pairs, timestep, server_timeout) :
        self.__timestep = timestep
        self.__url = url
        self.__asset_pairs = asset_pairs
        self.__server_timeout = server_timeout
        self.__initialize()

    def __initialize(self) :
        """
        Automatikusan frissulo grafikon + szerver adatainak beallitasa.
        """
        self.__prices = ColumnDataSource(data={"Time" : [], "Price" : [], "Volume" : [], "Avg10" : [], "Avg40" : []})
        self.__initialize_bokeh_graphics()
        self.__initialize_server()
        curdoc().add_periodic_callback(self.__periodic_update, self.__timestep)

    def __initialize_bokeh_graphics(self) :
        """
        Bokeh grafikonok alap elrendezese.
        """
        self.line1_color = "#FF4242"
        self.line2_color = "#0A284B"
        self.line3_color = "#0072B2"

        self.select_widget = Select(
            title="Valutapár",
            options=list(self.__asset_pairs.keys()),
            value="XBTUSD"
        )
        self.select_widget.on_change("value", self.__change_asset_pair)
        self.__asset_pair = self.__asset_pairs[self.select_widget.value]

        self.title_div = Div(text="<b>Kriptovaluta árfolyamok</b>", style={"font-size" : "150%", "height" : "50px"})

        self.price_div = Div(text="<b> </b>", style={"font-size" : "200%", "color" : self.line1_color})
        self.avg10_div = Div(text="<b> </b>", style={"font-size" : "150%", "color" : self.line2_color})
        self.avg40_div = Div(text="<b> </b>", style={"font-size" : "150%", "color" : self.line3_color})

        self.controls = Column(
            self.title_div,
            self.select_widget,
            self.price_div,
            self.avg10_div,
            self.avg40_div
        )

        self.__make_plot()
        self.layout = Row(self.controls, Column(self.plot1, self.plot2))
        curdoc().theme = "light_minimal"

    def __initialize_server(self) :
        """
        Az elso kapcsolat letesitesnek sikeresnek kell lennie (default utolso 1000 db adat visszakuldese),
        ennek hianyaban a program nem folytatja a mukodeset.
        """
        self.__last_data_point = None
        self.__prices.data = {"Time" : [], "Price" : [], "Volume" : [], "Avg10" : [], "Avg40" : []}

        print(self.select_widget.value)
        self.__server = Server(url=self.__url, asset_pair=self.__asset_pair, timeout=self.__server_timeout)
        self.__last_data_point = self.__server.get_last_price()
        if self.__last_data_point is None :
            print("Unsuccessful data-fetch from server.")
            exit()
        self.__last_data_point.time = datetime.now()

    def __make_plot(self) :
        """
        Grafikonok tulajdonsagainak beallitasa.

        Egy arfolyamot + mozgoatlagokat megjelenito es egy kereskedesi mennyiseget megjelenito
        grafikon letrehozasa.
        """
        p1 = figure(
            plot_width=1200,
            plot_height=600,
            title=self.__asset_pair.altname,
            x_axis_label="Idő",
            y_axis_label="Árfolyam",
            x_axis_type="datetime"
        )
        hover_tool_1 = HoverTool(
            tooltips=[
                ("Idő", "@Time{%Hh %Mm %Ss}"),
                ("Árfolyam", "@Price{0.0}"),
                ("Mozgóátlag 10", "@Avg10{0.0}"),
                ("Mozgóátlag 40", "@Avg40{0.0}"),
                ("Mennyiség", "@Volume"),
            ],
            formatters={"@Time" : "datetime"},
            mode="vline",
            line_policy="nearest",
            names=["price_scatter"]
        )
        p1.tools.append(hover_tool_1)

        circle1 = p1.plus(source=self.__prices, x="Time", y="Price", size=10, color=self.line1_color,
                          name="price_scatter")
                          
        line3 = p1.line(source=self.__prices, x="Time", y="Avg40", line_width=2, line_dash="dotted",
                        color=self.line3_color, muted_alpha=0.1)
        line2 = p1.line(source=self.__prices, x="Time", y="Avg10", line_width=2, line_dash="dashed",
                        color=self.line2_color, muted_alpha=0.1)
        line1 = p1.line(source=self.__prices, x="Time", y="Price", line_width=1, line_dash="",
                        color=self.line1_color)
        
        legend_items = [
            ("Árfolyam", [circle1]),
            ("Mozgóátlag 10", [line2]),
            ("Mozgóátlag 40", [line3])
        ]
        legend = Legend(items=legend_items)
        legend.click_policy = "mute"
        p1.add_layout(legend, "right")

        p2 = figure(
            plot_width=1200,
            plot_height=300,
            title="Kereskedett mennyiség",
            x_axis_label="Idő",
            y_axis_label="Mennyiség",
            x_range=p1.x_range,
            x_axis_type="datetime"
        )
        hover_tool_2 = HoverTool(
            tooltips=[
                ("Idő", "@Time{%Hh %Mm %Ss}"),
                ("Árfolyam", "@Price{0.0}"),
                ("Mennyiség", "@Volume"),
            ],
            formatters={"@Time" : "datetime"},
            mode="vline",
            line_policy="nearest"
        )
        p2.tools.append(hover_tool_2)

        p2.vbar(source=self.__prices, x="Time", top="Volume", bottom=0, width=1000, color="#222222")

        p1.background_fill_color = "#E0E0E0"
        p1.border_fill_color = "#EEEEEE"
        p2.background_fill_color = "#E0E0E0"
        p2.border_fill_color = "#EEEEEE"
        
        self.plot1 = p1
        self.plot2 = p2

    def __change_asset_pair(self, attr, old, new) :
        """
        A legordulo listabol valo valasztas soran lefuto fuggveny.

        Az uj valutapar adatait allitja be a szerver lekerdezesekhez.
        """
        self.__asset_pair = self.__asset_pairs[self.select_widget.value]
        self.plot1.title.text = self.__asset_pair.altname
        self.__initialize_server()

    def __periodic_update(self) :
        """
        Meghatarozott idokozonkent lefuto fuggveny.

        Elinditja a szerver lekerdezeseket, a megkapott adatok feldolgozasat,
        valamint a grafikonok adatainak frissiteset.
        """
        data_point = self.__server.get_last_price()

        if data_point is not None :
            self.__last_data_point = data_point
        else :
            self.__last_data_point.volume = 0.0
            data_point = self.__last_data_point
        data_point.time = datetime.now()

        if len(self.__prices.data["Price"]) > 0 :
            avg_10_array_length = min(9, len(self.__prices.data["Price"]))
            avg_40_array_length = min(39, len(self.__prices.data["Price"]))
            avg_10 = numpy.round(
                    (data_point.price + numpy.sum(self.__prices.data["Price"][-avg_10_array_length :]))
                    / (1 + avg_10_array_length), 4)
            avg_40 = numpy.round(
                    (data_point.price + numpy.sum(self.__prices.data["Price"][-avg_40_array_length :]))
                    / (1 + avg_40_array_length), 4)
        else :
            avg_10 = data_point.price
            avg_40 = data_point.price

        self.__prices.stream({
            "Time" : [data_point.time],
            "Price" : [data_point.price],
            "Volume" : [data_point.volume],
            "Avg10" : [avg_10],
            "Avg40" : [avg_40]
        },
            rollover=100
        )

        self.price_div.text = "<b>" + f"{self.__asset_pair.altname} :" + f"{data_point.price:10.1f}" + "</b>"
        self.avg10_div.text = "Mozgóátlag 10 :" + f"{avg_10:10.1f}"
        self.avg40_div.text = "Mozgóátlag 40 :" + f"{avg_40:10.1f}"
