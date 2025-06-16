# 1.

```
//@version=5
indicator("Trendlines & Support/Resistance", overlay=true, max_lines_count=100, max_labels_count=50)

// Input parameters
trendline_length = input.int(20, "Trendline Length", minval=5, maxval=100)
sr_length = input.int(10, "Support/Resistance Length", minval=5, maxval=50)
min_touches = input.int(2, "Minimum Touches for S/R", minval=2, maxval=5)
extend_lines = input.bool(true, "Extend Lines")
show_labels = input.bool(true, "Show Labels")

// Colors
bullish_color = input.color(color.green, "Bullish Trendline Color")
bearish_color = input.color(color.red, "Bearish Trendline Color")
support_color = input.color(color.blue, "Support Color")
resistance_color = input.color(color.orange, "Resistance Color")

// Line styles
line_style = input.string("Solid", "Line Style", options=["Solid", "Dashed", "Dotted"])
line_width = input.int(2, "Line Width", minval=1, maxval=5)

// Convert line style
get_line_style() =>
    switch line_style
        "Solid" => line.style_solid
        "Dashed" => line.style_dashed
        "Dotted" => line.style_dotted
        => line.style_solid

// Find pivot highs and lows
pivot_high = ta.pivothigh(high, sr_length, sr_length)
pivot_low = ta.pivotlow(low, sr_length, sr_length)

// Initialize trendline variables
var line uptrend_line = na
var line downtrend_line = na
var line support_line = na
var line resistance_line = na

// Variables for trendline calculation
var float last_pivot_high = na
var int last_pivot_high_bar = na
var float prev_pivot_high = na
var int prev_pivot_high_bar = na

var float last_pivot_low = na
var int last_pivot_low_bar = na
var float prev_pivot_low = na
var int prev_pivot_low_bar = na

// Update pivot high data
if not na(pivot_high)
    prev_pivot_high := last_pivot_high
    prev_pivot_high_bar := last_pivot_high_bar
    last_pivot_high := pivot_high
    last_pivot_high_bar := bar_index - sr_length

// Update pivot low data
if not na(pivot_low)
    prev_pivot_low := last_pivot_low
    prev_pivot_low_bar := last_pivot_low_bar
    last_pivot_low := pivot_low
    last_pivot_low_bar := bar_index - sr_length

// Draw resistance trendline
if not na(last_pivot_high) and not na(prev_pivot_high) and not na(last_pivot_high_bar) and not na(prev_pivot_high_bar)
    if not na(resistance_line)
        line.delete(resistance_line)
    
    slope = (last_pivot_high - prev_pivot_high) / (last_pivot_high_bar - prev_pivot_high_bar)
    
    extend_bars = extend_lines ? 20 : 0
    end_price = last_pivot_high + slope * extend_bars
    
    resistance_line := line.new(
         x1=prev_pivot_high_bar, 
         y1=prev_pivot_high,
         x2=last_pivot_high_bar + extend_bars, 
         y2=end_price,
         color=slope < 0 ? bearish_color : resistance_color,
         style=get_line_style(),
         width=line_width,
         extend=extend_lines ? extend.right : extend.none
     )

// Draw support trendline
if not na(last_pivot_low) and not na(prev_pivot_low) and not na(last_pivot_low_bar) and not na(prev_pivot_low_bar)
    if not na(support_line)
        line.delete(support_line)
    
    slope = (last_pivot_low - prev_pivot_low) / (last_pivot_low_bar - prev_pivot_low_bar)
    
    extend_bars = extend_lines ? 20 : 0
    end_price = last_pivot_low + slope * extend_bars
    
    support_line := line.new(
         x1=prev_pivot_low_bar, 
         y1=prev_pivot_low,
         x2=last_pivot_low_bar + extend_bars, 
         y2=end_price,
         color=slope > 0 ? bullish_color : support_color,
         style=get_line_style(),
         width=line_width,
         extend=extend_lines ? extend.right : extend.none
     )

// Plot pivot points
plotshape(pivot_high, style=shape.triangledown, location=location.abovebar, color=resistance_color, size=size.tiny, title="Pivot High")
plotshape(pivot_low, style=shape.triangleup, location=location.belowbar, color=support_color, size=size.tiny, title="Pivot Low")

// Add labels if enabled
if show_labels and not na(pivot_high)
    label.new(bar_index - sr_length, pivot_high, "R: " + str.tostring(pivot_high, "#.##"), 
              style=label.style_label_down, color=resistance_color, textcolor=color.white, size=size.small)

if show_labels and not na(pivot_low)
    label.new(bar_index - sr_length, pivot_low, "S: " + str.tostring(pivot_low, "#.##"), 
              style=label.style_label_up, color=support_color, textcolor=color.white, size=size.small)

// Alerts for trend changes
alertcondition(not na(pivot_high), title="New Resistance Level", message="New resistance level detected")
alertcondition(not na(pivot_low), title="New Support Level", message="New support level detected")

```

