
```
streamlit cache clear

python -m venv venv                                                                                                                                                             
.\venv\Scripts\activate

python -m venv fresh_venv
.\fresh_venv\Scripts\activate
pip install pandas yfinance ta pandas-ta==0.3.14b0 numpy==1.26.4 streamlit plotly setuptools<81
streamlit run 1.py

.\venv\Scripts\activate
pip install --upgrade pandas yfinance ta pandas-ta numpy streamlit plotly setuptools<81

.\venv\Scripts\activate
pip install numpy==1.26.4
pip install --force-reinstall pandas-ta
pip install setuptools<81

pip install --force-reinstall pandas-ta
python -m pip install --upgrade pip==25.1.1
pip --version
pip list
pip check
```

```
pip install --upgrade altair attrs beautifulsoup4 blinker cachetools certifi cffi charset-normalizer click colorama curl_cffi frozendict gitdb GitPython idna Jinja2 jsonschema jsonschema-specifications MarkupSafe multitasking narwhals numpy packaging pandas pandas_ta peewee pillow pip platformdirs plotly protobuf pyarrow pycparser pydeck python-dateutil pytz referencing requests rpds-py six smmap soupsieve streamlit ta tenacity toml tornado typing_extensions tzdata urllib3 watchdog websockets yfinance
```

<hr>


## Python libraries install kiye hain** unka ek **backup export** 

---

## ✅ Step-by-Step: Python Libraries Backup & One-Click Restore

---

### 🔹 **Step 1: Installed Libraries List Export karo**

Run this command:

```bash
pip freeze > requirements_backup.txt
```

🔸 Ye command aapke system me jo bhi libraries installed hain unka version ke saath list bana dega:

📂 Example file (`requirements_backup.txt`):

```
numpy==1.24.0
pandas==1.5.2
flask==2.2.3
requests==2.31.0
...
```

---

### 🔹 **Step 2: File ko safe jagah rakh lo**

* Pendrive, GitHub, Google Drive, Email me send kar lo
* File ka naam `requirements_backup.txt` hi rehne do for easy restore

---

### 🔹 **Step 3: Future me (new laptop ya format ke baad) install karne ke liye**

Just run this one command:

```bash
pip install -r requirements_backup.txt
```

⚡ Ye command **saari libraries wapas install** kar dega exactly jaise pehle thi!

---

### ✅ Bonus Tip: Python Version bhi note rakh lo

```bash
python --version > python_version.txt
```

Future me same Python version use karna helpful hoga, specially compatibility ke liye.

---

## 🧠 Extra Idea: Auto Installer Script

Ek `.bat` ya `.sh` file bana lo (Windows/Linux ke liye) jisme ho:

```bash
pip install -r requirements_backup.txt
```

Isse aap **one double-click me sab install** kar sakte ho.

---

<hr>

## Made `.bat` file** bana dete hain — jisse aap **one double-click me pip libraries install** kar sako.

---

## ✅ Step-by-Step Setup for `.bat` Installer

### 🔹 Step 1: Backup File Banayein (Already done):

```bash
pip freeze > requirements_backup.txt
```

Is file ko kahin safe rakh lo (e.g., USB, Google Drive, same folder as `.bat` file)

---

### 🔹 Step 2: `.bat` File Create Karo

📄 Notepad open karo, aur ye content paste karo:

```bat
@echo off
echo ===============================
echo Installing Python Libraries...
echo ===============================

:: Check if requirements file exists
IF EXIST requirements_backup.txt (
    pip install -r requirements_backup.txt
    echo.
    echo ✅ All packages installed successfully.
) ELSE (
    echo ❌ requirements_backup.txt file not found!
)

pause
```

---

### 🔹 Step 3: File ko Save Karo

1. **File > Save As**
2. File name: `install_packages.bat`
3. Save as type: **All Files**
4. Encoding: ANSI
5. ✅ Keep it in the same folder as `requirements_backup.txt`

---

## ▶️ How to Use:

* Bas **double-click** karo `install_packages.bat` par
* Ye automatic `pip install -r requirements_backup.txt` run karega
* Console me status dikhayega

---

## ✅ BONUS Tips:

1. Agar aapka Python path system me properly set nahi hai, to `.bat` file me direct Python path bhi likh sakte ho:

```bat
C:\Users\<YourName>\AppData\Local\Programs\Python\Python39\Scripts\pip.exe install -r requirements_backup.txt
```

2. Aap is `.bat` ko pendrive ya Google Drive me bhi rakh sakte ho future ke liye.

---

