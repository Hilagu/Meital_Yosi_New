import pandas as pd
import os
import glob
from datetime import datetime

# Directory containing processed CSV files
processed_dir = r"C:\Users\ASUS\Downloads\new source files\processed"
output_dir = processed_dir

# Read all processed files and combine them
print("Reading all processed CSV files...")
csv_files = glob.glob(os.path.join(processed_dir, "processed_*_WBPth.csv"))
print(f"Found {len(csv_files)} processed files")

all_data = []
for csv_file in csv_files:
    filename = os.path.basename(csv_file)
    source_sheet = filename.replace("processed_", "").replace(".csv", "")
    df = pd.read_csv(csv_file)
    df.insert(0, 'Source_Sheet', source_sheet)
    all_data.append(df)
    print(f"  Loaded: {source_sheet} ({len(df)} rows)")

df = pd.concat(all_data, ignore_index=True)
print(f"\nTotal rows combined: {len(df)}")

# Target timepoints in minutes from start (after "Measuring antidote")
target_timepoints = [2.5, 4.8, 5.5, 7.5]

print(f"\nTarget timepoints (minutes): {target_timepoints}")

def is_valid_subject(val):
    """Check if value is a valid subject like 2a, 3b, 1e, etc."""
    if pd.isna(val):
        return False
    val = str(val).strip()
    if len(val) < 2:
        return False
    return val[:-1].isdigit() and val[-1].isalpha()

def get_group(subject):
    """Extract group letter from subject (e.g., '2a' -> 'a')"""
    return str(subject)[-1].lower()

def get_subject_number(subject):
    """Extract subject number (e.g., '2a' -> 2)"""
    return int(str(subject)[:-1])

# Process each source sheet separately
all_results = []
source_sheets = df['Source_Sheet'].unique()

for source_sheet in source_sheets:
    sheet_df = df[df['Source_Sheet'] == source_sheet].copy()
    
    # Find the "Measuring antidote" row to get start time
    start_row = sheet_df[sheet_df['Subject'].astype(str).str.contains('Measuring antidote', na=False)]
    
    if len(start_row) == 0:
        print(f"  Skipping {source_sheet}: No 'Measuring antidote' found")
        continue
    
    start_date = start_row.iloc[0]['Date']
    start_time = start_row.iloc[0]['Time']
    
    try:
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M:%S.%f")
    except:
        try:
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M:%S")
        except:
            print(f"  Skipping {source_sheet}: Cannot parse start time")
            continue
    
    # Filter to only valid data rows
    data_rows = sheet_df[sheet_df['Subject'].apply(is_valid_subject)].copy()
    
    if len(data_rows) == 0:
        print(f"  Skipping {source_sheet}: No valid data rows")
        continue
    
    # Calculate elapsed time in minutes
    def calc_elapsed_minutes(row):
        try:
            row_datetime = datetime.strptime(f"{row['Date']} {row['Time']}", "%Y-%m-%d %H:%M:%S.%f")
        except:
            try:
                row_datetime = datetime.strptime(f"{row['Date']} {row['Time']}", "%Y-%m-%d %H:%M:%S")
            except:
                return None
        return (row_datetime - start_datetime).total_seconds() / 60
    
    data_rows['Elapsed_Minutes'] = data_rows.apply(calc_elapsed_minutes, axis=1)
    data_rows = data_rows.dropna(subset=['Elapsed_Minutes'])
    
    # For each target timepoint, find the CLOSEST single row
    for target in target_timepoints:
        data_rows['Distance'] = abs(data_rows['Elapsed_Minutes'] - target)
        closest_row = data_rows.loc[data_rows['Distance'].idxmin()].copy()
        
        # Only include if within 1 minute of target
        if closest_row['Distance'] <= 1.0:
            closest_row['Timepoint'] = target
            closest_row['Group'] = get_group(closest_row['Subject'])
            closest_row['Subject_Number'] = get_subject_number(closest_row['Subject'])
            all_results.append(closest_row)

if all_results:
    result_df = pd.DataFrame(all_results)
    print(f"\nTotal rows: {len(result_df)}")
    
    # Sort by Group, Timepoint, then Subject_Number (so all 2.5 of group A are together, etc.)
    result_df = result_df.sort_values(['Group', 'Timepoint', 'Subject_Number'])
    
    # Select and reorder columns (remove duplicates and temporary columns)
    final_cols = ['Group', 'Subject_Number', 'Subject', 'Timepoint', 'Elapsed_Minutes',
                  'Source_Sheet', 'Date', 'Time', 'Phase', 'Recording', 'Alarms',
                  'f', 'TVb', 'MVb', 'Penh', 'PAU', 'Rpef', 'Comp', 'PIFb', 'PEFb',
                  'Ti', 'Te', 'EF50', 'EIP', 'EEP', 'Tr', 'TB', 'TP', 'Tbody', 'Tc', 'RH', 'Rinx', 'BFCF']
    
    final_cols = [c for c in final_cols if c in result_df.columns]
    result_df = result_df[final_cols]
    
    # Save the grouped CSV
    output_file = os.path.join(output_dir, "grouped_by_timepoints.csv")
    result_df.to_csv(output_file, index=False)
    print(f"\nSaved: grouped_by_timepoints.csv")
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY BY GROUP:")
    print("="*60)
    
    for group in sorted(result_df['Group'].unique()):
        group_df = result_df[result_df['Group'] == group]
        subjects = sorted(group_df['Subject'].unique().tolist())
        print(f"\nGroup {group.upper()}: {len(subjects)} subjects")
        print(f"  Subjects: {subjects}")
        for tp in target_timepoints:
            tp_count = len(group_df[group_df['Timepoint'] == tp])
            print(f"  Timepoint {tp} min: {tp_count} rows")
    
    print(f"\n{'='*60}")
    print(f"Total: {len(result_df)} data points")
    print(f"  {len(result_df['Subject'].unique())} subjects")
    print(f"  {len(target_timepoints)} timepoints each")
else:
    print("No matching data found.")
