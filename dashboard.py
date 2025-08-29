import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="WiFi Funding Intelligence Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'data_dict' not in st.session_state:
    st.session_state.data_dict = {}

@st.cache_data
def load_excel_data(file_path):
    """Load all sheets from Excel file with caching"""
    try:
        excel_file = pd.ExcelFile(file_path)
        data_dict = {}
        
        for sheet_name in excel_file.sheet_names:
            # Load data with better error handling
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Clean and convert data types to prevent Arrow serialization issues
            for col in df.columns:
                # Handle datetime columns
                if 'date' in col.lower() or 'time' in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except:
                        df[col] = df[col].astype(str)  # Convert to string if datetime fails
                
                # Handle numeric columns with mixed types
                elif df[col].dtype == 'object':
                    # Try to convert to numeric, if fails keep as string
                    try:
                        # Remove currency symbols and commas for numeric conversion
                        if df[col].dtype == 'object':
                            cleaned_col = df[col].astype(str).str.replace('$', '').str.replace(',', '').str.replace('(', '-').str.replace(')', '')
                            pd.to_numeric(cleaned_col, errors='raise')
                            df[col] = pd.to_numeric(cleaned_col, errors='coerce')
                    except:
                        # If conversion fails, ensure it's a clean string
                        df[col] = df[col].astype(str).fillna('')
                
                # Handle boolean columns
                elif df[col].dtype == 'bool':
                    df[col] = df[col].fillna(False)
            
            # Ensure all object columns are strings to prevent Arrow issues
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str).fillna('')
            
            data_dict[sheet_name] = df
        
        return data_dict
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None

def calculate_total_funding(data_dict):
    """Calculate total funding across all sheets"""
    total_funding = 0
    
    # Emergency Connectivity Fund
    if 'Emergency Connectivity Fund' in data_dict:
        df = data_dict['Emergency Connectivity Fund']
        if 'FRN Approved Amount' in df.columns:
            amounts = df['FRN Approved Amount'].astype(str).str.replace('$', '').str.replace(',', '')
            amounts = pd.to_numeric(amounts, errors='coerce')
            total_funding += amounts.sum()
    
    # E-Rate
    if 'E-Rate' in data_dict:
        df = data_dict['E-Rate']
        if 'Total Funding' in df.columns:
            amounts = df['Total Funding'].astype(str).str.replace('$', '').str.replace(',', '')
            amounts = pd.to_numeric(amounts, errors='coerce')
            total_funding += amounts.sum()
    
    # Public Housing Funding
    if 'Public Housing Funding' in data_dict:
        df = data_dict['Public Housing Funding']
        if 'Award_Amount_USD' in df.columns:
            total_funding += pd.to_numeric(df['Award_Amount_USD'], errors='coerce').sum()
    
    return total_funding

