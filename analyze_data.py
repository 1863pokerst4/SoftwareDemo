import pandas as pd
import streamlit as st

def analyze_excel_file(file_path):
    """Analyze the structure of an Excel file with multiple sheets"""
    
    print("=== EXCEL FILE ANALYSIS ===\n")
    
    # Read all sheets
    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        print(f"Found {len(sheet_names)} sheets: {sheet_names}\n")
        
        # Analyze each sheet
        for i, sheet_name in enumerate(sheet_names, 1):
            print(f"--- SHEET {i}: {sheet_name} ---")
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            print(f"Shape: {df.shape} (rows: {df.shape[0]}, columns: {df.shape[1]})")
            print(f"Columns: {list(df.columns)}")
            print(f"Data types:\n{df.dtypes}")
            
            # Show first few rows
            print(f"\nFirst 3 rows:")
            print(df.head(3))
            
            # Basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                print(f"\nNumeric columns: {list(numeric_cols)}")
                print(f"Basic stats for numeric columns:")
                print(df[numeric_cols].describe())
            
            # Check for missing values
            missing_values = df.isnull().sum()
            if missing_values.sum() > 0:
                print(f"\nMissing values:")
                print(missing_values[missing_values > 0])
            
            print("\n" + "="*50 + "\n")
            
    except Exception as e:
        print(f"Error reading Excel file: {e}")

if __name__ == "__main__":
    analyze_excel_file(r"C:\Users\bushe\OneDrive\Orient Research\Mission Telecom\Data.xlsx")
