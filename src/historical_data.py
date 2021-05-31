import json
import time
import logging
logger = logging.getLogger(__name__)

import talib
import numpy

from constants import all_constants
from config import all_configs


class HistoricalData():
    currency = ''
    current_price = 0.0
    max_array_size = 1440

    def __init__(self):
        self.open_times = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.openes = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.highs = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.lows = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.closes = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.volumes = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.close_times = dict(all_constants.EMPTY_UNIT_ARRAY)

        self.latest_rsi = dict(all_constants.EMPTY_UNIT_DICT)
        self.reset_data = False

    def initilize_candle_data(self, candle_data, unit_time):
        self.open_times[unit_time], self.openes[unit_time], self.highs[unit_time], self.lows[unit_time], self.closes[unit_time], self.volumes[unit_time], self.close_times[unit_time] = [
            list(map(lambda each_hist: None if each_hist[6] > int(time.time() * 1000) else int(float(each_hist[_])) if float(each_hist[_]) == int(float(each_hist[_])) else float(each_hist[_]), candle_data)) for _ in range(7)]
        # Removing for the ones which has not closed
        if self.open_times[unit_time][-1] == None:
            self.open_times[unit_time].pop()
        if self.openes[unit_time][-1] == None:
            self.openes[unit_time].pop()
        if self.highs[unit_time][-1] == None:
            self.highs[unit_time].pop()
        if self.lows[unit_time][-1] == None:
            self.lows[unit_time].pop()
        if self.closes[unit_time][-1] == None:
            self.closes[unit_time].pop()
        if self.volumes[unit_time][-1] == None:
            self.volumes[unit_time].pop()
        if self.close_times[unit_time][-1] == None:
            self.close_times[unit_time].pop()

    def reset_all_data(self):
        self.open_times = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.openes = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.highs = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.lows = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.closes = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.volumes = dict(all_constants.EMPTY_UNIT_ARRAY)
        self.close_times = dict(all_constants.EMPTY_UNIT_ARRAY)

        self.latest_rsi = dict(all_constants.EMPTY_UNIT_DICT)
        self.latest_macd = dict(all_constants.EMPTY_UNIT_DICT)

    def __update_candle_data(self, candle_data, unit_time, replace_last = False):
        if (replace_last):
            self.open_times[unit_time].pop()
            self.openes[unit_time].pop()
            self.highs[unit_time].pop()
            self.lows[unit_time].pop()
            self.closes[unit_time].pop()
            self.volumes[unit_time].pop()
            self.close_times[unit_time].pop()

        if (len(self.closes[unit_time]) == self.max_array_size):
            self.open_times[unit_time].pop(0)
            self.openes[unit_time].pop(0)
            self.highs[unit_time].pop(0)
            self.lows[unit_time].pop(0)
            self.closes[unit_time].pop(0)
            self.volumes[unit_time].pop(0)
            self.close_times[unit_time].pop(0)

        self.open_times[unit_time].append(int(candle_data['t']))
        self.openes[unit_time].append(float(candle_data['o']))
        self.highs[unit_time].append(float(candle_data['h']))
        self.lows[unit_time].append(float(candle_data['l']))
        self.closes[unit_time].append(float(candle_data['c']))
        self.volumes[unit_time].append(float(candle_data['v']))
        self.close_times[unit_time].append(int(candle_data['T']))

    def update_candle_data(self, candle_data, unit_time):
        self.reset_data = False

        # Making sure with 1m we are always on tack with 12 hrs
        # This helps in reset after 12 hrs
        if (self.close_times[unit_time][-1] == int(candle_data['T']) and self.open_times[unit_time][-1] == int(candle_data['t'])):
            logger.debug("Updating the older value")
            self.__update_candle_data(candle_data, unit_time, True)
        elif (not(int(candle_data['T']) - self.close_times[unit_time][-1] == all_configs.TECHNICAL_INDICATOR_CONF.get("TIME_WINDOW_IN_MSEC").get(unit_time)) and not(int(candle_data['t']) - self.open_times[unit_time][-1] == all_configs.TECHNICAL_INDICATOR_CONF.get("TIME_WINDOW_IN_MSEC").get(unit_time))):
            logger.debug("Data is getting reset")
            self.reset_data = True
        elif (self.close_times[unit_time][-1] != int(candle_data['T']) and self.open_times[unit_time][-1] != int(candle_data['t'])):
            logger.debug("Adding new data")
            self.__update_candle_data(candle_data, unit_time, False)

    def update_latest_rsi(self, unit_time):
        for each_rsi in all_configs.TECHNICAL_INDICATOR_CONF.get("RSI").get('period'):
            if len(self.closes[unit_time]) > each_rsi:
                np_closes = numpy.array(self.closes[unit_time])
                rsi = talib.RSI(np_closes, each_rsi)
                self.latest_rsi[unit_time][each_rsi] = round(rsi[-1],2)

    def update_latest_macd(self, unit_time):
        FAST_P = all_configs.TECHNICAL_INDICATOR_CONF.get(
            "MACD").get("MACD_FAST")
        SLOW_P = all_configs.TECHNICAL_INDICATOR_CONF.get(
            "MACD").get("MACD_SLOW")
        MACD_SIG = all_configs.TECHNICAL_INDICATOR_CONF.get(
            "MACD").get("MACD_SIGNAL")
        if (len(self.closes[unit_time]) > all_configs.TECHNICAL_INDICATOR_CONF.get("MACD").get("MACD_SLOW")):
            np_closes = numpy.array(self.closes[unit_time])
            analysis = talib.MACD(
                np_closes, fastperiod=FAST_P, slowperiod=SLOW_P, signalperiod=MACD_SIG)
            self.latest_macd[unit_time] = {
                'mac': round(analysis[0][-1], 2), 'signal': round(analysis[1][-1], 2), 'histogram': round(analysis[2][-1], 2)}