def main_dashboard():
    """Main dashboard page"""
    st.markdown('<h1 class="main-header">📡 WiFi Funding Intelligence Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    if not st.session_state.data_loaded:
        # Try to load from file paths first
        with st.spinner("Loading data..."):
            # Try multiple possible file paths
            possible_paths = [
                "Data.xlsx",  # Relative path for Streamlit Cloud
                r"C:\Users\bushe\OneDrive\Orient Research\Mission Telecom\Data.xlsx",  # Local path
                "./Data.xlsx"  # Alternative relative path
            ]
            
            data_dict = None
            for path in possible_paths:
                try:
                    data_dict = load_excel_data(path)
                    if data_dict:
                        st.success(f"Data loaded successfully from: {path}")
                        break
                except Exception as e:
                    continue
        
        # If file loading failed, offer file upload option
        if not data_dict:
            st.error("Could not find Data.xlsx file automatically")
            st.info("""
            **Please upload your Excel file:**
            1. Use the file uploader below, OR
            2. Make sure 'Data.xlsx' is in the same folder as this dashboard
            3. For Streamlit Cloud: Upload the Excel file to your repository
            """)
            
            uploaded_file = st.file_uploader("Upload your Excel file", type=['xlsx', 'xls'])
            if uploaded_file is not None:
                try:
                    # Save uploaded file temporarily
                    with open("temp_data.xlsx", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    data_dict = load_excel_data("temp_data.xlsx")
                    if data_dict:
                        st.success("Data loaded successfully from uploaded file!")
                    else:
                        st.error("Failed to process uploaded file")
                        return
                except Exception as e:
                    st.error(f"Error processing uploaded file: {e}")
                    return
            else:
                st.warning("Please upload an Excel file to continue")
                return
        
        if data_dict:
            st.session_state.data_dict = data_dict
            st.session_state.data_loaded = True
    
    # Calculate total funding
    total_funding = calculate_total_funding(st.session_state.data_dict)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Funding Amount", f"${total_funding:,.0f}")
    
    with col2:
        total_sheets = len(st.session_state.data_dict)
        st.metric("Data Sources", total_sheets)
    
    with col3:
        # Count total records across all sheets
        total_records = sum(len(df) for df in st.session_state.data_dict.values())
        st.metric("Total Records", f"{total_records:,}")
    
    with col4:
        # Count unique states (approximate)
        all_states = set()
        for sheet_name, df in st.session_state.data_dict.items():
            for col in df.columns:
                if 'state' in col.lower():
                    all_states.update(df[col].dropna().unique())
        st.metric("States Covered", len(all_states))
    
    st.markdown("---")
    
    # Data overview
    st.subheader("📊 Data Overview")
    
    # Create overview table
    overview_data = []
    for sheet_name, df in st.session_state.data_dict.items():
        overview_data.append({
            'Sheet Name': sheet_name,
            'Records': len(df),
            'Columns': len(df.columns),
            'Sample Columns': ', '.join(df.columns[:5]) + ('...' if len(df.columns) > 5 else '')
        })
    
    overview_df = pd.DataFrame(overview_data)
    st.dataframe(overview_df, width='stretch')

def emergency_connectivity_page():
    """Emergency Connectivity Fund detailed page"""
    st.header("🚨 Emergency Connectivity Fund Analysis")
    
    try:
        if 'data_dict' not in st.session_state:
            st.error("Data not loaded. Please go to the main dashboard first.")
            return
        
        df = st.session_state.data_dict.get('Emergency Connectivity Fund')
        if df is None:
            st.error("Emergency Connectivity Fund data not found.")
            return
        
        # Display basic info about the data
        st.info(f"📊 Data loaded: {len(df)} records with {len(df.columns)} columns")
        
    except Exception as e:
        st.error(f"Error loading Emergency Connectivity Fund data: {e}")
        st.write("Please try refreshing the page or going back to the main dashboard.")
        return
    
    # Key metrics at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            total_apps = len(df)
            st.metric("Total Applications", f"{total_apps:,}")
        except:
            st.metric("Total Applications", "Data Error")
    
    with col2:
        # Calculate total funding
        try:
            amounts = df['FRN Approved Amount'].astype(str).str.replace('$', '').str.replace(',', '')
            amounts = pd.to_numeric(amounts, errors='coerce')
            total_funding = amounts.sum()
            st.metric("Total Funding Approved", f"${total_funding:,.0f}")
        except:
            st.metric("Total Funding Approved", "Data Error")
    
    with col3:
        try:
            unique_states = df['Billed Entity State'].nunique()
            st.metric("States Covered", unique_states)
        except:
            st.metric("States Covered", "Data Error")
    
    with col4:
        try:
            unique_applicants = df['Applicant Name'].nunique()
            st.metric("Unique Applicants", f"{unique_applicants:,}")
        except:
            st.metric("Unique Applicants", "Data Error")
    
    st.markdown("---")
    
    # Simple data display
    st.subheader("📋 Data Preview")
    try:
        st.dataframe(df.head(10), width='stretch')
    except Exception as e:
        st.error(f"Could not display data: {e}")

def public_housing_page():
    """Public Housing Funding page"""
    st.header("🏠 Public Housing Funding Analysis")
    
    try:
        if 'data_dict' not in st.session_state:
            st.error("Data not loaded. Please go to the main dashboard first.")
            return
        
        df = st.session_state.data_dict.get('Public Housing Funding')
        if df is None:
            st.error("Public Housing Funding data not found.")
            return
        
        # Display basic info about the data
        st.info(f"📊 Data loaded: {len(df)} records with {len(df.columns)} columns")
        
    except Exception as e:
        st.error(f"Error loading Public Housing Funding data: {e}")
        st.write("Please try refreshing the page or going back to the main dashboard.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            total_developments = len(df)
            st.metric("Total Developments", total_developments)
        except:
            st.metric("Total Developments", "Data Error")
    
    with col2:
        try:
            total_funding = pd.to_numeric(df['Award_Amount_USD'], errors='coerce').sum()
            st.metric("Total Funding Awarded", f"${total_funding:,.0f}")
        except:
            st.metric("Total Funding Awarded", "Data Error")
    
    with col3:
        try:
            connected_count = df['Connected'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False}).sum()
            connection_rate = (connected_count / total_developments) * 100
            st.metric("Connected Developments", f"{connected_count} ({connection_rate:.1f}%)")
        except:
            st.metric("Connected Developments", "Data Error")
    
    with col4:
        try:
            wifi_count = df['In_Building_WiFi'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False}).sum()
            wifi_rate = (wifi_count / total_developments) * 100
            st.metric("WiFi Available", f"{wifi_count} ({wifi_rate:.1f}%)")
        except:
            st.metric("WiFi Available", "Data Error")
    
    st.markdown("---")
    
    # Simple data display
    st.subheader("📋 Data Preview")
    try:
        st.dataframe(df.head(10), width='stretch')
    except Exception as e:
        st.error(f"Could not display data: {e}")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    [
        "Main Dashboard",
        "Emergency Connectivity Fund", 
        "Public Housing Funding"
    ]
)

# Page routing
if page == "Main Dashboard":
    main_dashboard()
elif page == "Emergency Connectivity Fund":
    emergency_connectivity_page()
elif page == "Public Housing Funding":
    public_housing_page()
