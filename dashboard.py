import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="WiFi Funding Intelligence Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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

# Initialize session state for data caching
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

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
    """Calculate total funding across all datasets"""
    total_funding = 0
    
    # Emergency Connectivity Fund - try to extract amounts from string columns
    if 'Emergency Connectivity Fund' in data_dict:
        df = data_dict['Emergency Connectivity Fund']
        if 'FRN Approved Amount' in df.columns:
            # Convert string amounts to numeric
            amounts = df['FRN Approved Amount'].astype(str).str.replace('$', '').str.replace(',', '')
            amounts = pd.to_numeric(amounts, errors='coerce')
            total_funding += amounts.sum()
    
    # E-Rate funding
    if 'E-Rate' in data_dict:
        df = data_dict['E-Rate']
        if 'Category1_Funding' in df.columns:
            total_funding += df['Category1_Funding'].sum()
        if 'Category2_Funding' in df.columns:
            total_funding += df['Category2_Funding'].sum()
    
    # Lifeline Program
    if 'Lifeline Program' in data_dict:
        df = data_dict['Lifeline Program']
        if 'Lifeline_Subsidies_Granted' in df.columns:
            total_funding += df['Lifeline_Subsidies_Granted'].sum()
    
    # Grants.Gov
    if 'Grants.Gov' in data_dict:
        df = data_dict['Grants.Gov']
        if 'Amount' in df.columns:
            total_funding += df['Amount'].sum()
    
    # 990Breakdown - WiFi initiatives spending
    if '990Breakdown' in data_dict:
        df = data_dict['990Breakdown']
        if 'WiFi_Initiatives' in df.columns:
            total_funding += df['WiFi_Initiatives'].sum()
    
    # Public Housing Funding
    if 'Public Housing Funding' in data_dict:
        df = data_dict['Public Housing Funding']
        if 'Award_Amount_USD' in df.columns:
            total_funding += df['Award_Amount_USD'].sum()
    
    return total_funding