---

# 2.

```
//@version=5
indicator("Trendlines & Support/Resistance", overlay=true, max_lines_count=100, max_labels_count=50)

// Input parameters
trendline_length = input.int(20, "Trendline Length", minval=5, maxval=100)
sr_length = input.int(10, "Support/Resistance Length", minval=5, maxval=50)
min_touches = input.int(2, "Minimum Touches for S/R", minval=2, maxval=5)
extend_lines = input.bool(true, "Extend Lines")
show_labels = input.bool(true, "Show Labels")

// Colors
bullish_color = input.color(color.green, "Bullish Trendline Color")
bearish_color = input.color(color.red, "Bearish Trendline Color")
support_color = input.color(color.blue, "Support Color")
resistance_color = input.color(color.orange, "Resistance Color")

// Line styles
line_style = input.string("Solid", "Line Style", options=["Solid", "Dashed", "Dotted"])
line_width = input.int(2, "Line Width", minval=1, maxval=5)

// Convert line style
get_line_style() =>
    switch line_style
        "Solid" => line.style_solid
        "Dashed" => line.style_dashed
        "Dotted" => line.style_dotted
        => line.style_solid

// Find pivot highs and lows
pivot_high = ta.pivothigh(high, sr_length, sr_length)
pivot_low = ta.pivotlow(low, sr_length, sr_length)

// Variables to store trendlines
var line support_line = na
var line resistance_line = na

// Variables for trendline calculation
var float last_pivot_high = na
var int last_pivot_high_bar = na
var float prev_pivot_high = na
var int prev_pivot_high_bar = na

var float last_pivot_low = na
var int last_pivot_low_bar = na
var float prev_pivot_low = na
var int prev_pivot_low_bar = na

// Update pivot high data
if not na(pivot_high)
    prev_pivot_high := last_pivot_high
    prev_pivot_high_bar := last_pivot_high_bar
    last_pivot_high := pivot_high
    last_pivot_high_bar := bar_index - sr_length

// Update pivot low data
if not na(pivot_low)
    prev_pivot_low := last_pivot_low
    prev_pivot_low_bar := last_pivot_low_bar
    last_pivot_low := pivot_low
    last_pivot_low_bar := bar_index - sr_length

// Draw resistance trendline
if not na(last_pivot_high) and not na(prev_pivot_high) and not na(last_pivot_high_bar) and not na(prev_pivot_high_bar)
    if not na(resistance_line)
        line.delete(resistance_line)
    
    // Calculate slope
    slope = (last_pivot_high - prev_pivot_high) / (last_pivot_high_bar - prev_pivot_high_bar)
    
    // Extend line
    extend_bars = extend_lines ? 20 : 0
    end_price = last_pivot_high + slope * extend_bars
    
    resistance_line := line.new(
         x1=prev_pivot_high_bar, 
         y1=prev_pivot_high,
         x2=last_pivot_high_bar + extend_bars, 
         y2=end_price,
         color=slope < 0 ? bearish_color : resistance_color,
         style=get_line_style(),
         width=line_width,
         extend=extend_lines ? extend.right : extend.none
     )

// Draw support trendline
if not na(last_pivot_low) and not na(prev_pivot_low) and not na(last_pivot_low_bar) and not na(prev_pivot_low_bar)
    if not na(support_line)
        line.delete(support_line)
    
    // Calculate slope
    slope = (last_pivot_low - prev_pivot_low) / (last_pivot_low_bar - prev_pivot_low_bar)
    
    // Extend line
    extend_bars = extend_lines ? 20 : 0
    end_price = last_pivot_low + slope * extend_bars
    
    support_line := line.new(
         x1=prev_pivot_low_bar, 
         y1=prev_pivot_low,
         x2=last_pivot_low_bar + extend_bars, 
         y2=end_price,
         color=slope > 0 ? bullish_color : support_color,
         style=get_line_style(),
         width=line_width,
         extend=extend_lines ? extend.right : extend.none
     )

// Horizontal Support and Resistance levels
var array<float> support_levels = array.new<float>()
var array<float> resistance_levels = array.new<float>()
var array<line> h_support_lines = array.new<line>()
var array<line> h_resistance_lines = array.new<line>()

// Add new support/resistance levels
if not na(pivot_high)
    array.push(resistance_levels, pivot_high)
    if array.size(resistance_levels) > 20
        array.shift(resistance_levels)

if not na(pivot_low)
    array.push(support_levels, pivot_low)
    if array.size(support_levels) > 20
        array.shift(support_levels)

// Function to find similar levels with array size check
find_similar_levels(levels, current_level, tolerance) =>
    count = 0
    if array.size(levels) > 0
        for i = 0 to array.size(levels) - 1
            if math.abs(array.get(levels, i) - current_level) <= tolerance
                count += 1
    count

// Function to clear old lines safely
clear_lines(line_array) =>
    if array.size(line_array) > 0
        for i = 0 to array.size(line_array) - 1
            line.delete(array.get(line_array, i))
        array.clear(line_array)

// Draw horizontal support lines
if bar_index % 20 == 0 and array.size(support_levels) > 0
    // Clear old support lines
    clear_lines(h_support_lines)
    
    // Find significant support levels
    tolerance = ta.atr(14) * 0.5
    processed = array.new<float>()
    
    for i = 0 to array.size(support_levels) - 1
        level = array.get(support_levels, i)
        already_processed = false
        
        // Check if already processed
        if array.size(processed) > 0
            for j = 0 to array.size(processed) - 1
                if math.abs(level - array.get(processed, j)) <= tolerance
                    already_processed := true
                    break
        
        if not already_processed
            touches = find_similar_levels(support_levels, level, tolerance)
            if touches >= min_touches and array.size(h_support_lines) < 5
                array.push(processed, level)
                support_line_h = line.new(
                     x1=bar_index - 100, 
                     y1=level,
                     x2=bar_index + (extend_lines ? 50 : 0), 
                     y2=level,
                     color=support_color,
                     style=line.style_dashed,
                     width=1,
                     extend=extend_lines ? extend.right : extend.none
                 )
                array.push(h_support_lines, support_line_h)

// Draw horizontal resistance lines
if bar_index % 20 == 0 and array.size(resistance_levels) > 0
    // Clear old resistance lines
    clear_lines(h_resistance_lines)
    
    // Find significant resistance levels
    tolerance = ta.atr(14) * 0.5
    processed = array.new<float>()
    
    for i = 0 to array.size(resistance_levels) - 1
        level = array.get(resistance_levels, i)
        already_processed = false
        
        // Check if already processed
        if array.size(processed) > 0
            for j = 0 to array.size(processed) - 1
                if math.abs(level - array.get(processed, j)) <= tolerance
                    already_processed := true
                    break
        
        if not already_processed
            touches = find_similar_levels(resistance_levels, level, tolerance)
            if touches >= min_touches and array.size(h_resistance_lines) < 5
                array.push(processed, level)
                resistance_line_h = line.new(
                     x1=bar_index - 100, 
                     y1=level,
                     x2=bar_index + (extend_lines ? 50 : 0), 
                     y2=level,
                     color=resistance_color,
                     style=line.style_dashed,
                     width=1,
                     extend=extend_lines ? extend.right : extend.none
                 )
                array.push(h_resistance_lines, resistance_line_h)

// Plot pivot points
plotshape(pivot_high, style=shape.triangledown, location=location.abovebar, color=resistance_color, size=size.tiny, title="Pivot High")
plotshape(pivot_low, style=shape.triangleup, location=location.belowbar, color=support_color, size=size.tiny, title="Pivot Low")

// Add labels if enabled
if show_labels and not na(pivot_high)
    label.new(bar_index - sr_length, pivot_high, "R: " + str.tostring(pivot_high, "#.##"), 
              style=label.style_label_down, color=resistance_color, textcolor=color.white, size=size.small)

if show_labels and not na(pivot_low)
    label.new(bar_index - sr_length, pivot_low, "S: " + str.tostring(pivot_low, "#.##"), 
              style=label.style_label_up, color=support_color, textcolor=color.white, size=size.small)

// Alerts
alertcondition(not na(pivot_high), title="New Resistance Level", message="New resistance level detected")
alertcondition(not na(pivot_low), title="New Support Level", message="New support level detected")

// Display current levels info
if barstate.islast and show_labels
    var table info_table = table.new(position.top_right, 2, 4, bgcolor=color.white, border_width=1, frame_width=1)
    table.cell(info_table, 0, 0, "Levels", text_color=color.black, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 0, "Price", text_color=color.black, bgcolor=color.gray, text_size=size.small)
    
    table.cell(info_table, 0, 1, "Last High", text_color=color.black, text_size=size.small)
    table.cell(info_table, 1, 1, not na(last_pivot_high) ? str.tostring(last_pivot_high, "#.##") : "N/A", text_color=color.red, text_size=size.small)
    
    table.cell(info_table, 0, 2, "Last Low", text_color=color.black, text_size=size.small)
    table.cell(info_table, 1, 2, not na(last_pivot_low) ? str.tostring(last_pivot_low, "#.##") : "N/A", text_color=color.blue, text_size=size.small)
    
    table.cell(info_table, 0, 3, "S/R Count", text_color=color.black, text_size=size.small)
    table.cell(info_table, 1, 3, str.tostring(array.size(h_support_lines)) + "/" + str.tostring(array.size(h_resistance_lines)), text_color=color.black, text_size=size.small)

```
