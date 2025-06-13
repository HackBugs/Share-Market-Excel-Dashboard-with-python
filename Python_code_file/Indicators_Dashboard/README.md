
```
Run - python stock_dashboard.py
# On Windows
.\venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### Stock Dashboard Documentation

This project is a **Professional Stock Dashboard** built using Python, Flask, and JavaScript. It allows users to analyze stock data for Indian companies listed on the National Stock Exchange (NSE) by fetching real-time data using the `yfinance` library, calculating technical indicators with the `ta` library, and presenting the results in an interactive web interface.

---

#### **Features**
- **Company Selection**: Choose from a list of NSE companies loaded from a CSV file.
- **Technical Indicators**: Supports a wide range of indicators (e.g., EMA, RSI, MACD, Bollinger Bands) across multiple timeframes (5min, 15min, 1d, etc.).
- **Stock Details**: Displays detailed stock information, including current price, VWAP, 52-week high/low, and more.
- **Profit & Loss Calculator**: Calculate P&L based on buy price, quantity, and current price.
- **Strategy Report**: Generates a detailed analysis report based on selected indicators and timeframes.
- **Responsive UI**: Built with Tailwind CSS for a modern, user-friendly interface.

---

#### **Prerequisites**

Before running the project, ensure the following are installed on the system:

1. **Python 3.8 or higher**:
   - Download and install Python from [python.org](https://www.python.org/downloads/).
   - Verify installation: `python --version`

2. **pip** (Python package manager):
   - Usually bundled with Python. Verify with: `pip --version`
   - If not installed, follow [pip installation instructions](https://pip.pypa.io/en/stable/installation/).

3. **Git** (optional, for cloning the project if shared via a repository):
   - Install Git from [git-scm.com](https://git-scm.com/downloads).
   - Verify: `git --version`

4. **A Web Browser** (e.g., Chrome, Firefox) to access the dashboard.

---

#### **Required Libraries**

The project depends on the following Python libraries. Install them using pip:

- `yfinance`: Fetches stock data from Yahoo Finance.
- `ta`: Calculates technical indicators.
- `flask`: Web framework to serve the dashboard.
- `waitress`: Production WSGI server to run the Flask app.
- `pandas`: Handles data manipulation (e.g., loading the CSV file).
- `numpy`: Handles numerical operations and checks for `NaN` values.

**Install all required libraries** by running the following command in your terminal or command prompt:

```bash
pip install yfinance ta flask waitress pandas numpy
```

Verify the installations:

```bash
pip show yfinance
pip show ta
pip show flask
pip show waitress
pip show pandas
pip show numpy
```

---

#### **Project Structure**

Ensure your project directory is structured as follows:

```
stock_dashboard/
│
├── stock_dashboard.py       # Main Flask application script
├── templates/
│   └── index.html           # HTML template for the dashboard
└── EQUITY_L.csv             # CSV file containing NSE company names and symbols
```

- **`stock_dashboard.py`**: The backend script that fetches stock data, calculates indicators, and serves the web interface.
- **`templates/index.html`**: The frontend template for the dashboard UI.
- **`EQUITY_L.csv`**: A CSV file with columns `NAME OF COMPANY` and `SYMBOL` (e.g., `Adani Enterprises,ADANIENSOL`). This file must be placed at the path specified in the script (default: `E:\Coding\Attandance\Stock sheet\EQUITY_L.csv`).

**Example `EQUITY_L.csv`**:
```
NAME OF COMPANY,SYMBOL
Adani Enterprises,ADANIENSOL
Reliance Industries,RELIANCE
Tata Motors,TATAMOTORS
```

---

#### **Setup Instructions**

1. **Prepare the CSV File**:
   - Ensure you have a file named `EQUITY_L.csv` with NSE company names and symbols.
   - Place it at the path `E:\Coding\Attandance\Stock sheet\EQUITY_L.csv`.
   - If your file is in a different location, update the `csv_path` variable in `stock_dashboard.py`:
     ```python
     csv_path = r"path\to\your\EQUITY_L.csv"
     ```

2. **Download the Code**:
   - If you’re sharing the code as files, provide `stock_dashboard.py` and `templates/index.html`.
   - Alternatively, host the code in a Git repository and share the repository URL. The recipient can clone it using:
     ```bash
     git clone <repository-url>
     cd stock_dashboard
     ```

3. **Set Up the Project Directory**:
   - Ensure the project structure matches the one described above.
   - Place `stock_dashboard.py` in the root directory.
   - Place `index.html` inside a `templates` folder.

4. **Install Dependencies**:
   - Open a terminal in the project directory.
   - Run the pip command to install required libraries (as shown in the "Required Libraries" section).

---

#### **Running the Dashboard**

1. **Start the Server**:
   - In the terminal, navigate to the project directory.
   - Run the following command to start the Flask server:
     ```bash
     python stock_dashboard.py
     ```
   - You should see output like:
     ```
     * Serving Flask app 'stock_dashboard'
     * Debug mode: off
     INFO:waitress:Serving on http://127.0.0.1:5000
     ```

2. **Access the Dashboard**:
   - Open a web browser and go to: `http://127.0.0.1:5000/`
   - The dashboard should load, displaying a dropdown to select a company and options to add indicators.

