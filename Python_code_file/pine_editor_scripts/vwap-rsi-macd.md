# 1.

```
//@version=5
indicator(title="Alpha-Predator Custom Indicator", overlay=true)

// Moving Averages
ema9 = ta.ema(close, 9)
ema21 = ta.ema(close, 21)

// Relative Strength Index (RSI)
rsi = ta.rsi(close, 14)

// Moving Average Convergence Divergence (MACD)
[macdLine, signalLine, _] = ta.macd(close, 12, 26, 9)

// Volume Weighted Average Price (VWAP)
vwap = ta.vwap(close)

// Price Volume Trend (PVT)
pvt = ta.pvt

// Bollinger Bands
bbUpper = ta.sma(close, 20) + ta.stdev(close, 20) * 2
bbLower = ta.sma(close, 20) - ta.stdev(close, 20) * 2

// Stochastic RSI
stochRSI = ta.stoch(close, high, low, 14)

// Pivot Points
pivotPoint = (high + low + close) / 3
support1 = pivotPoint - (high - low)
resistance1 = pivotPoint + (high - low)

// Average True Range (ATR)
atr = ta.atr(14)

// Supertrend Indicator
[supertrend, direction] = ta.supertrend(3, 7)

// Dashboard Setup with Block Color Background
var table dashboard = table.new(position=position.top_right, columns=3, rows=10, bgcolor=color.black)
if bar_index % 10 == 0
    table.cell(dashboard, 0, 0, "Indicator", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 0, "Value", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 0, 1, "EMA9", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 1, str.tostring(ema9), text_color=color.green, bgcolor=color.black)
    table.cell(dashboard, 0, 2, "RSI", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 2, str.tostring(rsi), text_color=color.green, bgcolor=color.black)
    table.cell(dashboard, 0, 3, "MACD", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 3, str.tostring(macdLine), text_color=color.green, bgcolor=color.black)
    table.cell(dashboard, 0, 4, "VWAP", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 4, str.tostring(vwap), text_color=color.green, bgcolor=color.black)
    table.cell(dashboard, 0, 5, "Supertrend", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 5, str.tostring(supertrend), text_color=color.green, bgcolor=color.black)

// Plot indicators
plot(ema9, title="EMA9", color=color.blue)
plot(ema21, title="EMA21", color=color.red)
plot(rsi, title="RSI", color=color.purple)
plot(macdLine, title="MACD Line", color=color.green)
plot(signalLine, title="Signal Line", color=color.orange)
plot(vwap, title="VWAP", color=color.yellow)
plot(supertrend, title="Supertrend", color=color.green)
plot(bbUpper, title="BB Upper", color=color.blue)
plot(bbLower, title="BB Lower", color=color.blue)
plot(pivotPoint, title="Pivot Point", color=color.gray)
plot(support1, title="Support 1", color=color.green)
plot(resistance1, title="Resistance 1", color=color.red)
```

---

# 2.

