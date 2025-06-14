import streamlit as st
import os
import glob
import subprocess
import time
from pathlib import Path
import psutil
import streamlit.components.v1 as components
import requests

# Set page configuration for the master dashboard
st.set_page_config(page_title="Master Stock Dashboard", layout="wide")

# Directory where dashboard files are stored
DASHBOARD_DIR = "dashboards"

# Ensure the dashboards directory exists
if not os.path.exists(DASHBOARD_DIR):
    os.makedirs(DASHBOARD_DIR)

# Base port for running dashboards (using 8600 to avoid conflicts)
BASE_PORT = 8600
# Dictionary to store running processes
running_processes = {}

# Function to discover all .py files in the dashboard directory
def get_dashboard_files():
    return glob.glob(f"{DASHBOARD_DIR}/*.py")

# Function to check if a port is in use
def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Function to check if a dashboard is ready
def is_dashboard_ready(url, timeout=15):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            time.sleep(1)
    return False

# Function to start a Streamlit dashboard on a specific port
def start_dashboard(file_path, port):
    # Check if already running
    if port in running_processes and running_processes[port].poll() is None:
        return True
    # Check if port is in use
    if is_port_in_use(port):
        st.error(f"Port {port} is in use. Open Command Prompt as Administrator and run: 'netstat -aon | find \":{port}\"', then 'taskkill /PID <pid> /F'. Or, change BASE_PORT in this script.")
        return False
    # Start the dashboard as a subprocess
    try:
        process = subprocess.Popen(
            ["streamlit", "run", file_path, "--server.port", str(port), "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        # Wait to ensure the server starts
        time.sleep(5)
        # Check if the process is still running
        if process.poll() is not None:
            stderr = process.stderr.read()
            st.error(f"Failed to start dashboard {file_path} on port {port}: {stderr}")
            return False
        running_processes[port] = process
        # Verify the dashboard is ready
        iframe_url = f"http://localhost:{port}"
        if not is_dashboard_ready(iframe_url):
            st.error(f"Dashboard at {iframe_url} is not responding. Check the dashboard code or increase 'time.sleep(5)' to 'time.sleep(10)' in 'start_dashboard'.")
            stop_dashboard(port)
            return False
        return True
    except Exception as e:
        st.error(f"Error starting dashboard {file_path} on port {port}: {str(e)}")
        return False

# Function to stop a specific dashboard
def stop_dashboard(port):
    if port in running_processes:
        try:
            process = running_processes[port]
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            running_processes.pop(port)
        except psutil.NoSuchProcess:
            running_processes.pop(port, None)

# Function to stop all running dashboards
def stop_all_dashboards():
    for port in list(running_processes.keys()):
        stop_dashboard(port)

# Stop all dashboards on startup to avoid conflicts
stop_all_dashboards()

# Main app
def main():
    st.title("Master Stock Dashboard")
    st.write("Select a dashboard to view (e.g., final, indicators):")

    # Get list of dashboard files
    dashboard_files = get_dashboard_files()

    if not dashboard_files:
        st.error(f"No dashboard files found in the '{DASHBOARD_DIR}' directory. Please add files like 'final.py' or 'indicators.py'.")
        return

    # Create a dropdown to select a dashboard
    dashboard_names = [Path(f).stem for f in dashboard_files]
    selected_dashboard = st.selectbox("Choose a Dashboard", dashboard_names)

    # Display the selected dashboard
    if selected_dashboard:
        st.subheader(f"Running {selected_dashboard}")
        dashboard_path = os.path.join(DASHBOARD_DIR, f"{selected_dashboard}.py")
        port = BASE_PORT + dashboard_names.index(selected_dashboard)

        # Stop other dashboards to save resources
        for p in list(running_processes.keys()):
            if p != port:
                stop_dashboard(p)

        # Start and embed the selected dashboard
        if start_dashboard(dashboard_path, port):
            iframe_url = f"http://localhost:{port}"
            components.iframe(iframe_url, height=800, scrolling=True)
        else:
            st.write("Please check the error above and ensure the dashboard file is a valid Streamlit app.")

    # Button to stop all dashboards
    if st.button("Stop All Dashboards"):
        stop_all_dashboards()
        st.success("All dashboards stopped.")

if __name__ == "__main__":
    try:
        main()
    finally:
        stop_all_dashboards()