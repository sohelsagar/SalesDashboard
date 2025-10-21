"""
Launcher script for SalesDashboard
This will be bundled with the executable to properly launch Streamlit
"""
import sys
import os
import subprocess
import webbrowser
import time
from threading import Timer

def open_browser(port=8501):
    """Open browser after a short delay"""
    webbrowser.open(f'http://localhost:{port}')

def main():
    # Get the base path (works for both PyInstaller and normal Python)
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Set environment variables
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Path to the main app
    app_path = os.path.join(base_path, 'app.py')
    
    print("Starting SalesDashboard...")
    print(f"Base path: {base_path}")
    print(f"App path: {app_path}")
    
    # Open browser after 3 seconds
    Timer(3.0, open_browser).start()
    
    # Run Streamlit
    try:
        subprocess.run([
            sys.executable,
            '-m', 'streamlit', 'run',
            app_path,
            '--server.port=8501',
            '--server.address=localhost',
            '--server.headless=true',
            '--browser.serverAddress=localhost',
            '--browser.gatherUsageStats=false'
        ])
    except KeyboardInterrupt:
        print("\nShutting down SalesDashboard...")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()