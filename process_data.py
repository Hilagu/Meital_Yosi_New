import pandas as pd
import os
import glob

# Directory containing CSV files
data_dir = r"C:\Users\ASUS\Downloads\new source files"
output_dir = os.path.join(data_dir, "processed")

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Find all CSV files (excluding the processed ones)
csv_files = glob.glob(os.path.join(data_dir, "*_WBPth.csv"))

print(f"Found {len(csv_files)} CSV files to process")
print("="*60)

processed_files = []
combined_data = []

for csv_file in csv_files:
    filename = os.path.basename(csv_file)
    print(f"\nProcessing: {filename}")
    
    # Read CSV - first row is header
    df = pd.read_csv(csv_file, header=0)
    
    # Get original column names
    original_columns = df.columns.tolist()
    print(f"  Original columns: {original_columns[:5]}...")  # Show first 5
    
    # Find column B (second column) - this is the "Subject" column or similar
    col_b_name = original_columns[1]
    col_b = df[col_b_name].astype(str)
    
    # Find the row indices for "Measuring antidote" and "Experiment Complete"
    start_idx = None
    end_idx = None
    
    for idx, val in enumerate(col_b):
        if "Measuring antidote" in str(val):
            start_idx = idx
            print(f"  Found 'Measuring antidote' at row {idx}")
        if "Experiment Complete" in str(val) and start_idx is not None:
            end_idx = idx
            print(f"  Found 'Experiment Complete' at row {idx}")
            break  # Take the first occurrence after start
    
    if start_idx is None:
        print(f"  WARNING: 'Measuring antidote' not found in {filename}")
        continue
    
    # If "Experiment Complete" not found, use the entire file from start_idx to end
    if end_idx is None:
        end_idx = len(df) - 1
        print(f"  Note: 'Experiment Complete' not found, using end of file (row {end_idx})")
    
    # Extract rows from start_idx to end_idx (inclusive)
    filtered_df = df.iloc[start_idx:end_idx+1].copy()
    print(f"  Extracted {len(filtered_df)} rows (from row {start_idx} to {end_idx})")
    
    # Split the first column (Time/datetime) into Date and Time
    first_col_name = original_columns[0]
    datetime_values = filtered_df[first_col_name].astype(str)
    
    dates = []
    times = []
    
    for val in datetime_values:
        if ' ' in val and len(val) > 10:  # Looks like a datetime
            parts = val.split(' ', 1)
            dates.append(parts[0])
            times.append(parts[1] if len(parts) > 1 else '')
        else:
            dates.append(val)
            times.append('')
    
    # Create new DataFrame with Date and Time as first two columns
    # Start with Date and Time columns
    result_df = pd.DataFrame()
    result_df['Date'] = dates
    result_df['Time'] = times
    
    # Add all other columns (skip the original first column which we split)
    for col in original_columns[1:]:
        result_df[col] = filtered_df[col].values
    
    # Save individual processed file with header
    output_filename = f"processed_{filename}"
    output_path = os.path.join(output_dir, output_filename)
    result_df.to_csv(output_path, index=False)
    processed_files.append(output_filename)
    print(f"  Saved: {output_filename}")
    print(f"  New columns: {result_df.columns.tolist()[:6]}...")
    
    # Add source column for combined output
    result_df_with_source = result_df.copy()
    result_df_with_source.insert(0, 'Source_Sheet', filename.replace('.csv', ''))
    combined_data.append(result_df_with_source)

# Create combined output
if combined_data:
    combined_df = pd.concat(combined_data, ignore_index=True)
    combined_path = os.path.join(output_dir, "combined_all_sheets.csv")
    combined_df.to_csv(combined_path, index=False)
    print(f"\n{'='*60}")
    print(f"Combined file saved: combined_all_sheets.csv")
    print(f"Total rows in combined file: {len(combined_df)}")

print(f"\n{'='*60}")
print("PROCESSING COMPLETE!")
print(f"{'='*60}")
print(f"\nProcessed {len(processed_files)} files")
print(f"\nOutput directory: {output_dir}")
print("\nProcessed files:")
for f in processed_files:
    print(f"  - {f}")