def main_dashboard():
    """Main dashboard page"""
    st.markdown('<h1 class="main-header">📡 WiFi Funding Intelligence Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    if not st.session_state.data_loaded:
        with st.spinner("Loading data..."):
                               data_dict = load_excel_data("Data.xlsx")
            if data_dict:
                st.session_state.data_dict = data_dict
                st.session_state.data_loaded = True
                st.success("Data loaded successfully!")
            else:
                st.error("Failed to load data")
                return
    
    # Calculate total funding
    total_funding = calculate_total_funding(st.session_state.data_dict)
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Funding Programs",
            value=len(st.session_state.data_dict),
            delta="9 datasets"
        )
    
    with col2:
        # Count total records across all datasets
        total_records = sum(len(df) for df in st.session_state.data_dict.values())
        st.metric(
            label="Total Records",
            value=f"{total_records:,}",
            delta="Comprehensive data"
        )
    
    with col3:
        # Count Emergency Connectivity Fund records
        ecf_records = len(st.session_state.data_dict.get('Emergency Connectivity Fund', pd.DataFrame()))
        st.metric(
            label="ECF Applications",
            value=f"{ecf_records:,}",
            delta="Primary dataset"
        )
    
    with col4:
        # Total funding amount
        st.metric(
            label="Total Funding Amount",
            value=f"${total_funding:,.0f}",
            delta="Across all programs"
        )
    
    st.markdown("---")
    
    # Quick overview of datasets
    st.subheader("📊 Dataset Overview")
    
    dataset_info = []
    for sheet_name, df in st.session_state.data_dict.items():
        dataset_info.append({
            'Dataset': sheet_name,
            'Records': len(df),
            'Columns': len(df.columns),
            'Type': 'Funding' if 'funding' in sheet_name.lower() or 'grant' in sheet_name.lower() else 'Spending' if 'spending' in sheet_name.lower() else 'Other'
        })
    
    overview_df = pd.DataFrame(dataset_info)
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
    
    # Advanced filters
    st.subheader("🔍 Advanced Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            states = sorted(df['Billed Entity State'].astype(str).dropna().unique())
            selected_state = st.selectbox("Select State", ['All States'] + list(states))
        except:
            selected_state = st.selectbox("Select State", ['All States'])
    
    with col2:
        try:
            app_types = sorted(df['Applicant Type'].astype(str).dropna().unique())
            selected_type = st.selectbox("Select Applicant Type", ['All Types'] + list(app_types))
        except:
            selected_type = st.selectbox("Select Applicant Type", ['All Types'])
    
    with col3:
        try:
            service_types = sorted(df['Service Type'].astype(str).dropna().unique())
            selected_service = st.selectbox("Select Service Type", ['All Types'] + list(service_types))
        except:
            selected_service = st.selectbox("Select Service Type", ['All Types'])
    
    # Funding amount filter
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            amounts = df['FRN Approved Amount'].astype(str).str.replace('$', '').str.replace(',', '')
            amounts = pd.to_numeric(amounts, errors='coerce').dropna()
            min_amount = float(amounts.min())
            max_amount = float(amounts.max())
            
            funding_range = st.slider(
                "Funding Amount Range ($)",
                min_value=min_amount,
                max_value=max_amount,
                value=(min_amount, max_amount),
                step=1000.0
            )
        except:
            st.write("Funding range filter unavailable due to data format issues")
            funding_range = (0.0, 1000000.0)  # Default range
    
    with col2:
        # Status filter
        try:
            statuses = sorted(df['Application Status'].astype(str).dropna().unique())
            selected_status = st.multiselect("Application Status", statuses, default=statuses)
        except:
            selected_status = st.multiselect("Application Status", ["No data available"])
    
    # Filter data
    filtered_df = df.copy()
    
    try:
        if selected_state != 'All States':
            filtered_df = filtered_df[filtered_df['Billed Entity State'].astype(str) == selected_state]
        if selected_type != 'All Types':
            filtered_df = filtered_df[filtered_df['Applicant Type'].astype(str) == selected_type]
        if selected_service != 'All Types':
            filtered_df = filtered_df[filtered_df['Service Type'].astype(str) == selected_service]
        if selected_status and selected_status != ["No data available"]:
            filtered_df = filtered_df[filtered_df['Application Status'].astype(str).isin(selected_status)]
        
        # Apply funding range filter
        amounts_filtered = filtered_df['FRN Approved Amount'].astype(str).str.replace('$', '').str.replace(',', '')
        amounts_filtered = pd.to_numeric(amounts_filtered, errors='coerce')
        filtered_df = filtered_df[(amounts_filtered >= funding_range[0]) & (amounts_filtered <= funding_range[1]) & (amounts_filtered.notna())]
        
        st.write(f"**Filtered Results:** {len(filtered_df):,} applications")
    except Exception as e:
        st.error(f"Error applying filters: {e}")
        filtered_df = df.copy()
        st.write(f"**Showing all data:** {len(filtered_df):,} applications")
    
    # Visualizations
    st.subheader("📊 Visualizations")
    
    # Map visualization
    st.write("**Geographic Distribution**")
    
    try:
        # Create state-level summary for map
        state_summary = filtered_df.groupby('Billed Entity State').agg({
            'Applicant Name': 'count',
            'FRN Approved Amount': lambda x: pd.to_numeric(x.astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce').sum()
        }).reset_index()
        state_summary.columns = ['State', 'Applications', 'Total_Funding']
        
        # Create choropleth map
        fig = px.choropleth(
            state_summary,
            locations='State',
            locationmode='USA-states',
            color='Total_Funding',
            hover_data=['Applications', 'Total_Funding'],
            title='ECF Funding by State',
            color_continuous_scale='Blues'
        )
        fig.update_layout(geo=dict(scope='usa'))
        st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.error(f"Could not create map visualization: {e}")
        st.write("Map data processing failed. Check data format.")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Top states by applications
        try:
            top_states = filtered_df['Billed Entity State'].value_counts().head(10)
            fig = px.bar(
                x=top_states.values, 
                y=top_states.index,
                orientation='h',
                title='Top 10 States by Applications'
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create top states chart: {e}")
    
    with col2:
        # Applicant types distribution
        try:
            app_type_counts = filtered_df['Applicant Type'].value_counts()
            fig = px.pie(
                values=app_type_counts.values,
                names=app_type_counts.index,
                title='Applications by Applicant Type'
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create applicant types chart: {e}")
    
    # Funding distribution
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            amounts_clean = pd.to_numeric(filtered_df['FRN Approved Amount'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
            fig = px.histogram(
                x=amounts_clean.dropna(),
                nbins=50,
                title='Funding Amount Distribution',
                labels={'x': 'Funding Amount ($)', 'y': 'Number of Applications'}
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create funding distribution chart: {e}")
    
    with col2:
        # Service types
        try:
            service_counts = filtered_df['Service Type'].value_counts().head(10)
            fig = px.bar(
                x=service_counts.values,
                y=service_counts.index,
                orientation='h',
                title='Top 10 Service Types'
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create service types chart: {e}")
    
    # Top prospects table
    st.subheader("🎯 Top Prospects")
    
    # Create prospects table with key info
    try:
        prospects_df = filtered_df[['Applicant Name', 'Billed Entity State', 'Applicant Type', 'Contact Name', 'Contact Email', 'Contact Phone', 'FRN Approved Amount']].copy()
        prospects_df['Funding_Amount'] = pd.to_numeric(prospects_df['FRN Approved Amount'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
        prospects_df = prospects_df.sort_values('Funding_Amount', ascending=False).head(20)
        
        # Display prospects table
        st.dataframe(prospects_df, width='stretch')
    except Exception as e:
        st.error(f"Could not create prospects table: {e}")
        st.write("Prospects table creation failed. Check data format.")
    
    # Export functionality
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Filtered Data (CSV)"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"ecf_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🎯 Export Top Prospects (CSV)"):
            csv = prospects_df.to_csv(index=False)
            st.download_button(
                label="Download Prospects CSV",
                data=csv,
                file_name=f"ecf_prospects_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Full data table (collapsible)
    with st.expander("📋 View Full Filtered Data"):
        st.dataframe(filtered_df, width='stretch')

def erate_page():
    """E-Rate funding page"""
    st.header("🎓 E-Rate Educational Funding")
    
    if 'data_dict' not in st.session_state:
        st.error("Data not loaded. Please go to the main dashboard first.")
        return
    
    df = st.session_state.data_dict.get('E-Rate')
    if df is None:
        st.error("E-Rate data not found.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orgs = len(df)
        st.metric("Total Organizations", total_orgs)
    
    with col2:
        total_cat1 = df['Category1_Funding'].sum()
        st.metric("Total Category 1 Funding", f"${total_cat1:,.0f}")
    
    with col3:
        total_cat2 = df['Category2_Funding'].sum()
        st.metric("Total Category 2 Funding", f"${total_cat2:,.0f}")
    
    with col4:
        total_funding = total_cat1 + total_cat2
        st.metric("Total Funding", f"${total_funding:,.0f}")
    
    st.markdown("---")
    
    # Filters
    st.subheader("🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        states = sorted(df['State'].dropna().unique())
        selected_state = st.selectbox("Select State", ['All States'] + list(states))
    
    with col2:
        entity_types = sorted(df['Entity_Type'].dropna().unique())
        selected_entity = st.selectbox("Select Entity Type", ['All Types'] + list(entity_types))
    
    with col3:
        # Funding range filter
        min_funding = df[['Category1_Funding', 'Category2_Funding']].min().min()
        max_funding = df[['Category1_Funding', 'Category2_Funding']].max().max()
        
        funding_range = st.slider(
            "Total Funding Range ($)",
            min_value=float(min_funding),
            max_value=float(max_funding),
            value=(float(min_funding), float(max_funding)),
            step=1000.0
        )
    
    # Filter data
    filtered_df = df.copy()
    if selected_state != 'All States':
        filtered_df = filtered_df[filtered_df['State'] == selected_state]
    if selected_entity != 'All Types':
        filtered_df = filtered_df[filtered_df['Entity_Type'] == selected_entity]
    
    # Apply funding range filter
    filtered_df['Total_Funding'] = filtered_df['Category1_Funding'] + filtered_df['Category2_Funding']
    filtered_df = filtered_df[(filtered_df['Total_Funding'] >= funding_range[0]) & (filtered_df['Total_Funding'] <= funding_range[1])]
    
    st.write(f"**Filtered Results:** {len(filtered_df)} organizations")
    
    # Visualizations
    st.subheader("📊 Visualizations")
    
    # Map visualization
    st.write("**Geographic Distribution**")
    
    # Create state-level summary for map
    state_summary = filtered_df.groupby('State').agg({
        'Organization_Name': 'count',
        'Category1_Funding': 'sum',
        'Category2_Funding': 'sum'
    }).reset_index()
    state_summary['Total_Funding'] = state_summary['Category1_Funding'] + state_summary['Category2_Funding']
    
    # Create choropleth map
    fig = px.choropleth(
        state_summary,
        locations='State',
        locationmode='USA-states',
        color='Total_Funding',
        hover_data=['Organization_Name', 'Category1_Funding', 'Category2_Funding'],
        title='E-Rate Funding by State',
        color_continuous_scale='Greens'
    )
    fig.update_layout(geo=dict(scope='usa'))
    st.plotly_chart(fig, width='stretch')
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Top states by funding
        top_states = filtered_df.groupby('State')['Total_Funding'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(
            x=top_states.values,
            y=top_states.index,
            orientation='h',
            title='Top 10 States by Total Funding'
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        # Entity types distribution
        entity_counts = filtered_df['Entity_Type'].value_counts()
        fig = px.pie(
            values=entity_counts.values,
            names=entity_counts.index,
            title='Organizations by Entity Type'
        )
        st.plotly_chart(fig, width='stretch')
    
    # Funding analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Category 1 vs Category 2 funding
        fig = px.scatter(
            filtered_df,
            x='Category1_Funding',
            y='Category2_Funding',
            hover_data=['Organization_Name', 'State'],
            title='Category 1 vs Category 2 Funding',
            labels={'Category1_Funding': 'Category 1 Funding ($)', 'Category2_Funding': 'Category 2 Funding ($)'}
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        # Total funding distribution
        fig = px.histogram(
            filtered_df,
            x='Total_Funding',
            nbins=30,
            title='Total Funding Distribution',
            labels={'Total_Funding': 'Total Funding ($)', 'count': 'Number of Organizations'}
        )
        st.plotly_chart(fig, width='stretch')
    
    # Top prospects table
    st.subheader("🎯 Top Prospects")
    
    # Create prospects table
    prospects_df = filtered_df[['Organization_Name', 'State', 'Entity_Type', 'Contact_Email', 'Category1_Funding', 'Category2_Funding', 'Total_Funding']].copy()
    prospects_df = prospects_df.sort_values('Total_Funding', ascending=False).head(20)
    
    # Display prospects table
    st.dataframe(prospects_df, width='stretch')
    
    # Export functionality
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Filtered Data (CSV)"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"erate_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🎯 Export Top Prospects (CSV)"):
            csv = prospects_df.to_csv(index=False)
            st.download_button(
                label="Download Prospects CSV",
                data=csv,
                file_name=f"erate_prospects_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Full data table (collapsible)
    with st.expander("📋 View Full Filtered Data"):
        st.dataframe(filtered_df, width='stretch')

def marketing_page():
    """Marketing intelligence page"""
    st.header("📢 Marketing Intelligence")
    
    if 'data_dict' not in st.session_state:
        st.error("Data not loaded. Please go to the main dashboard first.")
        return
    
    df = st.session_state.data_dict.get('Marketing')
    if df is None:
        st.error("Marketing data not found.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_outlets = len(df)
        st.metric("Total Marketing Outlets", total_outlets)
    
    with col2:
        total_reach = df['Audience_Reach'].sum()
        st.metric("Total Audience Reach", f"{total_reach:,}")
    
    with col3:
        total_cost = df['Annual_Sponsorship_Cost'].sum()
        st.metric("Total Annual Cost", f"${total_cost:,}")
    
    with col4:
        avg_cost_per_reach = total_cost / total_reach if total_reach > 0 else 0
        st.metric("Cost per Reach", f"${avg_cost_per_reach:.2f}")
    
    st.markdown("---")
    
    # Filters
    st.subheader("🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        outlet_types = sorted(df['Type'].dropna().unique())
        selected_type = st.selectbox("Select Outlet Type", ['All Types'] + list(outlet_types))
    
    with col2:
        # Audience reach range
        min_reach = df['Audience_Reach'].min()
        max_reach = df['Audience_Reach'].max()
        
        reach_range = st.slider(
            "Audience Reach Range",
            min_value=int(min_reach),
            max_value=int(max_reach),
            value=(int(min_reach), int(max_reach)),
            step=1000
        )
    
    with col3:
        # Cost range
        min_cost = df['Annual_Sponsorship_Cost'].min()
        max_cost = df['Annual_Sponsorship_Cost'].max()
        
        cost_range = st.slider(
            "Annual Cost Range ($)",
            min_value=int(min_cost),
            max_value=int(max_cost),
            value=(int(min_cost), int(max_cost)),
            step=1000
        )
    
    # Filter data
    filtered_df = df.copy()
    if selected_type != 'All Types':
        filtered_df = filtered_df[filtered_df['Type'] == selected_type]
    
    filtered_df = filtered_df[
        (filtered_df['Audience_Reach'] >= reach_range[0]) & 
        (filtered_df['Audience_Reach'] <= reach_range[1]) &
        (filtered_df['Annual_Sponsorship_Cost'] >= cost_range[0]) & 
        (filtered_df['Annual_Sponsorship_Cost'] <= cost_range[1])
    ]
    
    st.write(f"**Filtered Results:** {len(filtered_df)} outlets")
    
    # Visualizations
    st.subheader("📊 Visualizations")
    
    # Main scatter plot
    fig = px.scatter(
        filtered_df, 
        x='Audience_Reach', 
        y='Annual_Sponsorship_Cost',
        color='Type',
        hover_data=['Outlet_Name', 'Contact_Name', 'Contact_Email'],
        title='Marketing Outlets: Reach vs Cost by Type',
        labels={'Audience_Reach': 'Audience Reach', 'Annual_Sponsorship_Cost': 'Annual Sponsorship Cost ($)'}
    )
    st.plotly_chart(fig, width='stretch')
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Outlet types distribution
        type_counts = filtered_df['Type'].value_counts()
        fig = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title='Distribution by Outlet Type'
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        # Top outlets by reach
        top_outlets = filtered_df.nlargest(10, 'Audience_Reach')
        fig = px.bar(
            top_outlets,
            x='Audience_Reach',
            y='Outlet_Name',
            orientation='h',
            title='Top 10 Outlets by Audience Reach'
        )
        st.plotly_chart(fig, width='stretch')
    
    # Cost efficiency analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Cost per reach analysis
        filtered_df['Cost_Per_Reach'] = filtered_df['Annual_Sponsorship_Cost'] / filtered_df['Audience_Reach']
        efficient_outlets = filtered_df.nsmallest(10, 'Cost_Per_Reach')
        
        fig = px.bar(
            efficient_outlets,
            x='Cost_Per_Reach',
            y='Outlet_Name',
            orientation='h',
            title='Most Cost-Effective Outlets (Lowest Cost per Reach)'
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        # Cost distribution
        fig = px.histogram(
            filtered_df,
            x='Annual_Sponsorship_Cost',
            nbins=20,
            title='Annual Sponsorship Cost Distribution',
            labels={'Annual_Sponsorship_Cost': 'Annual Cost ($)', 'count': 'Number of Outlets'}
        )
        st.plotly_chart(fig, width='stretch')
    
    # Top prospects table
    st.subheader("🎯 Top Marketing Opportunities")
    
    # Create opportunities table with ROI calculation
    opportunities_df = filtered_df[['Outlet_Name', 'Type', 'Audience_Reach', 'Annual_Sponsorship_Cost', 'Contact_Name', 'Contact_Email']].copy()
    opportunities_df['Cost_Per_Reach'] = opportunities_df['Annual_Sponsorship_Cost'] / opportunities_df['Audience_Reach']
    opportunities_df['Reach_Per_Dollar'] = opportunities_df['Audience_Reach'] / opportunities_df['Annual_Sponsorship_Cost']
    
    # Sort by reach per dollar (best ROI)
    opportunities_df = opportunities_df.sort_values('Reach_Per_Dollar', ascending=False).head(15)
    
    # Display opportunities table
    st.dataframe(opportunities_df, width='stretch')
    
    # Export functionality
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Filtered Data (CSV)"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"marketing_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🎯 Export Top Opportunities (CSV)"):
            csv = opportunities_df.to_csv(index=False)
            st.download_button(
                label="Download Opportunities CSV",
                data=csv,
                file_name=f"marketing_opportunities_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Full data table (collapsible)
    with st.expander("📋 View Full Filtered Data"):
        st.dataframe(filtered_df, width='stretch')

def lifeline_page():
    """Lifeline Program page"""
    st.header("📞 Lifeline Program Analysis")
    
    if 'data_dict' not in st.session_state:
        st.error("Data not loaded. Please go to the main dashboard first.")
        return
    
    df = st.session_state.data_dict.get('Lifeline Program')
    if df is None:
        st.error("Lifeline Program data not found.")
        return
    
    st.write(f"**Total Organizations:** {len(df)}")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_households = df['Households_Served'].sum()
        st.metric("Total Households Served", f"{total_households:,}")
    
    with col2:
        total_subsidies = df['Lifeline_Subsidies_Granted'].sum()
        st.metric("Total Subsidies Granted", f"${total_subsidies:,}")
    
    with col3:
        avg_subsidy = df['Lifeline_Subsidies_Granted'].mean()
        st.metric("Average Subsidy per Organization", f"${avg_subsidy:,.0f}")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(df, x='State', y='Households_Served', 
                     title='Households Served by State',
                     color='Lifeline_Subsidies_Granted')
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        fig = px.scatter(df, x='Households_Served', y='Lifeline_Subsidies_Granted',
                         hover_data=['Organization_Name', 'State'],
                         title='Households vs Subsidies')
        st.plotly_chart(fig, width='stretch')
    
    # Show data
    st.dataframe(df, width='stretch')

def grants_gov_page():
    """Grants.Gov page"""
    st.header("🏛️ Federal Grants (Grants.Gov)")
    
    if 'data_dict' not in st.session_state:
        st.error("Data not loaded. Please go to the main dashboard first.")
        return
    
    df = st.session_state.data_dict.get('Grants.Gov')
    if df is None:
        st.error("Grants.Gov data not found.")
        return
    
    st.write(f"**Total Grant Opportunities:** {len(df)}")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_amount = df['Amount'].sum()
        st.metric("Total Grant Amount", f"${total_amount:,.0f}")
    
    with col2:
        avg_amount = df['Amount'].mean()
        st.metric("Average Grant Amount", f"${avg_amount:,.0f}")
    
    with col3:
        status_counts = df['Opportunity Status'].value_counts()
        st.metric("Active Opportunities", f"{len(df[df['Opportunity Status'] == 'Posted'])}")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(df, values='Amount', names='Recipient', 
                     title='Grant Distribution by Recipient')
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        fig = px.bar(df, x='Opportunity Status', y='Amount',
                     title='Grant Amounts by Status')
        st.plotly_chart(fig, width='stretch')
    
    # Show data
    st.dataframe(df, width='stretch')

def tribal_funding_page():
    """FTIA Tribal Funding page"""
    st.header("🏛️ Tribal Funding (FTIA)")
    
    if 'data_dict' not in st.session_state:
        st.error("Data not loaded. Please go to the main dashboard first.")
        return
    
    df = st.session_state.data_dict.get('FTIA Funding Report')
    if df is None:
        st.error("FTIA Funding Report data not found.")
        return
    
    st.write(f"**Total Tribal Entities:** {len(df)}")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        agencies = df['Agency'].nunique()
        st.metric("Funding Agencies", agencies)
    
    with col2:
        programs = df['Program'].nunique()
        st.metric("Program Types", programs)
    
    with col3:
        states = df['Which State'].nunique()
        st.metric("States Covered", states)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        agency_counts = df['Agency'].value_counts().head(10)
        fig = px.bar(x=agency_counts.values, y=agency_counts.index, 
                     orientation='h', title='Top 10 Funding Agencies')
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        program_counts = df['Program'].value_counts().head(10)
        fig = px.bar(x=program_counts.values, y=program_counts.index, 
                     orientation='h', title='Top 10 Program Types')
        st.plotly_chart(fig, width='stretch')
    
    # Show data
    st.dataframe(df, width='stretch')

def tp_cap_fund_page():
    """TP Cap Fund page"""
    st.header("💰 Tribal Priority Capital Fund")
    
    if 'data_dict' not in st.session_state:
        st.error("Data not loaded. Please go to the main dashboard first.")
        return
    
    df = st.session_state.data_dict.get('TP Cap Fund')
    if df is None:
        st.error("TP Cap Fund data not found.")
        return
    
    st.write(f"**Total States/Territories:** {len(df)}")
    
    # Convert funding amounts to numeric
    df_clean = df.copy()
    df_clean['Funding_Amount'] = df_clean['Total CPF Allocation'].str.replace('$', '').str.replace(',', '')
    df_clean['Funding_Amount'] = pd.to_numeric(df_clean['Funding_Amount'], errors='coerce')
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_funding = df_clean['Funding_Amount'].sum()
        st.metric("Total CPF Allocation", f"${total_funding:,.0f}")
    
    with col2:
        avg_funding = df_clean['Funding_Amount'].mean()
        st.metric("Average Allocation", f"${avg_funding:,.0f}")
    
    with col3:
        max_funding = df_clean['Funding_Amount'].max()
        st.metric("Highest Allocation", f"${max_funding:,.0f}")
    
    # Visualizations
    fig = px.bar(df_clean, x='State/Territory', y='Funding_Amount',
                 title='CPF Allocations by State/Territory')
    st.plotly_chart(fig, width='stretch')
    
    # Show data
    st.dataframe(df, width='stretch')

def nonprofit_spending_page():
    """990Breakdown Nonprofit Spending page"""
    st.header("🏢 Nonprofit WiFi Spending (990 Breakdown)")
    
    if 'data_dict' not in st.session_state:
        st.error("Data not loaded. Please go to the main dashboard first.")
        return
    
    df = st.session_state.data_dict.get('990Breakdown')
    if df is None:
        st.error("990Breakdown data not found.")
        return
    
    st.write(f"**Total Organizations:** {len(df)}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_wifi = df['WiFi_Initiatives'].sum()
        st.metric("Total WiFi Spending", f"${total_wifi:,}")
    
    with col2:
        total_digital = df['Digital_Inclusion_Programs'].sum()
        st.metric("Digital Inclusion Spending", f"${total_digital:,}")
    
    with col3:
        total_revenue = df['Total_Revenue'].sum()
        st.metric("Total Revenue", f"${total_revenue:,}")
    
    with col4:
        wifi_percent = (total_wifi / total_revenue * 100) if total_revenue > 0 else 0
        st.metric("WiFi % of Revenue", f"{wifi_percent:.1f}%")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.scatter(df, x='Total_Revenue', y='WiFi_Initiatives',
                         hover_data=['Organization_Name'],
                         title='Revenue vs WiFi Spending')
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        fig = px.bar(df, x='Organization_Name', y='WiFi_Initiatives',
                     title='WiFi Spending by Organization')
        st.plotly_chart(fig, width='stretch')
    
    # Show data
    st.dataframe(df, width='stretch')

def news_page():
    """News and Updates page"""
    st.header("📰 Industry News & Updates")
    
    if 'data_dict' not in st.session_state:
        st.error("Data not loaded. Please go to the main dashboard first.")
        return
    
    df = st.session_state.data_dict.get('NEWS')
    if df is None:
        st.error("NEWS data not found.")
        return
    
    st.write(f"**Total News Items:** {len(df)}")
    
    # Display news items
    for idx, row in df.iterrows():
        with st.expander(f"📰 {row['Headline']} - {row['Date'].strftime('%B %d, %Y')}"):
            st.write(f"**Date:** {row['Date'].strftime('%B %d, %Y')}")
            st.write(f"**Headline:** {row['Headline']}")
            st.write(f"**Story:** {row['Story']}")
            st.markdown("---")

def public_housing_page():
    """Public Housing Funding page"""
    st.header("🏠 Public Housing Funding Analysis")
    
    if 'data_dict' not in st.session_state:
        st.error("Data not loaded. Please go to the main dashboard first.")
        return
    
    df = st.session_state.data_dict.get('Public Housing Funding')
    if df is None:
        st.error("Public Housing Funding data not found.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_developments = len(df)
        st.metric("Total Developments", total_developments)
    
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
    
    # Filters
    st.subheader("🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            states = sorted(df['State'].astype(str).dropna().unique())
            selected_state = st.selectbox("Select State", ['All States'] + list(states))
        except:
            selected_state = st.selectbox("Select State", ['All States'])
    
    with col2:
        try:
            program_types = sorted(df['Program_Type'].astype(str).dropna().unique())
            selected_program = st.selectbox("Select Program Type", ['All Types'] + list(program_types))
        except:
            selected_program = st.selectbox("Select Program Type", ['All Types'])
    
    with col3:
        # Funding range filter
        try:
            funding_numeric = pd.to_numeric(df['Award_Amount_USD'], errors='coerce').dropna()
            min_funding = int(funding_numeric.min())
            max_funding = int(funding_numeric.max())
            
            funding_range = st.slider(
                "Funding Amount Range ($)",
                min_value=min_funding,
                max_value=max_funding,
                value=(min_funding, max_funding),
                step=100
            )
        except:
            st.write("Funding range filter unavailable due to data format issues")
            funding_range = (0, 1000000)  # Default range
    
    # Additional filters
    col1, col2 = st.columns(2)
    
    with col1:
        # Connection status
        connection_status = st.multiselect(
            "Connection Status",
            ['Connected', 'Not Connected'],
            default=['Connected', 'Not Connected']
        )
    
    with col2:
        # WiFi availability
        wifi_status = st.multiselect(
            "WiFi Availability",
            ['WiFi Available', 'No WiFi'],
            default=['WiFi Available', 'No WiFi']
        )
    
    # Filter data
    filtered_df = df.copy()
    
    # Apply state filter
    if selected_state != 'All States':
        filtered_df = filtered_df[filtered_df['State'].astype(str) == selected_state]
    
    # Apply program type filter
    if selected_program != 'All Types':
        filtered_df = filtered_df[filtered_df['Program_Type'].astype(str) == selected_program]
    
    # Apply funding range filter (handle non-numeric values)
    try:
        filtered_df['Award_Amount_USD'] = pd.to_numeric(filtered_df['Award_Amount_USD'], errors='coerce')
        filtered_df = filtered_df[
            (filtered_df['Award_Amount_USD'] >= funding_range[0]) & 
            (filtered_df['Award_Amount_USD'] <= funding_range[1]) &
            (filtered_df['Award_Amount_USD'].notna())
        ]
    except:
        st.warning("Could not filter by funding amount due to data format issues")
    
    # Apply connection status filter (handle boolean conversion)
    try:
        filtered_df['Connected'] = filtered_df['Connected'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False})
        
        if 'Connected' not in connection_status:
            filtered_df = filtered_df[~filtered_df['Connected']]
        if 'Not Connected' not in connection_status:
            filtered_df = filtered_df[filtered_df['Connected']]
    except:
        st.warning("Could not filter by connection status due to data format issues")
    
    # Apply WiFi status filter (handle boolean conversion)
    try:
        filtered_df['In_Building_WiFi'] = filtered_df['In_Building_WiFi'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False})
        
        if 'WiFi Available' not in wifi_status:
            filtered_df = filtered_df[~filtered_df['In_Building_WiFi']]
        if 'No WiFi' not in wifi_status:
            filtered_df = filtered_df[filtered_df['In_Building_WiFi']]
    except:
        st.warning("Could not filter by WiFi status due to data format issues")
    
    st.write(f"**Filtered Results:** {len(filtered_df)} developments")
    
    # Visualizations
    st.subheader("📊 Visualizations")
    
    # Map visualization
    st.write("**Geographic Distribution**")
    
    # Create state-level summary for map
    try:
        # Ensure numeric columns for aggregation
        filtered_df['Award_Amount_USD'] = pd.to_numeric(filtered_df['Award_Amount_USD'], errors='coerce')
        filtered_df['Connected'] = filtered_df['Connected'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False})
        filtered_df['In_Building_WiFi'] = filtered_df['In_Building_WiFi'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False})
        
        state_summary = filtered_df.groupby('State').agg({
            'Development_Name': 'count',
            'Award_Amount_USD': 'sum',
            'Connected': 'sum',
            'In_Building_WiFi': 'sum'
        }).reset_index()
        state_summary.columns = ['State', 'Developments', 'Total_Funding', 'Connected_Count', 'WiFi_Count']
        
        # Create choropleth map
        fig = px.choropleth(
            state_summary,
            locations='State',
            locationmode='USA-states',
            color='Total_Funding',
            hover_data=['Developments', 'Connected_Count', 'WiFi_Count'],
            title='Public Housing Funding by State',
            color_continuous_scale='Reds'
        )
        fig.update_layout(geo=dict(scope='usa'))
        st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.error(f"Could not create map visualization: {e}")
        st.write("Map data processing failed. Check data format.")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Top states by funding
        try:
            top_states = filtered_df.groupby('State')['Award_Amount_USD'].sum().sort_values(ascending=False).head(10)
            fig = px.bar(
                x=top_states.values,
                y=top_states.index,
                orientation='h',
                title='Top 10 States by Funding Amount'
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create top states chart: {e}")
    
    with col2:
        # Program types distribution
        try:
            program_counts = filtered_df['Program_Type'].value_counts()
            fig = px.pie(
                values=program_counts.values,
                names=program_counts.index,
                title='Developments by Program Type'
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create program types chart: {e}")
    
    # Connectivity analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Connection status
        try:
            connection_counts = filtered_df['Connected'].value_counts()
            fig = px.bar(
                x=['Connected', 'Not Connected'],
                y=[connection_counts.get(True, 0), connection_counts.get(False, 0)],
                title='Connection Status Distribution',
                color=['Connected', 'Not Connected']
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create connection status chart: {e}")
    
    with col2:
        # WiFi availability
        try:
            wifi_counts = filtered_df['In_Building_WiFi'].value_counts()
            fig = px.bar(
                x=['WiFi Available', 'No WiFi'],
                y=[wifi_counts.get(True, 0), wifi_counts.get(False, 0)],
                title='WiFi Availability Distribution',
                color=['WiFi Available', 'No WiFi']
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create WiFi availability chart: {e}")
    
    # Speed analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Download speeds
        try:
            filtered_df['Download_Mbps'] = pd.to_numeric(filtered_df['Download_Mbps'], errors='coerce')
            fig = px.histogram(
                filtered_df.dropna(subset=['Download_Mbps']),
                x='Download_Mbps',
                nbins=20,
                title='Download Speed Distribution',
                labels={'Download_Mbps': 'Download Speed (Mbps)', 'count': 'Number of Developments'}
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create download speed chart: {e}")
    
    with col2:
        # Upload speeds
        try:
            filtered_df['Upload_Mbps'] = pd.to_numeric(filtered_df['Upload_Mbps'], errors='coerce')
            fig = px.histogram(
                filtered_df.dropna(subset=['Upload_Mbps']),
                x='Upload_Mbps',
                nbins=20,
                title='Upload Speed Distribution',
                labels={'Upload_Mbps': 'Upload Speed (Mbps)', 'count': 'Number of Developments'}
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create upload speed chart: {e}")
    
    # Funding analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Funding distribution
        try:
            fig = px.histogram(
                filtered_df.dropna(subset=['Award_Amount_USD']),
                x='Award_Amount_USD',
                nbins=30,
                title='Funding Amount Distribution',
                labels={'Award_Amount_USD': 'Award Amount ($)', 'count': 'Number of Developments'}
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create funding distribution chart: {e}")
    
    with col2:
        # Funding vs connectivity
        try:
            # Ensure both columns are numeric
            scatter_df = filtered_df.copy()
            scatter_df['Award_Amount_USD'] = pd.to_numeric(scatter_df['Award_Amount_USD'], errors='coerce')
            scatter_df['Download_Mbps'] = pd.to_numeric(scatter_df['Download_Mbps'], errors='coerce')
            scatter_df = scatter_df.dropna(subset=['Award_Amount_USD', 'Download_Mbps'])
            
            fig = px.scatter(
                scatter_df,
                x='Award_Amount_USD',
                y='Download_Mbps',
                color='Connected',
                hover_data=['Development_Name', 'State'],
                title='Funding vs Download Speed',
                labels={'Award_Amount_USD': 'Award Amount ($)', 'Download_Mbps': 'Download Speed (Mbps)'}
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Could not create funding vs connectivity chart: {e}")
    
    # Top prospects table
    st.subheader("🎯 Top Opportunities")
    
    # Create opportunities table
    try:
        opportunities_df = filtered_df[['Development_Name', 'State', 'City', 'Program_Type', 'Connected', 'In_Building_WiFi', 'Download_Mbps', 'Award_Amount_USD', 'Digital_Training_Hours']].copy()
        
        # Ensure numeric columns for scoring
        opportunities_df['Award_Amount_USD'] = pd.to_numeric(opportunities_df['Award_Amount_USD'], errors='coerce')
        opportunities_df['Connected'] = opportunities_df['Connected'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False})
        
        # Add opportunity score (higher funding + not connected = better opportunity)
        opportunities_df['Opportunity_Score'] = opportunities_df['Award_Amount_USD'] * (1 + (opportunities_df['Connected'] == False).astype(int))
        opportunities_df = opportunities_df.sort_values('Opportunity_Score', ascending=False).head(20)
        
        # Display opportunities table
        st.dataframe(opportunities_df, width='stretch')
    except Exception as e:
        st.error(f"Could not create opportunities table: {e}")
        st.write("Opportunity scoring failed. Check data format.")
    
    # Export functionality
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Filtered Data (CSV)"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"public_housing_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🎯 Export Top Opportunities (CSV)"):
            csv = opportunities_df.to_csv(index=False)
            st.download_button(
                label="Download Opportunities CSV",
                data=csv,
                file_name=f"public_housing_opportunities_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Full data table (collapsible)
    with st.expander("📋 View Full Filtered Data"):
        st.dataframe(filtered_df, width='stretch')

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    [
        "Main Dashboard",
        "Emergency Connectivity Fund", 
        "E-Rate", 
        "Public Housing Funding",
        "Lifeline Program",
        "Federal Grants (Grants.Gov)",
        "Tribal Funding (FTIA)",
        "Tribal Priority Capital Fund",
        "Nonprofit WiFi Spending",
        "Marketing Intelligence",
        "Industry News"
    ]
)

# Page routing
if page == "Main Dashboard":
    main_dashboard()
elif page == "Emergency Connectivity Fund":
    emergency_connectivity_page()
elif page == "E-Rate":
    erate_page()
elif page == "Public Housing Funding":
    public_housing_page()
elif page == "Lifeline Program":
    lifeline_page()
elif page == "Federal Grants (Grants.Gov)":
    grants_gov_page()
elif page == "Tribal Funding (FTIA)":
    tribal_funding_page()
elif page == "Tribal Priority Capital Fund":
    tp_cap_fund_page()
elif page == "Nonprofit WiFi Spending":
    nonprofit_spending_page()
elif page == "Marketing Intelligence":
    marketing_page()
elif page == "Industry News":
    news_page()
