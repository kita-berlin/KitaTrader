import time
from datetime import datetime
from bokeh.layouts import column, row
from bokeh.models import Select, Slider, Spacer
from bokeh.models.widgets import (
    TextInput,
    Select,
    Div,
    DatePicker,
    CheckboxGroup,
    RadioButtonGroup,
)
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler

from Settings import *
from TradingClass import TradingClass
from CoFu import *


#############################################
class MainWindow:
    def __init__(self):
        self.isSave = False
        self.TradingClass = TradingClass()
        self.tradeState = 0

        # OnAnyInputChanged
        # region
        def OnAnyInputChanged(attr, old, new):
            if self.isSave:
                system_settings = SystemSettings(
                    default_symbol_name=symbolInput.value,
                    TradeDirection=modeInput.value,
                    init_balance=initBalanceInput.value,
                    start_dt=startDateInput.value,
                    end_dt=endDateInput.value,
                    Rebuy1stPercent=rebuy1stInput.value,
                    RebuyPercent=rebuyInput.value,
                    TakeProfitPercent=takeProfitInput.value,
                    Volume=volumeInput.value,
                    is_visual_mode=str(0 in visualMode.active),
                    speed=str(self.speed.value),
                    chart_bars=chartBarsInput.value,
                    default_timeframe_value=timeframeInput.value,
                    TimeframeUnits=timeframeUnitInput.value,
                    Platform="me_files",
                    platform_parameter=folderInput.value,
                )
                self.CoFu.SaveSettings(
                    os.path.join("Files", "System.json"), system_settings
                )
            pass

        # endregion

        # Load setting
        # region
        error, system_settings = self.TradingClass.LoadSettings(self)
        if "" != error:
            today = datetime.now()
            system_settings = Guiparameters(
                "",  # data path
                "",  # symbol
                str(TradeDirection.neither).split(".")[1],
                "0",  # balance
                "2024-01-01",
                today.strftime("%Y-%m-%d"),
                "0",
                "0",
                "0",
                "0",  # volume
                0,  # visual mode
                0,  # speed
                "0",  # chart bars
                "0",  # timeframe value
                str(TimeframeUnits.sec).split(".")[1],
                Platform=Platform.me_files,
            )
        # endregion

        # Widgets
        # region
        # File input
        folderTitle = Div(text="Data path:", width=100)
        folderInput = TextInput(
            value=system_settings.platform_parameter,
            sizing_mode="fixed",
            width=800,
            height=30,
        )
        folderInput.on_change("value", OnAnyInputChanged)

        # symbol input
        symbolTitle = Div(text="symbol", width=100)
        symbolInput = TextInput(
            value=system_settings.default_symbol_name,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        symbolInput.on_change("value", OnAnyInputChanged)

        # Mode input
        modeTitle = Div(text="Mode:", width=100)
        modeInput = Select(
            options=[member.name for member in TradeDirection],
            value=system_settings.TradeDirection,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        modeInput.on_change("value", OnAnyInputChanged)

        # Balance input
        initBalanceTitle = Div(text="Init. Balance:", width=100)
        initBalanceInput = TextInput(
            value=system_settings.init_balance,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        initBalanceInput.on_change("value", OnAnyInputChanged)

        # start date
        startDateTitle = Div(text="start date:", width=100)
        startDateInput = DatePicker(
            value=system_settings.start_dt,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        startDateInput.on_change("value", OnAnyInputChanged)

        # End date
        endDateTitle = Div(text="End date:", width=100)
        endDateInput = DatePicker(
            value=system_settings.end_dt,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        endDateInput.on_change("value", OnAnyInputChanged)

        # 1st rebuy percent input
        rebuy1stTitle = Div(text="1st RebuyPercent%:", width=100)
        rebuy1stInput = TextInput(
            value=system_settings.Rebuy1stPercent,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        rebuy1stInput.on_change("value", OnAnyInputChanged)

        # RebuyPercent percent input
        rebuyTitle = Div(text="RebuyPercent%:", width=100)
        rebuyInput = TextInput(
            value=system_settings.RebuyPercent,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        rebuyInput.on_change("value", OnAnyInputChanged)

        # Take profit input
        takeProfitTitle = Div(text="Take profit%:", width=100)
        takeProfitInput = TextInput(
            value=system_settings.TakeProfitPercent,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        takeProfitInput.on_change("value", OnAnyInputChanged)

        # Volume input
        volumeTitle = Div(text="Volume:", width=100)
        volumeInput = TextInput(
            value=system_settings.Volume,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        volumeInput.on_change("value", OnAnyInputChanged)

        # speed slider
        self.speed = Slider(
            title="speed", start=0, value=int(system_settings.speed), end=1000, step=1
        )
        self.speed.on_change("value", OnAnyInputChanged)

        # Visual mode checkbox
        visualMode = CheckboxGroup(labels=["Visual Mode"], active=[])
        visualMode.on_change("active", OnAnyInputChanged)
        if "True" == system_settings.is_visual_mode:
            if 0 == len(visualMode.active):
                visualMode.active.append(0)
        else:
            if len(visualMode.active) > 0:
                visualMode.active.remove(0)

        # start, Pause, Stop control
        self.controlButtons = RadioButtonGroup(
            labels=["start", "Pause", "Stop"], active=2
        )
        pass

        ###################################
        def onChartTimeframeUnitChanged(attr, old, new):
            if self.isSave:
                OnAnyInputChanged(attr, old, new)
                self.TradingClass.GuiParams.TimeframeUnits = new
                self.TradingClass.default_timeframe_seconds = (
                    self.TradingClass.get_timeframe_from_gui_params(
                        self.TradingClass.GuiParams
                    )
                )

                self.TradingClass.bars = self.TradingClass.market_data.get_bars(
                    self.TradingClass.bin_settings
                )
                self.TradingClass.update_chart_text_and_bars()

        ###################################
        def onChartTimeframeChanged(attr, old, new):
            if self.isSave:
                OnAnyInputChanged(attr, old, new)
                self.TradingClass.GuiParams.default_timeframe_value = new
                self.TradingClass.default_timeframe_seconds = (
                    self.TradingClass.get_timeframe_from_gui_params(
                        self.TradingClass.GuiParams
                    )
                )

                self.TradingClass.bars = self.TradingClass.market_data.get_bars(
                    self.TradingClass.bin_settings
                )
                self.TradingClass.update_chart_text_and_bars()

        ###################################
        def onChartBarsChanged(attr, old, new):
            if self.isSave:
                OnAnyInputChanged(attr, old, new)
                newSize = int(new)
                if newSize > int(self.TradingClass.bars.count / 1.1):
                    self.TradingClass.bars = self.TradingClass.market_data.get_bars(
                        self.TradingClass.bin_settings
                    )

                self.TradingClass.chart.bars_in_chart = newSize
                self.TradingClass.update_chart_text_and_bars()

        # bars in chart input
        chartBarsTitle = Div(text="bars in chart:", width=100)
        chartBarsInput = TextInput(
            value=system_settings.chart_bars,
            sizing_mode="fixed",
            width=150,
            height=30,
        )
        chartBarsInput.on_change("value", onChartBarsChanged)

        # Timeframe in chart input
        timeFrameTitle = Div(text="Timeframe:", width=60)
        timeframeInput = TextInput(
            value=system_settings.default_timeframe_value,
            sizing_mode="fixed",
            width=75,
            height=30,
        )
        timeframeInput.on_change("value", onChartTimeframeChanged)

        timeframeUnitTitle = Div(text="Unit:", width=20)
        timeframeUnitInput = Select(
            value=system_settings.TimeframeUnits,
            options=[member.name for member in TimeframeUnits],
            sizing_mode="fixed",
            width=70,
            height=30,
        )
        timeframeUnitInput.on_change("value", onChartTimeframeUnitChanged)
        # endregion

        # Text output labels
        # region
        balanceLabel = Div(text="Balance:", width=70)
        self.TradingClass.BalanceValue = Div(text=initBalanceInput.value, width=100)

        equityLabel = Div(text="Equity:", width=70)
        self.TradingClass.EquityValue = Div(text=initBalanceInput.value, width=100)

        datetimeLabel = Div(text="DateTime:", width=70)
        self.TradingClass.DatetimeValue = Div(text=startDateInput.value, width=150)

        maxEqDdLabel = Div(text="Max.Eq.Dd:", width=70)
        self.TradingClass.MaxEqDdValue = Div(text="0", width=100)
        self.isSave = True
        # endregion

        ###################################
        def ConnectionLost(sessionContext):
            exit()

        ###################################
        def MainLoop():
            self.doc.add_next_tick_callback(MainLoop)

            if 0 == self.tradeState:  # idle
                if 0 != self.TradingClass.bars.count:
                    time.sleep(0.1)
                    if self.controlButtons.active == 0:  # wait for start pressed
                        self.prevDtMs = int(time.time_ns() / 200000.0)
                        self.TradingClass.start()  # start the bot
                        self.tradeState = 1

            elif 1 == self.tradeState:  # trade loop
                if self.controlButtons.active == 1:  # Pause pressed
                    self.tradeState = 2
                elif (
                    self.TradingClass.Tick()
                    or self.controlButtons.active
                    == 2  # End date reached or stop pressed
                ):
                    self.tradeState = 3
                else:  # active loop
                    if 1000 != self.speed.value:
                        time.sleep((1000.0 - self.speed.value) / 1000.0)
                        self.TradingClass.update_chart_text_and_bars()
                    elif self.TradingClass.time.date() != self.MyPrevTime.date():
                        self.TradingClass.update_chart_text_and_bars()

            elif 2 == self.tradeState:  # pause
                if self.controlButtons.active == 0:  # Pause pressed
                    self.tradeState = 1

            elif 3 == self.tradeState:  # stop
                self.TradingClass.Stop()
                self.TradingClass.update_chart_text_and_bars()
                self.TradingClass.pre_start(system_settings)
                self.tradeState = 0
                self.controlButtons.active = 2

            self.MyPrevTime = self.TradingClass.time

        ###################################
        def ModifyDoc(doc):
            self.doc = doc
            self.TradingClass.pre_start(system_settings)  # init grafic, etc.
            self.MyPrevTime = self.TradingClass.time

            doc.title = "Quantrosoft Python Backtester"
            doc.add_root(
                column(
                    row(folderTitle, folderInput),
                    row(symbolTitle, symbolInput),
                    row(
                        modeTitle,
                        modeInput,
                        Spacer(width=20),
                        visualMode,
                        Spacer(width=50),
                        self.controlButtons,
                    ),
                    row(
                        initBalanceTitle,
                        initBalanceInput,
                        Spacer(width=50),
                        row(self.speed),
                    ),
                    row(
                        startDateTitle,
                        startDateInput,
                        Spacer(width=20),
                        balanceLabel,
                        self.TradingClass.BalanceValue,
                        equityLabel,
                        self.TradingClass.EquityValue,
                    ),
                    row(
                        endDateTitle,
                        endDateInput,
                        Spacer(width=20),
                        datetimeLabel,
                        self.TradingClass.DatetimeValue,
                        maxEqDdLabel,
                        self.TradingClass.MaxEqDdValue,
                    ),
                    row(
                        rebuy1stTitle,
                        rebuy1stInput,
                        Spacer(width=20),
                        rebuyTitle,
                        rebuyInput,
                        Spacer(width=20),
                        takeProfitTitle,
                        takeProfitInput,
                    ),
                    row(volumeTitle, volumeInput),
                    row(
                        chartBarsTitle,
                        chartBarsInput,
                        Spacer(width=20),
                        timeFrameTitle,
                        timeframeInput,
                        # Spacer(width=20),
                        timeframeUnitTitle,
                        timeframeUnitInput,
                    ),
                    self.TradingClass.chart.OhlcPlot,
                )
            )

            self.tradeState = 0
            self.TradingClass.update_chart_text_and_bars()
            doc.add_next_tick_callback(MainLoop)
            # https://docs.bokeh.org/en/latest/_modules/bokeh/events.html
            doc.js_on_event("connection_lost", ConnectionLost)

        # start Bokeh server
        # region
        # Bokeh app and server setup
        apps = {"/": Application(FunctionHandler(ModifyDoc))}
        server = Server(apps, port=5000)
        server.start()
        server.io_loop.current().add_callback(  # Add callback to show the server's main page
            server.show, "/"
        )
        server.io_loop.current().start()  # start the I/O loop
        # endregion


#############################################
MainWindow()  # starts Bokeh server and does not return

# end of file
