# Pre-Build Checklist for Sales Dashboard EXE

Before running the build, verify all these items are in place.

## System Requirements

- [ ] Docker Desktop installed and running
- [ ] At least 10 GB free disk space
- [ ] Windows 10/11 or Linux with Docker
- [ ] Internet connection (for downloading dependencies)

## Project Files

Create this directory structure:

```
SalesDashboard/
├── app.py
├── Dockerfile
├── requirements.txt
├── build_windows_exe.bat
├── shapefiles/
│   ├── adm01.shp
│   ├── adm01.shx
│   ├── adm01.dbf
│   ├── adm01.prj
│   ├── adm01.sbn
│   ├── adm01.sbx
│   ├── adm01.cpg
│   ├── adm01.json
│   └── adm01.xml
```

## Checklist

### Files to Include

- [ ] **app.py** - Main application code
  - Contains Streamlit dashboard
  - Handles CSV uploads
  - Converts Month numbers to names
  - Creates geographic maps
  
- [ ] **Dockerfile** - Docker build configuration
  - Sets up build environment
  - Installs all dependencies
  - Runs PyInstaller
  
- [ ] **requirements.txt** - Python dependencies
  - All pip packages listed
  - Specific versions pinned
  
- [ ] **build_windows_exe.bat** - Windows build script
  - Runs Docker build
  - Generates EXE file

### Shapefile Files (All Required)

- [ ] **adm01.shp** - Shapefile geometry
- [ ] **adm01.shx** - Shapefile index
- [ ] **adm01.dbf** - Attribute database
- [ ] **adm01.prj** - Projection information
- [ ] **adm01.sbn** - Spatial index
- [ ] **adm01.sbx** - Spatial index
- [ ] **adm01.cpg** - Code page
- [ ] **adm01.json** - Optional GeoJSON version
- [ ] **adm01.xml** - Optional metadata

### CSV Data Format

Your test CSV should have these columns:

- [ ] **Amount_(BDT)** - Numeric (sales amount)
- [ ] **Qty_(Pcs)** - Numeric (quantity pieces)
- [ ] **Qty_(KG)** - Numeric (quantity kilograms)
- [ ] **Year** - Numeric (e.g., 2023)
- [ ] **Month** - Numeric 1-12 (1=January, 12=December)
- [ ] **Brand** - Text (optional)
- [ ] **DivName** - Text (optional)
- [ ] **AdmDiv** - Text matching shapefile divisions (optional, for maps)

Example valid Month values:
- [ ] 1 = January
- [ ] 2 = February
- [ ] 3 = March
- [ ] 4 = April
- [ ] 5 = May
- [ ] 6 = June
- [ ] 7 = July
- [ ] 8 = August
- [ ] 9 = September
- [ ] 10 = October
- [ ] 11 = November
- [ ] 12 = December

## Build Steps

1. [ ] Navigate to project folder in Command Prompt
2. [ ] Verify Docker is running (`docker --version`)
3. [ ] Run `build_windows_exe.bat`
4. [ ] Wait 20-40 minutes for build to complete
5. [ ] Check `dist/` folder for `SalesDashboard.exe`

## Testing After Build

1. [ ] Double-click `SalesDashboard.exe`
2. [ ] Wait for browser window to open (first run takes 10-15 seconds)
3. [ ] Upload a test CSV file
4. [ ] Verify data loads correctly
5. [ ] Check if months display as names (January, February, etc.)
6. [ ] Test generating a map
7. [ ] Test downloading data

## Distribution

1. [ ] Copy only `SalesDashboard.exe` to target machines
2. [ ] No additional files needed
3. [ ] No Python installation required on target machines
4. [ ] Users just double-click the EXE

## Troubleshooting

If build fails:

1. [ ] Check Docker is running
2. [ ] Verify all files are in correct locations
3. [ ] Delete `dist/` folder and retry
4. [ ] Run `docker system prune` to free space
5. [ ] Check available disk space (need 10GB+)

If EXE doesn't run:

1. [ ] Check Windows Defender/Antivirus not blocking it
2. [ ] Run from Command Prompt to see error messages
3. [ ] Verify shapefile files are present in folder
4. [ ] Check Windows 10/11 is fully updated

If CSV upload fails:

1. [ ] Verify CSV is comma-separated
2. [ ] Check column names match exactly
3. [ ] Ensure Month column has numeric values 1-12
4. [ ] Test with smaller CSV first (< 10,000 rows)

## File Size Expectations

- `SalesDashboard.exe` size: 400-600 MB
- Installation size when run: 1-1.5 GB
- Runtime memory usage: 500MB-1GB
- Typical CSV data: Size depends on records

## Additional Notes

- First run will be slower (extracting bundled files)
- Subsequent runs will be faster
- Temporary files stored in Windows %TEMP% folder
- Application uses port 8501 for web interface
- Multiple EXE instances can't run on same port

Ready to build? Run: `build_windows_exe.bat`
