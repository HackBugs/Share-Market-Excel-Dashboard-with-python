
> # All companies tickers
1. NSE (National Stock Exchange):
- [csv_file](https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv)

3. BSE (Bombay Stock Exchange):

> # Here are the links to sources where you can obtain ticker data for all companies listed on the National Stock Exchange (NSE) and Bombay Stock Exchange (BSE):

### Official Exchange Websites
1. **NSE (National Stock Exchange)**
   - **Link:** [https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv](https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv)
   - **Description:** Direct download link for the CSV file containing ticker symbols and company names for ~2,671 NSE-listed companies.[](https://medium.com/%40arunes007/extract-all-listed-companies-in-indian-stock-market-nse-bse-688b525f3d20)
   - **Alternative Navigation:** [www.nseindia.com](https://www.nseindia.com) > Products > Equities > Securities Available for Trading

2. **BSE (Bombay Stock Exchange)**
   - **Link:** [https://www.bseindia.com/corporates/ListedCorp.aspx](https://www.bseindia.com/corporates/ListedCorp.aspx)
   - **Description:** Web page to access the list of ~5,000 BSE-listed companies. Select "Equity" and "Active" status, submit the form, and download the CSV. Automation may require tools like Selenium.[](https://www.bseindia.com/corporates/List_Scrips.html)
   - **Note:** No direct CSV link is available; manual download or automation is needed.

### Financial Data Platforms
3. **Screener.in**
   - **Link:** [https://www.screener.in/](https://www.screener.in/)
   - **Description:** Browse NSE/BSE company lists. Exporting full ticker data requires a paid subscription. Manual scraping may be possible with permission.[](https://medium.com/%40arunes007/extract-all-listed-companies-in-indian-stock-market-nse-bse-688b525f3d20)

4. **ETMoney.com**
   - **Link:** [https://www.etmoney.com/stocks](https://www.etmoney.com/stocks)
   - **Description:** A-to-Z stock list with share price and market cap. Manual extraction or scraping may be needed for complete ticker data.[](https://www.etmoney.com/stocks/list-of-stocks)

5. **Ticker.Finology.in**
   - **Link:** [https://ticker.finology.in/](https://ticker.finology.in/)
   - **Description:** Directory of NSE/BSE-listed companies. Check terms for scraping or automation limits.[](https://ticker.finology.in/company)

6. **Moneycontrol.com**
   - **Link:** [https://www.moneycontrol.com/india/stockpricequote/](https://www.moneycontrol.com/india/stockpricequote/)
   - **Description:** Lists companies with tickers. Manual browsing or scraping may be required for bulk data.[](https://www.moneycontrol.com/india/stockpricequote/miscellaneous/bselimited/B08)

7. **TrueData.in (Paid)**
   - **Link:** [https://www.truedata.in/](https://www.truedata.in/)
   - **Description:** Authorized real-time data vendor for NSE/BSE. Provides ticker lists via APIs. Contact [sales@truedata.in](mailto:sales@truedata.in) for pricing.[](https://www.truedata.in/)

8. **GlobalDataFeeds.in (Paid)**
   - **Link:** [https://www.globaldatafeeds.in/](https://www.globaldatafeeds.in/)
   - **Description:** Authorized vendor for NSE/BSE data, including ticker lists. Pricing available on request.[](https://www.truedata.in/)

9. **TickData.com (Paid)**
   - **Link:** [https://www.tickdata.com/](https://www.tickdata.com/)
   - **Description:** Historical data for NSE equities since 2012, including ticker mappings. Contact [sales@tickdata.com](mailto:sales@tickdata.com) for licensing.[](https://www.tickdata.com/equity-data/national-stock-exchange-of-india)

10. **5Paisa.com**
    - **Link:** [https://www.5paisa.com/stocks](https://www.5paisa.com/stocks)
    - **Description:** Alphabetical list of NSE/BSE companies. API access may require a subscription.[](https://www.5paisa.com/stocks/all)

11. **Dhan.co**
    - **Link:** [https://dhan.co/stocks/](https://dhan.co/stocks/)
    - **Description:** Share price list with A-to-Z filter for NSE/BSE companies. API access may be subscription-based.[](https://dhan.co/all-stocks-list/)

### Additional Resources
12. **Medium Article by Arunesh Kumar Singh**
    - **Link:** [https://medium.com/@aruneshsingh/extract-all-listed-companies-in-indian-stock-market-nse-bse-9b7b8f7b8e3c](https://medium.com/@aruneshsingh/extract-all-listed-companies-in-indian-stock-market-nse-bse-9b7b8f7b8e3c)
    - **Description:** Guide to fetch and merge NSE/BSE ticker lists using Python, resulting in ~4,385 unique securities. Includes sample code for automation.[](https://medium.com/%40arunes007/extract-all-listed-companies-in-indian-stock-market-nse-bse-688b525f3d20)

### Notes
- **NSE Data:** The `EQUITY_L.csv` file is the most straightforward source for NSE tickers. Use the provided Python script for automation.
- **BSE Data:** Requires form interaction for download. Use Selenium/Splinter for automation, as outlined in the Medium article.
- **Paid Vendors:** TrueData, GlobalDatafeeds, and TickData offer reliable, real-time, or historical data with ticker lists, ideal for professional applications.
- **Legal Compliance:** Verify terms of use for scraping or redistributing data from these sources to avoid violations.
- **Dynamic Updates:** Schedule regular downloads (e.g., weekly) to capture new listings or delistings.

<hr>

## CMD FOR 
streamlit run app-6.py

[visual-cpp-build-tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) - Download

```
pip install -r requirements.txt
```

```
pip install streamlit
pip install streamlit yfinance pandas numpy plotly ta seaborn matplotlib
pip install yfinance streamlit pandas numpy plotly ta seaborn matplotlib
```

```
cd E:\Coding\Attandance\Stock sheet
pip install --upgrade streamlit yfinance pandas numpy plotly ta seaborn matplotlib
```

```
python -m venv venv
.\venv\Scripts\activate
pip install streamlit yfinance pandas numpy plotly ta seaborn matplotlib
streamlit run app-5.py
```

```
py -3.12 -m venv venv
.\venv\Scripts\activate
pip install streamlit yfinance pandas numpy plotly ta seaborn matplotlib
```

## Install These Dependencies

```
pip install pandas
pip install nsepy
pip install yfinance
pip install plotly
pip install dash
pip install dash-bootstrap-components
pip install openpyxl
pip install ta
pip show streamlit
pip install --upgrade streamlit

pip install streamlit yfinance pandas numpy plotly ta
pip install curl_cffi
pip install curl_cffi --only-binary :all:
pip install requests
python --version
```

```
pip install --upgrade streamlit yfinance pandas numpy plotly ta
pip install streamlit yfinance pandas numpy plotly ta seaborn matplotlib
pip install streamlit==1.38.0
pip cache purge
```

## For running the program

```
python app.py
streamlit run app.py
python -m streamlit run app-5.py
```

# Excel-Dashboard-with-python

## This script is a Python program that generates a shift schedule for a team of 5 people from April to December. It creates an Excel file with the schedule. To run this script, you'll need to install several Python packages.

Here's what you need to install and how to do it:

1. First, make sure you have Python installed on your system. The script uses Python's standard libraries and some additional packages.
2. Install the required packages using pip:

```
pip install pandas
```

```
pip install openpyxl
```

## The script uses:

- **calendar** (built-in Python module, no installation needed)
- **pandas** (for data manipulation and creating DataFrames)
- **datetime** (built-in Python module, no installation needed)
- **openpyxl** (for Excel file operations)

## After installing these packages, you should be able to run the script without any errors. The script will:

1. Generate a shift schedule for each day from April to December
2. Rotate team members to ensure fair distribution of shifts
3. Create an Excel file named "shift_schedule_April_December.xlsx" with the schedule

## To run the script, save it as a .py file (e.g., "shift_scheduler.py") and execute it using Python:

```
python shift_scheduler.py
```

