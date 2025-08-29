# WiFi Funding Intelligence Dashboard

A comprehensive Streamlit dashboard for analyzing WiFi funding and connectivity data across multiple programs and initiatives.

## Features

- **Multi-Sheet Excel Analysis**: Processes Excel files with multiple tabs
- **Interactive Visualizations**: Maps, charts, and graphs for data exploration
- **Advanced Filtering**: Filter data by state, program type, funding amount, and more
- **Export Functionality**: Download filtered data and insights as CSV
- **Sales Intelligence**: Identify top prospects and opportunities

## Pages

1. **Main Dashboard**: Executive summary with key metrics
2. **Emergency Connectivity Fund**: 41K+ applications with geographic analysis
3. **Public Housing Funding**: 200+ developments with connectivity insights
4. **E-Rate**: Educational funding analysis
5. **Additional Pages**: Lifeline, Grants, Tribal Funding, and more

## Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Dashboard**:
   ```bash
   streamlit run dashboard.py
   ```

3. **Upload Data**: Use the file uploader or place `Data.xlsx` in the same directory

## Streamlit Cloud Deployment

### Option 1: Upload File to Repository
1. Add your `Data.xlsx` file to the repository
2. Deploy to Streamlit Cloud
3. The dashboard will automatically load the file

### Option 2: Use File Uploader
1. Deploy to Streamlit Cloud without the Excel file
2. Use the built-in file uploader to upload your data
3. The dashboard will process the uploaded file

### Required Files for Deployment
- `dashboard.py` - Main application
- `requirements.txt` - Python dependencies
- `Data.xlsx` - Your data file (optional, can use uploader)

## Data Format

The dashboard expects an Excel file with multiple sheets:
- Emergency Connectivity Fund
- E-Rate
- Public Housing Funding
- Lifeline Program
- Federal Grants (Grants.Gov)
- Tribal Funding (FTIA)
- Tribal Priority Capital Fund
- Nonprofit WiFi Spending
- Marketing Intelligence
- Industry News

## Troubleshooting

### File Not Found Error
- Ensure `Data.xlsx` is in the same directory as `dashboard.py`
- Use the file uploader if deploying to Streamlit Cloud
- Check file permissions and naming

### Data Loading Issues
- Verify Excel file format (.xlsx or .xls)
- Check that sheets contain the expected column names
- Use the error messages to identify specific issues

### Performance Issues
- Large files may take time to load
- Use filters to reduce data size for better performance
- Consider splitting very large datasets

## Support

For issues or questions, check the error messages in the dashboard or review the data format requirements.
