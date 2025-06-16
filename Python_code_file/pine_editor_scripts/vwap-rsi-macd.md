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

---

# 3.

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
vwap = ta.vwap

// Price Volume Trend (PVT)
pvt = ta.pvt

// Bollinger Bands
bbLength = 20
bbMult = 2
bbBasis = ta.sma(close, bbLength)
bbUpper = bbBasis + ta.stdev(close, bbLength) * bbMult
bbLower = bbBasis - ta.stdev(close, bbLength) * bbMult

// Stochastic RSI
stochRSI = ta.stoch(rsi, rsi, rsi, 14)

// Pivot Points
pivotPoint = (high[1] + low[1] + close[1]) / 3
support1 = pivotPoint - (high[1] - low[1])
resistance1 = pivotPoint + (high[1] - low[1])

// Average True Range (ATR)
atr = ta.atr(14)

// Supertrend Indicator
[supertrend, direction] = ta.supertrend(3, 7)

// Volume-based Institutional vs Retail Activity Detector
volumeSMA = ta.sma(volume, 20)
highVolume = volume > volumeSMA * 2
retailActivity = volume < volumeSMA
institutionalPresence = highVolume and close > vwap
retailPresence = retailActivity and close < vwap

// Create Volume Scanner Table
var table volumeTable = table.new(position=position.top_left, columns=3, rows=4, bgcolor=color.new(color.black, 20), border_width=1)

if barstate.islast
    table.cell(volumeTable, 0, 0, "Asset", text_color=color.white, bgcolor=color.new(color.gray, 50))
    table.cell(volumeTable, 1, 0, "Volume", text_color=color.white, bgcolor=color.new(color.gray, 50))
    table.cell(volumeTable, 2, 0, "Signal", text_color=color.white, bgcolor=color.new(color.gray, 50))
    
    table.cell(volumeTable, 0, 1, "Current", text_color=color.white, bgcolor=color.new(color.black, 20))
    table.cell(volumeTable, 1, 1, str.tostring(math.round(volume/1000)) + "K", text_color=color.green, bgcolor=color.new(color.black, 20))
    
    signalText = institutionalPresence ? "Inst. Buy" : (retailPresence ? "Retail Sell" : "Neutral")
    signalColor = institutionalPresence ? color.blue : (retailPresence ? color.red : color.gray)
    table.cell(volumeTable, 2, 1, signalText, text_color=signalColor, bgcolor=color.new(color.black, 20))

// Dashboard Setup
var table dashboard = table.new(position=position.top_right, columns=2, rows=8, bgcolor=color.new(color.black, 20), border_width=1)

if barstate.islast
    table.cell(dashboard, 0, 0, "Indicator", text_color=color.white, bgcolor=color.new(color.gray, 50))
    table.cell(dashboard, 1, 0, "Value", text_color=color.white, bgcolor=color.new(color.gray, 50))
    
    table.cell(dashboard, 0, 1, "EMA9", text_color=color.white, bgcolor=color.new(color.black, 20))
    table.cell(dashboard, 1, 1, str.tostring(math.round(ema9, 2)), text_color=color.blue, bgcolor=color.new(color.black, 20))
    
    table.cell(dashboard, 0, 2, "RSI", text_color=color.white, bgcolor=color.new(color.black, 20))
    rsiColor = rsi > 70 ? color.red : (rsi < 30 ? color.green : color.yellow)
    table.cell(dashboard, 1, 2, str.tostring(math.round(rsi, 1)), text_color=rsiColor, bgcolor=color.new(color.black, 20))
    
    table.cell(dashboard, 0, 3, "VWAP", text_color=color.white, bgcolor=color.new(color.black, 20))
    table.cell(dashboard, 1, 3, str.tostring(math.round(vwap, 2)), text_color=color.yellow, bgcolor=color.new(color.black, 20))
    
    table.cell(dashboard, 0, 4, "Supertrend", text_color=color.white, bgcolor=color.new(color.black, 20))
    stColor = direction == 1 ? color.green : color.red
    table.cell(dashboard, 1, 4, str.tostring(math.round(supertrend, 2)), text_color=stColor, bgcolor=color.new(color.black, 20))
    
    table.cell(dashboard, 0, 5, "MACD Signal", text_color=color.white, bgcolor=color.new(color.black, 20))
    macdSignal = macdLine > signalLine ? "Bullish" : "Bearish"
    macdColor = macdLine > signalLine ? color.green : color.red
    table.cell(dashboard, 1, 5, macdSignal, text_color=macdColor, bgcolor=color.new(color.black, 20))
    
    table.cell(dashboard, 0, 6, "BB Position", text_color=color.white, bgcolor=color.new(color.black, 20))
    bbPosition = close > bbUpper ? "Above" : (close < bbLower ? "Below" : "Inside")
    bbColor = close > bbUpper ? color.red : (close < bbLower ? color.green : color.gray)
    table.cell(dashboard, 1, 6, bbPosition, text_color=bbColor, bgcolor=color.new(color.black, 20))

// Plot main chart indicators (price-based only)
plot(ema9, title="EMA9", color=color.blue, linewidth=2)
plot(ema21, title="EMA21", color=color.red, linewidth=2)
plot(vwap, title="VWAP", color=color.yellow, linewidth=2)
plot(supertrend, title="Supertrend", color=direction == 1 ? color.green : color.red, linewidth=2)

// Bollinger Bands
p1 = plot(bbUpper, title="BB Upper", color=color.new(color.blue, 50))
p2 = plot(bbLower, title="BB Lower", color=color.new(color.blue, 50))
fill(p1, p2, color=color.new(color.blue, 90), title="BB Fill")

// Support and Resistance
plot(pivotPoint, title="Pivot Point", color=color.gray, style=plot.style_line, linewidth=1)
plot(support1, title="Support 1", color=color.new(color.green, 30), style=plot.style_line)
plot(resistance1, title="Resistance 1", color=color.new(color.red, 30), style=plot.style_line)

// Volume-based signals
plotshape(institutionalPresence, title="Institutional Buying", location=location.belowbar, color=color.blue, style=shape.triangleup, size=size.small)
plotshape(retailPresence, title="Retail Selling", location=location.abovebar, color=color.red, style=shape.triangledown, size=size.small)

// Alerts
alertcondition(ta.crossover(ema9, ema21), title="EMA Bullish Cross", message="EMA9 crossed above EMA21")
alertcondition(ta.crossunder(ema9, ema21), title="EMA Bearish Cross", message="EMA9 crossed below EMA21")
alertcondition(institutionalPresence, title="Institutional Activity", message="High institutional buying detected")
alertcondition(ta.crossover(close, supertrend), title="Supertrend Buy", message="Price crossed above Supertrend")
alertcondition(ta.crossunder(close, supertrend), title="Supertrend Sell", message="Price crossed below Supertrend")
```
