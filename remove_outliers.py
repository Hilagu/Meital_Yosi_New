import pandas as pd
import numpy as np
import os

# Read the grouped data
data_file = r"C:\Users\ASUS\Downloads\new source files\processed\grouped_by_timepoints.csv"
output_dir = r"C:\Users\ASUS\Downloads\new source files\processed"

print("Reading data...")
df = pd.read_csv(data_file)
print(f"Original data: {len(df)} rows")

# Parameters to check for outliers
parameters = ['f', 'TVb', 'MVb', 'Penh', 'PAU', 'Rpef', 'PIFb', 'PEFb',
              'Ti', 'Te', 'EF50', 'EIP', 'EEP', 'Tr', 'TB', 'TP', 'Rinx', 'BFCF']

# Filter to only parameters that exist in the data
parameters = [p for p in parameters if p in df.columns]
print(f"\nChecking {len(parameters)} parameters for outliers")

# Using 4× SD (Standard Deviation) from group mean as threshold
# This is equivalent to ~4× SEM for detecting extreme outliers
SD_THRESHOLD = 4

# Track outliers - store row indices
outlier_rows = set()
outlier_details = []

print("\n" + "="*60)
print(f"OUTLIER DETECTION (>{SD_THRESHOLD} × SD from GROUP mean)")
print("="*60)

groups = df['Group'].unique()

for group in sorted(groups):
    group_data = df[df['Group'] == group]
    group_indices = group_data.index
    
    print(f"\n--- Group {group.upper()} ({len(group_data)} rows) ---")
    group_outliers = []
    
    for param in parameters:
        # Get valid data for this group and parameter
        param_values = group_data[param].dropna()
        
        if len(param_values) < 3:  # Need at least 3 values
            continue
        
        # Calculate mean and SD within the group
        mean = param_values.mean()
        std = param_values.std()
        
        if std == 0:  # Skip if no variation
            continue
        
        # Define outlier threshold: more than 4 × SD from group mean
        threshold = SD_THRESHOLD * std
        lower_bound = mean - threshold
        upper_bound = mean + threshold
        
        # Find outliers for this parameter within this group
        for idx in group_indices:
            value = df.loc[idx, param]
            if pd.notna(value):
                if value < lower_bound or value > upper_bound:
                    deviation = abs(value - mean) / std
                    subject = df.loc[idx, 'Subject']
                    timepoint = df.loc[idx, 'Timepoint']
                    
                    outlier_rows.add(idx)
                    group_outliers.append({
                        'Parameter': param,
                        'Group': group,
                        'Subject': subject,
                        'Timepoint': timepoint,
                        'Value': value,
                        'Group_Mean': mean,
                        'Group_SD': std,
                        'Deviation_SD': deviation
                    })
    
    if group_outliers:
        # Print unique subjects with outliers
        outlier_subjects = set(o['Subject'] for o in group_outliers)
        print(f"  Outliers: {len(group_outliers)} values from subjects: {', '.join(sorted(outlier_subjects))}")
        outlier_details.extend(group_outliers)
    else:
        print(f"  No outliers found")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

total_outliers = len(outlier_rows)
print(f"\nTotal rows flagged as outliers: {total_outliers}")
print(f"Rows remaining after removal: {len(df) - total_outliers}")

if total_outliers > 0:
    # Get unique subjects that are outliers
    outlier_subjects = df.loc[list(outlier_rows), 'Subject'].unique()
    print(f"\nSubjects with outlier values ({len(outlier_subjects)} subjects):")
    for subj in sorted(outlier_subjects):
        subj_rows = [idx for idx in outlier_rows if df.loc[idx, 'Subject'] == subj]
        # Get which parameters are outliers
        subj_params = set()
        for detail in outlier_details:
            if detail['Subject'] == subj:
                subj_params.add(detail['Parameter'])
        print(f"  - {subj}: {len(subj_rows)} outlier rows ({', '.join(sorted(subj_params)[:3])}...)")

# Create cleaned dataframe (exclude outlier rows)
df_clean = df.drop(index=list(outlier_rows)).copy()
print(f"\nCleaned data: {len(df_clean)} rows")

# Save cleaned CSV
output_file = os.path.join(output_dir, "grouped_by_timepoints_cleaned.csv")
df_clean.to_csv(output_file, index=False)
print(f"\nSaved cleaned data to: {output_file}")

# Save outlier details
if outlier_details:
    outlier_df = pd.DataFrame(outlier_details)
    outlier_df = outlier_df.sort_values(['Group', 'Subject', 'Timepoint', 'Parameter'])
    outlier_file = os.path.join(output_dir, "outliers_removed.csv")
    outlier_df.to_csv(outlier_file, index=False)
    print(f"Saved outlier details to: {outlier_file}")

# Summary by group after cleaning
print("\n" + "="*60)
print("GROUP SUMMARY AFTER CLEANING")
print("="*60)

for group in sorted(df_clean['Group'].unique()):
    group_data = df_clean[df_clean['Group'] == group]
    subjects = sorted(group_data['Subject'].unique())
    print(f"\nGroup {group.upper()}: {len(subjects)} subjects, {len(group_data)} data points")
    print(f"  Subjects: {', '.join(subjects)}")

# Comparison with original
print("\n" + "="*60)
print("COMPARISON: ORIGINAL vs CLEANED")
print("="*60)
print(f"\n{'Group':<10} {'Original Subjects':<20} {'Cleaned Subjects':<20}")
print("-" * 50)
for group in sorted(df['Group'].unique()):
    orig_subj = len(df[df['Group'] == group]['Subject'].unique())
    clean_subj = len(df_clean[df_clean['Group'] == group]['Subject'].unique()) if group in df_clean['Group'].values else 0
    print(f"{group.upper():<10} {orig_subj:<20} {clean_subj:<20}")

print("\n" + "="*60)
print("OUTLIER REMOVAL COMPLETE!")
print("="*60)
