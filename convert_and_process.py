import pandas as pd
import os

# Path to the Excel file
excel_file = r"C:\Users\ASUS\Downloads\new source files\a-c.xlsx"
output_dir = r"C:\Users\ASUS\Downloads\new source files"

# Step 1: Read Excel file and get all sheet names
print("Reading Excel file...")
xl = pd.ExcelFile(excel_file)
sheet_names = xl.sheet_names
print(f"Found {len(sheet_names)} sheets: {sheet_names}")

# Step 2: Convert each sheet to CSV
csv_files = []
for sheet_name in sheet_names:
    print(f"\nProcessing sheet: '{sheet_name}'")
    
    # Read the sheet
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    
    # Save as CSV with sheet name
    # Clean the sheet name to make it a valid filename
    clean_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet_name)
    csv_filename = f"{clean_name}.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    df.to_csv(csv_path, index=False, header=False)
    csv_files.append(csv_filename)
    print(f"  Saved: {csv_filename}")

print("\n" + "="*50)
print("CSV files created:")
for f in csv_files:
    print(f"  - {f}")
print("="*50)

