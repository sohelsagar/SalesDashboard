import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
import os
import sys
import geopandas as gpd
import json
from pathlib import Path
import io

warnings.filterwarnings('ignore')

# Get the application's base directory
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SHAPEFILE_FOLDER = os.path.join(BASE_DIR, 'shapefiles')
SHAPEFILE_NAME = "adm01.shp"

# Configure Streamlit page
st.set_page_config(
    page_title="Sales Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .section-header {
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: bold;
        margin: 2rem 0 1rem 0;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


class SalesDashboard:
    def __init__(self):
        self.df = None
        self.gdf = None
        self.variables = None
        self.parameters = None
        self.trend_params = None
        self.all_mat_periods = None
        
    def load_shapefile(self):
        """Load Bangladesh shapefile for geospatial visualization"""
        try:
            shapefile_path = os.path.join(SHAPEFILE_FOLDER, SHAPEFILE_NAME)
            
            if not os.path.exists(shapefile_path):
                st.warning(f"Shapefile not found at: {shapefile_path}")
                return None
            
            gdf = gpd.read_file(shapefile_path)
            
            possible_name_cols = ['ADM1_EN', 'NAME_1', 'DIVISION', 'DIV_NAME', 'name', 'Name', 'NAME']
            
            name_col = None
            for col in possible_name_cols:
                if col in gdf.columns:
                    name_col = col
                    break
            
            if name_col:
                gdf = gdf.rename(columns={name_col: 'AdmDiv'})
            else:
                non_geom_cols = [col for col in gdf.columns if col != 'geometry']
                if non_geom_cols:
                    gdf = gdf.rename(columns={non_geom_cols[0]: 'AdmDiv'})
            
            if gdf.crs != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')
            
            if 'AdmDiv' in gdf.columns:
                gdf['AdmDiv'] = gdf['AdmDiv'].str.strip().str.title()
            
            return gdf
            
        except Exception as e:
            st.error(f"Error loading shapefile: {str(e)}")
            return None
    
    def load_data_from_upload(self, uploaded_file):
        """Load data from uploaded CSV file"""
        try:
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(uploaded_file, delimiter=',', encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                st.error("Could not read file with any of the supported encodings")
                return None
            
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            
            # Identify numeric columns and convert them
            numeric_cols = ['Qty_(Pcs)', 'Qty_(KG)', 'Amount_(BDT)']
            existing_numeric_cols = [col for col in numeric_cols if col in df.columns]
            
            for col in existing_numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Convert non-numeric columns to string
            non_numeric_cols = [col for col in df.columns if col not in existing_numeric_cols]
            for col in non_numeric_cols:
                df[col] = df[col].astype(str).fillna('Unknown')
            
            # Clean AdmDiv column if it exists
            if 'AdmDiv' in df.columns:
                df['AdmDiv'] = df['AdmDiv'].str.strip().str.title()
            
            # Convert Month from numeric to month name if needed
            if 'Month' in df.columns:
                df['Month'] = pd.to_numeric(df['Month'], errors='coerce').astype('Int64')
                df['MonthName'] = df['Month'].apply(self.month_number_to_name)
            
            # Create derived time columns
            if 'Year' in df.columns and 'Month' in df.columns:
                df['YearMonth'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
            
            if 'Year' in df.columns and 'Quarter' in df.columns:
                df['YearQuarter'] = df['Year'].astype(str) + '-Q' + df['Quarter'].astype(str)
            
            # Memory optimization
            for col in df.select_dtypes(include=['object']).columns:
                num_unique = len(df[col].unique())
                if num_unique / len(df) < 0.5:
                    df[col] = df[col].astype('category')
            
            return df
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return None
    
    def initialize_data(self, df):
        """Initialize dashboard with loaded data"""
        self.df = df
        self.variables = ['Qty_(Pcs)', 'Qty_(KG)', 'Amount_(BDT)']
        self.variables = [v for v in self.variables if v in df.columns]
        
        excluded_params = ['DivisionName', 'DepotName', 'DistributorName', 'MonthName']
        self.parameters = [col for col in df.columns 
                          if col not in self.variables and col not in excluded_params]
        
        self.trend_params = [col for col in self.parameters 
                            if col not in ['DivisionName', 'DepotName', 'DistributorName']]
        
        self.all_mat_periods = self.calculate_all_mat_periods()
        
        # Load shapefile
        self.gdf = self.load_shapefile()
    
    @staticmethod
    def month_number_to_name(month_num):
        """Convert numeric month (1-12) to month name"""
        if pd.isna(month_num):
            return 'Unknown'
        
        try:
            month_num = int(month_num)
            month_names = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }
            return month_names.get(month_num, 'Unknown')
        except:
            return 'Unknown'
    
    @staticmethod
    def month_name_to_number(month_name):
        """Convert month name to number"""
        month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        if pd.isna(month_name):
            return np.nan
        
        month_str = str(month_name).strip().lower()
        
        if month_str in month_names:
            return month_names[month_str]
        
        try:
            return int(month_str)
        except:
            return np.nan
    
    def calculate_all_mat_periods(self):
        """Calculate all possible MAT periods from the data"""
        if self.df is None or 'Month' not in self.df.columns or 'Year' not in self.df.columns:
            return []
        
        try:
            work_df = self.df.copy()
            
            work_df['Month_num'] = pd.to_numeric(work_df['Month'], errors='coerce')
            work_df['Year_num'] = pd.to_numeric(work_df['Year'], errors='coerce')
            
            work_df = work_df.dropna(subset=['Year_num', 'Month_num'])
            
            if work_df.empty:
                return []
            
            work_df['YearMonth_num'] = work_df['Year_num'] * 100 + work_df['Month_num']
            
            earliest_ym = work_df['YearMonth_num'].min()
            latest_ym = work_df['YearMonth_num'].max()
            
            earliest_year = int(earliest_ym // 100)
            earliest_month = int(earliest_ym % 100)
            latest_year = int(latest_ym // 100)
            latest_month = int(latest_ym % 100)
            
            month_names = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
                          7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'}
            
            all_mat_periods = []
            current_year = latest_year
            current_month = latest_month
            mat_count = 0
            
            while (current_year > earliest_year or 
                  (current_year == earliest_year and current_month >= earliest_month)) and mat_count < 24:
                
                mat_months = []
                mat_year = current_year
                mat_month = current_month
                
                for i in range(12):
                    mat_months.append((mat_year, mat_month))
                    mat_month -= 1
                    if mat_month == 0:
                        mat_month = 12
                        mat_year -= 1
                
                mat_months = mat_months[::-1]
                mat_label = f"MAT_{month_names[current_month]}_{current_year}"
                
                all_mat_periods.append({
                    'label': mat_label,
                    'months': mat_months,
                    'end_year': current_year,
                    'end_month': current_month
                })
                
                current_month -= 1
                if current_month == 0:
                    current_month = 12
                    current_year -= 1
                
                mat_count += 1
            
            return all_mat_periods
            
        except Exception as e:
            st.error(f"Error calculating MAT periods: {str(e)}")
            return []
    
    def get_unique_values(self, column):
        """Get unique values from a column"""
        if self.df is not None and column in self.df.columns:
            return sorted([x for x in self.df[column].unique() if str(x) != 'nan' and str(x) != 'Unknown'])
        return []
    
    def filter_data(self, filters):
        """Apply filters to the dataframe"""
        if self.df is None:
            return pd.DataFrame()
        
        filtered_df = self.df.copy()
        
        for column, values in filters.items():
            if values and 'All' not in values and column in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[column].isin(values)]
        
        return filtered_df
    
    def filter_data_by_mat(self, df, mat_months):
        """Filter dataframe to include only data from specified MAT months"""
        if df.empty or not mat_months:
            return df.copy()
        
        try:
            work_df = df.copy()
            work_df['Month_num'] = pd.to_numeric(work_df['Month'], errors='coerce')
            work_df['Year_num'] = pd.to_numeric(work_df['Year'], errors='coerce')
            
            filtered_df = work_df[
                work_df.apply(
                    lambda row: (int(row['Year_num']), int(row['Month_num'])) in mat_months,
                    axis=1
                )
            ].copy()
            
            filtered_df = filtered_df.drop(columns=['Year_num', 'Month_num'], errors='ignore')
            return filtered_df
        except Exception as e:
            st.error(f"Error filtering MAT data: {str(e)}")
            return df.copy()
    
    def prepare_geojson(self, gdf):
        """Prepare GeoDataFrame for JSON serialization"""
        gdf_copy = gdf.copy()
        
        for col in gdf_copy.columns:
            if gdf_copy[col].dtype == 'datetime64[ns]':
                gdf_copy[col] = gdf_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            elif pd.api.types.is_datetime64_any_dtype(gdf_copy[col]):
                gdf_copy[col] = gdf_copy[col].astype(str)
        
        return gdf_copy
    
    def create_choropleth_map(self, df, gdf, adm_col='AdmDiv', value_col='Amount_(BDT)', 
                             title="Bangladesh Sales Map", color_scale='Viridis'):
        """Create choropleth map for Bangladesh divisions"""
        if df.empty or gdf is None:
            st.warning("No data or shapefile available for mapping")
            return go.Figure()
        
        if adm_col not in df.columns:
            st.warning(f"Column '{adm_col}' not found in data")
            return go.Figure()
        
        agg_data = df.groupby(adm_col)[value_col].sum().reset_index()
        agg_data.columns = ['AdmDiv', 'Value']
        
        map_data = gdf.merge(agg_data, on='AdmDiv', how='left')
        map_data['Value'] = map_data['Value'].fillna(0)
        
        map_data_clean = self.prepare_geojson(map_data)
        geojson = json.loads(map_data_clean.to_json())
        
        fig = px.choropleth_mapbox(
            map_data,
            geojson=geojson,
            locations=map_data.index,
            color='Value',
            hover_name='AdmDiv',
            hover_data={'Value': ':.2f'},
            mapbox_style="carto-positron",
            center={"lat": 23.8103, "lon": 90.4125},
            zoom=6,
            color_continuous_scale=color_scale,
            title=title,
            labels={'Value': value_col}
        )
        
        fig.update_layout(
            height=700,
            title_x=0.5,
            margin={"r": 0, "t": 50, "l": 0, "b": 0}
        )
        
        return fig
    
    def create_trend_chart(self, df, time_col, value_var, group_by_params=None, 
                          agg_type='sum', chart_type='line', title="Trend Chart"):
        """Create trend chart"""
        if df.empty or time_col not in df.columns or value_var not in df.columns:
            return go.Figure()
        
        if group_by_params and len(group_by_params) > 0:
            group_cols = [time_col] + group_by_params
            
            if agg_type == 'sum':
                trend_data = df.groupby(group_cols)[value_var].sum().reset_index()
            else:
                trend_data = df.groupby(group_cols)[value_var].mean().reset_index()
            
            trend_data = trend_data.sort_values(time_col)
            
            fig = px.line(trend_data, x=time_col, y=value_var, color=group_by_params[0] if group_by_params else None,
                         title=title, markers=True)
        else:
            if agg_type == 'sum':
                trend_data = df.groupby(time_col)[value_var].sum().reset_index()
            else:
                trend_data = df.groupby(time_col)[value_var].mean().reset_index()
            
            trend_data = trend_data.sort_values(time_col)
            
            fig = px.line(trend_data, x=time_col, y=value_var, title=title, markers=True)
        
        fig.update_layout(height=600, title_x=0.5)
        return fig
    
    def create_bar_chart(self, df, x_col, y_col, title="Bar Chart"):
        """Create bar chart"""
        if df.empty or x_col not in df.columns or y_col not in df.columns:
            return go.Figure()
        
        chart_data = df.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False)
        
        fig = px.bar(chart_data, x=x_col, y=y_col, title=title)
        fig.update_layout(height=600, title_x=0.5)
        return fig


def main():
    st.markdown('<h1 class="main-header">📊 Sales Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    st.sidebar.header("⚙️ Application Setup")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="Select a comma-separated CSV file with your sales data"
    )
    
    if uploaded_file is not None:
        # Initialize dashboard
        dashboard = SalesDashboard()
        df = dashboard.load_data_from_upload(uploaded_file)
        
        if df is not None and not df.empty:
            dashboard.initialize_data(df)
            
            st.sidebar.success("✅ Data loaded successfully!")
            
            # Display dataset information
            with st.expander("📋 Dataset Information"):
                st.write(f"**Total Records:** {len(dashboard.df):,}")
                st.write(f"**Columns:** {', '.join(dashboard.df.columns.tolist())}")
                st.write(f"**Date Range:** {dashboard.df['Year'].min() if 'Year' in dashboard.df.columns else 'N/A'} - {dashboard.df['Year'].max() if 'Year' in dashboard.df.columns else 'N/A'}")
                if dashboard.gdf is not None:
                    st.write(f"**Geographic Divisions Available:** {len(dashboard.gdf)}")
                    st.write(f"**Divisions:** {', '.join(dashboard.gdf['AdmDiv'].tolist())}")
            
            st.markdown("---")
            
            # Global filters
            st.sidebar.header("📍 Global Filters")
            
            filters = {}
            
            # Add filters based on available columns
            filter_columns = ['DivName', 'Brand', 'Year', 'FY', 'Quarter']
            
            for col in filter_columns:
                if col in dashboard.df.columns:
                    unique_vals = ['All'] + dashboard.get_unique_values(col)
                    selected = st.sidebar.multiselect(
                        col,
                        unique_vals,
                        default=['All'],
                        key=f"filter_{col}"
                    )
                    filters[col] = selected
            
            # Apply filters
            filtered_df = dashboard.filter_data(filters)
            
            if not filtered_df.empty:
                # Display key metrics
                st.markdown("### 📈 Key Metrics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if 'Amount_(BDT)' in filtered_df.columns:
                        total_amount = filtered_df['Amount_(BDT)'].sum()
                        st.metric("💰 Total Sales (BDT)", f"{total_amount:,.0f}")
                
                with col2:
                    if 'Qty_(Pcs)' in filtered_df.columns:
                        total_qty_pcs = filtered_df['Qty_(Pcs)'].sum()
                        st.metric("📦 Total Qty (Pcs)", f"{total_qty_pcs:,.0f}")
                
                with col3:
                    if 'Qty_(KG)' in filtered_df.columns:
                        total_qty_kg = filtered_df['Qty_(KG)'].sum()
                        st.metric("⚖️ Total Qty (KG)", f"{total_qty_kg:,.2f}")
                
                with col4:
                    unique_records = len(filtered_df)
                    st.metric("📊 Total Records", f"{unique_records:,}")
                
                st.markdown("---")
                
                # Tabs for different analyses
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🗺️ Geographic Map",
                    "📈 Trend Analysis",
                    "📊 Summary Statistics",
                    "📋 Data Table",
                    "💾 Export Data"
                ])
                
                with tab1:
                    st.markdown('<div class="section-header">🗺️ Geographic Analysis</div>', unsafe_allow_html=True)
                    
                    if dashboard.gdf is not None and 'AdmDiv' in filtered_df.columns:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            map_value_var = st.selectbox(
                                "Value to Display",
                                ['Amount_(BDT)', 'Qty_(Pcs)', 'Qty_(KG)'],
                                key="map_value"
                            )
                        
                        with col2:
                            color_scale = st.selectbox(
                                "Color Scale",
                                ['Viridis', 'Blues', 'Greens', 'Reds', 'YlOrRd', 'RdYlGn'],
                                key="map_color"
                            )
                        
                        if st.button("🗺️ Generate Map"):
                            map_fig = dashboard.create_choropleth_map(
                                filtered_df,
                                dashboard.gdf,
                                'AdmDiv',
                                map_value_var,
                                f"Bangladesh {map_value_var} Distribution",
                                color_scale
                            )
                            st.plotly_chart(map_fig, use_container_width=True)
                    else:
                        st.warning("Geographic data not available or AdmDiv column missing")
                
                with tab2:
                    st.markdown('<div class="section-header">📈 Trend Analysis</div>', unsafe_allow_html=True)
                    
                    time_cols = [col for col in ['Year', 'Quarter', 'MonthName', 'YearMonth'] if col in dashboard.df.columns]
                    
                    if time_cols:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            time_col = st.selectbox("Time Period", time_cols, key="trend_time")
                            value_col = st.selectbox("Value", ['Amount_(BDT)', 'Qty_(Pcs)', 'Qty_(KG)'], key="trend_value")
                        
                        with col2:
                            group_col = st.selectbox(
                                "Group By (optional)",
                                ['None'] + [col for col in dashboard.parameters if col in dashboard.df.columns],
                                key="trend_group"
                            )
                        
                        if st.button("📊 Generate Trend"):
                            group_params = [group_col] if group_col != 'None' else []
                            trend_fig = dashboard.create_trend_chart(
                                filtered_df,
                                time_col,
                                value_col,
                                group_params,
                                title=f"Trend: {value_col} over {time_col}"
                            )
                            st.plotly_chart(trend_fig, use_container_width=True)
                    else:
                        st.warning("No time columns available in data")
                
                with tab3:
                    st.markdown('<div class="section-header">📊 Summary Statistics</div>', unsafe_allow_html=True)
                    
                    summary_col = st.selectbox(
                        "Analyze by",
                        [col for col in dashboard.parameters if col in dashboard.df.columns],
                        key="summary_col"
                    )
                    
                    if summary_col and 'Amount_(BDT)' in filtered_df.columns:
                        summary_data = filtered_df.groupby(summary_col).agg({
                            'Amount_(BDT)': ['sum', 'mean', 'count']
                        }).round(2)
                        summary_data.columns = ['Total Sales', 'Avg Sales', 'Count']
                        summary_data = summary_data.sort_values('Total Sales', ascending=False)
                        
                        st.dataframe(summary_data, use_container_width=True)
                
                with tab4:
                    st.markdown('<div class="section-header">📋 Data Table</div>', unsafe_allow_html=True)
                    
                    # Show with MonthName instead of Month if available
                    display_df = filtered_df.copy()
                    if 'MonthName' in display_df.columns and 'Month' in display_df.columns:
                        display_df = display_df.drop('Month', axis=1)
                        display_df = display_df.rename(columns={'MonthName': 'Month'})
                    
                    st.dataframe(display_df.head(1000), use_container_width=True)
                    st.write(f"Showing 1,000 of {len(filtered_df):,} records")
                
                with tab5:
                    st.markdown('<div class="section-header">💾 Export Data</div>', unsafe_allow_html=True)
                    
                    # Prepare export data
                    export_df = filtered_df.copy()
                    if 'MonthName' in export_df.columns and 'Month' in export_df.columns:
                        export_df = export_df.drop('Month', axis=1)
                        export_df = export_df.rename(columns={'MonthName': 'Month'})
                    
                    csv = export_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"sales_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    st.success("✅ Click button above to download the current filtered data")
            else:
                st.warning("No data matches the selected filters")
        else:
            st.error("Failed to load data. Please check your CSV file format.")
    else:
        st.info("""
        👋 Welcome to Sales Analysis Dashboard
        
        **How to use:**
        1. Upload a CSV file using the file uploader on the left
        2. The CSV should contain sales data with columns like:
           - Amount_(BDT), Qty_(Pcs), Qty_(KG)
           - Year, Month (as numbers 1-12), Quarter
           - Brand, Division, or other categorical data
           - AdmDiv (for geographic analysis, optional)
        3. Once loaded, explore the data using the tabs and filters
        
        **Supported Columns:**
        - Month: Should be numeric (1=January, 12=December)
        - Year: Numeric year value
        - Quarter: Numeric quarter (1-4)
        - Amount_(BDT): Sales amount in Bangladeshi Taka
        - Qty_(Pcs): Quantity in pieces
        - Qty_(KG): Quantity in kilograms
        - AdmDiv: Administrative division for geographic mapping
        """)


if __name__ == "__main__":
    main()