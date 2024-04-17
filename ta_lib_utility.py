import talib
import numpy as np
from candles import candle_patterns

def calculate_rsi(data, period=14):
    data['RSI'] = talib.RSI(data['Close'], timeperiod=period)
    return data

def calculate_macd(data):
    macd, signal, hist = talib.MACD(data['Close'])
    data['MACD'] = macd
    data['MACD_Signal'] = signal
    data['MACD_Histogram'] = hist
    return data

def calculate_dmi_and_adx(data, period=14):
    adx = talib.ADX(data['High'], data['Low'], data['Close'], timeperiod=period)
    data['ADX'] = adx
    data['DMI+'] = talib.PLUS_DI(data['High'], data['Low'], data['Close'], timeperiod=period)
    data['DMI-'] = talib.MINUS_DI(data['High'], data['Low'], data['Close'], timeperiod=period)
    return data

def calculate_roc(data, period=12):
    data['ROC'] = talib.ROC(data['Close'], timeperiod=period)
    return data

def calculate_bollinger_bands_width(data, period=20, nbdevup=2, nbdevdn=2):
    upper, middle, lower = talib.BBANDS(data['Close'], timeperiod=period, nbdevup=nbdevup, nbdevdn=nbdevdn)
    data['BB_Width'] = (upper - lower) / middle
    return data

def calculate_moving_averages(data, short_window=50, medium_window=100, long_window=200):
        short_ma = data['Close'].rolling(window=short_window, min_periods=1).mean()
        medium_ma = data['Close'].rolling(window=medium_window, min_periods=1).mean()
        long_ma = data['Close'].rolling(window=long_window, min_periods=1).mean()
        data['Short MA'] = short_ma
        data['Medium MA'] = medium_ma
        data['Long MA'] = long_ma
        return data

@staticmethod
def calculate_atr(data, high_col='High', low_col='Low', close_col='Close', period=14):
        high = data[high_col].values
        low = data[low_col].values
        close = data[close_col].values

        atr = talib.ATR(high, low, close, timeperiod=period)
        data['ATR'] = atr

        return data

def handle_candle_pattern(data):
        for pattern_name, pattern_data in candle_patterns.items():
            pattern_function_name = pattern_data['function']
            pattern_description = pattern_data['description']
            pattern_function = getattr(talib, pattern_function_name)
            result = pattern_function(data['Open'], data['High'], data['Low'], data['Close'])
            result_filtered = np.where(result != 0, result, np.nan)
            data[pattern_name + '_result'] = result_filtered
            data[pattern_name + 'description'] = pattern_description  

        data.dropna(how='all', inplace=True)
        return data