```
//@version=5
indicator(title="Alpha-Predator Pro", overlay=true)

// Moving Averages
ema9 = ta.ema(close, 9)
ema21 = ta.ema(close, 21)

// Relative Strength Index (RSI)
rsi = ta.rsi(close, 14)

// Moving Average Convergence Divergence (MACD)
[macdLine, signalLine, _] = ta.macd(close, 12, 26, 9)

// Volume Weighted Average Price (VWAP)
vwap = ta.vwap(close)

// Price Volume Trend (PVT)
pvt = ta.pvt

// Bollinger Bands
bbUpper = ta.sma(close, 20) + ta.stdev(close, 20) * 2
bbLower = ta.sma(close, 20) - ta.stdev(close, 20) * 2

// Stochastic RSI
stochRSI = ta.stoch(close, high, low, 14)

// Pivot Points
pivotPoint = (high + low + close) / 3
support1 = pivotPoint - (high - low)
resistance1 = pivotPoint + (high - low)

// Average True Range (ATR)
atr = ta.atr(14)

// Supertrend Indicator
[supertrend, direction] = ta.supertrend(3, 7)

// Volume-based Institutional vs Retail Activity Detector
highVolume = volume > ta.sma(volume, 20) * 2  // High institutional interest
retailActivity = volume < ta.sma(volume, 20)  // Likely retail trading
institutionalPresence = highVolume and close > vwap  // Confirmed institutional buying
retailPresence = retailActivity and close < vwap  // Retail dominance in selling zone

// Create Volume Scanner Table
var table volumeTable = table.new(position=position.top_left, columns=3, rows=6, bgcolor=color.black)
if bar_index % 10 == 0
    table.cell(volumeTable, 0, 0, "Stock", text_color=color.white, bgcolor=color.black)
    table.cell(volumeTable, 1, 0, "Volume", text_color=color.white, bgcolor=color.black)
    table.cell(volumeTable, 2, 0, "Signal", text_color=color.white, bgcolor=color.black)
    
    table.cell(volumeTable, 0, 1, "Stock A", text_color=color.white, bgcolor=color.black)
    table.cell(volumeTable, 1, 1, str.tostring(volume), text_color=color.green, bgcolor=color.black)
    table.cell(volumeTable, 2, 1, institutionalPresence ? "Institutional Buy" : (retailPresence ? "Retail Sell" : "Neutral"), text_color=institutionalPresence ? color.blue : (retailPresence ? color.red : color.gray), bgcolor=color.black)

    table.cell(volumeTable, 0, 2, "Stock B", text_color=color.white, bgcolor=color.black)
    table.cell(volumeTable, 1, 2, str.tostring(volume), text_color=color.green, bgcolor=color.black)
    table.cell(volumeTable, 2, 2, institutionalPresence ? "Institutional Buy" : (retailPresence ? "Retail Sell" : "Neutral"), text_color=institutionalPresence ? color.blue : (retailPresence ? color.red : color.gray), bgcolor=color.black)

// Dashboard Setup (Block Color Background)
var table dashboard = table.new(position=position.top_right, columns=4, rows=12, bgcolor=color.black)
if bar_index % 10 == 0
    table.cell(dashboard, 0, 0, "Indicator", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 0, "Value", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 0, 1, "EMA9", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 1, str.tostring(ema9), text_color=color.green, bgcolor=color.black)
    table.cell(dashboard, 0, 2, "RSI", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 2, str.tostring(rsi), text_color=color.green, bgcolor=color.black)
    table.cell(dashboard, 0, 3, "VWAP", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 3, str.tostring(vwap), text_color=color.green, bgcolor=color.black)
    table.cell(dashboard, 0, 4, "Supertrend", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 4, str.tostring(supertrend), text_color=color.green, bgcolor=color.black)
    table.cell(dashboard, 0, 5, "Institutional Trade", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 5, str.tostring(institutionalPresence), text_color=color.blue, bgcolor=color.black)
    table.cell(dashboard, 0, 6, "Retail Trade", text_color=color.white, bgcolor=color.black)
    table.cell(dashboard, 1, 6, str.tostring(retailPresence), text_color=color.red, bgcolor=color.black)

// Plot indicators
plot(ema9, title="EMA9", color=color.blue)
plot(ema21, title="EMA21", color=color.red)
plot(rsi, title="RSI", color=color.purple)
plot(macdLine, title="MACD Line", color=color.green)
plot(signalLine, title="Signal Line", color=color.orange)
plot(vwap, title="VWAP", color=color.yellow)
plot(supertrend, title="Supertrend", color=color.green)
plot(bbUpper, title="BB Upper", color=color.blue)
plot(bbLower, title="BB Lower", color=color.blue)
plot(pivotPoint, title="Pivot Point", color=color.gray)
plot(support1, title="Support 1", color=color.green)
plot(resistance1, title="Resistance 1", color=color.red)
plot(highVolume ? close : na, title="Institutional Buying", color=color.blue, style=plot.style_circles)
plot(retailActivity ? close : na, title="Retail Selling", color=color.red, style=plot.style_circles)
```