3. **Using the Dashboard**:
   - **Select a Company**: Choose a company from the dropdown (loaded from `EQUITY_L.csv`).
   - **Add Indicators**: Search and add technical indicators (e.g., EMA9, RSI) to analyze.
   - **Fetch Data**: Click the "Fetch Data" button to load stock details and indicator values.
   - **View Details**: Explore stock price details, trade information, and securities info.
   - **Calculate P&L**: Enter a buy price and quantity to calculate profit/loss.
   - **View Strategy Report**: Click "View Strategy" to see a detailed analysis report.
   - **Download Report**: Click "Download Report" to save the strategy report as a text file.

---

#### **Troubleshooting**

1. **Server Doesn’t Start**:
   - Ensure all dependencies are installed (`pip install yfinance ta flask waitress pandas numpy`).
   - Check for errors in the terminal. Common issues:
     - `ModuleNotFoundError`: A library is missing. Install it using pip.
     - `FileNotFoundError`: The `EQUITY_L.csv` file is not found. Verify the `csv_path` in `stock_dashboard.py`.

2. **Dashboard Loads but Fails to Fetch Data**:
   - Check the browser console (F12 → Console) for errors.
   - Check the terminal for server logs. Common issues:
     - **Invalid Symbol**: The stock symbol in `EQUITY_L.csv` might be incorrect. Verify symbols on Yahoo Finance (e.g., `ADANIENSOL.NS`).
     - **Market Hours**: The NSE operates from 9:15 AM to 3:30 PM IST, Monday to Friday. Outside these hours, intraday data may be unavailable. The code falls back to daily data, but some indicators may show `N/A`.
     - **Network Issues**: Ensure you have an active internet connection, as `yfinance` fetches data online.

3. **Indicators Show `N/A`**:
   - This can happen if `yfinance` returns incomplete data (e.g., low trading volume, market closed).
   - Test with a widely traded stock like `RELIANCE.NS` to confirm functionality.

---

#### **Additional Notes**

- **Market Hours**: The dashboard fetches data using `yfinance`, which may return limited data outside NSE trading hours (9:15 AM to 3:30 PM IST, Monday to Friday). The code includes fallbacks to daily data, but some intraday timeframes (e.g., 5min) may not work outside market hours.
- **Performance**: For large CSV files or many indicators, the dashboard may take a few seconds to load data. The loading bar in the UI indicates progress.
- **Customization**:
  - Add more indicators by extending the `INDICATORS` list and `fetch_indicator_data()` function in `stock_dashboard.py`.
  - Modify `TIMEFRAMES` to support additional timeframes (e.g., `1mo` for monthly data).

---

#### **Sharing the Code**

If you’re sharing the code with someone:
- Provide the `stock_dashboard.py` and `templates/index.html` files.
- Include a copy of your `EQUITY_L.csv` file or instructions to create one.
- Share this documentation to help them get started.

If you’re hosting the code in a Git repository:
- Create a repository with the project structure.
- Include a `README.md` with the above instructions.
- Share the repository URL with the recipient.

---
