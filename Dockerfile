FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget curl software-properties-common gnupg2 \
    cabextract unzip xvfb x11-utils \
    && rm -rf /var/lib/apt/lists/*

# Add Wine repository
RUN dpkg --add-architecture i386 && \
    mkdir -pm755 /etc/apt/keyrings && \
    wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key && \
    wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/jammy/winehq-jammy.sources

# Install Wine
RUN apt-get update && apt-get install -y --install-recommends winehq-stable && \
    rm -rf /var/lib/apt/lists/*

# Set Wine environment
ENV WINEPREFIX=/wine
ENV WINEARCH=win64
ENV WINEDEBUG=-all
ENV DISPLAY=:99

RUN mkdir -p /wine

# Download Python for Windows
RUN wget -q https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe -O /tmp/python-installer.exe

WORKDIR /app

# Copy files
COPY app.py /app/
COPY requirements.txt /app/
COPY shapefiles/ /app/shapefiles/

RUN mkdir -p /app/dist /app/build

# Create build script in multiple steps to avoid encoding issues
RUN echo '#!/bin/bash' > /app/build_wine.sh
RUN echo 'set -e' >> /app/build_wine.sh
RUN echo 'echo "Starting build process..."' >> /app/build_wine.sh
RUN echo 'echo "Starting virtual display..."' >> /app/build_wine.sh
RUN echo 'Xvfb :99 -screen 0 1024x768x16 > /dev/null 2>&1 &' >> /app/build_wine.sh
RUN echo 'XVFB_PID=$!' >> /app/build_wine.sh
RUN echo 'sleep 3' >> /app/build_wine.sh
RUN echo 'echo "Initializing Wine..."' >> /app/build_wine.sh
RUN echo 'wineboot -u' >> /app/build_wine.sh
RUN echo 'sleep 5' >> /app/build_wine.sh
RUN echo 'echo "Installing Python 3.10 for Windows..."' >> /app/build_wine.sh
RUN echo 'wine /tmp/python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_pip=1 Include_tcltk=0' >> /app/build_wine.sh
RUN echo 'sleep 20' >> /app/build_wine.sh
RUN echo 'echo "Installing PyInstaller..."' >> /app/build_wine.sh
RUN echo 'wine python -m pip install --upgrade pip --quiet' >> /app/build_wine.sh
RUN echo 'wine python -m pip install pyinstaller==6.3.0 --quiet' >> /app/build_wine.sh
RUN echo 'echo "Installing dependencies..."' >> /app/build_wine.sh
RUN echo 'wine python -m pip install streamlit==1.28.1 pandas==2.0.3 numpy==1.24.3 plotly==5.17.0 --quiet' >> /app/build_wine.sh
RUN echo 'wine python -m pip install shapely==2.0.1 pyproj==3.6.0 geopandas==0.13.2 fiona==1.9.4 --quiet' >> /app/build_wine.sh
RUN echo 'wine python -m pip install scipy==1.11.2 matplotlib==3.7.3 scikit-learn==1.3.1 --quiet' >> /app/build_wine.sh
RUN echo 'wine python -m pip install openpyxl==3.1.2 xlrd==2.0.1 altair tornado --quiet' >> /app/build_wine.sh

# Add spec file creation to script
RUN cat >> /app/build_wine.sh << 'SPECEND'
echo "Creating spec file..."
cat > /app/SalesDashboard.spec << 'SPECFILE'
import os
block_cipher = None
icon_file = 'app_icon.ico' if os.path.exists('app_icon.ico') else None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('shapefiles', 'shapefiles')],
    hiddenimports=[
        'streamlit', 'streamlit.runtime', 'streamlit.runtime.scriptrunner',
        'pandas', 'geopandas', 'shapely', 'shapely.geometry',
        'fiona', 'fiona.crs', 'fiona.schema', 'pyproj',
        'plotly', 'plotly.graph_objs', 'numpy', 'PIL',
        'tornado', 'altair', 'scipy', 'matplotlib', 'sklearn',
        'openpyxl', 'xlrd'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

try:
    import streamlit
    a.datas += Tree(streamlit.__path__[0], prefix='streamlit', excludes=['*.pyc'])
except:
    pass

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='SalesDashboard',
    debug=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,
    icon=icon_file,
)
SPECFILE

echo "Building executable..."
wine python -m PyInstaller --clean --noconfirm SalesDashboard.spec

if [ -f "/app/dist/SalesDashboard.exe" ]; then
    echo "Build completed successfully!"
    ls -lh /app/dist/SalesDashboard.exe
else
    echo "Build failed!"
    exit 1
fi

kill $XVFB_PID 2>/dev/null || true
SPECEND

RUN chmod +x /app/build_wine.sh

CMD ["/bin/bash", "/app/build_wine.sh"]