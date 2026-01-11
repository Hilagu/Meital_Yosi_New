import pandas as pd
import numpy as np
from scipy import stats
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# Read the grouped data
data_file = r"C:\Users\ASUS\Downloads\new source files\processed\grouped_by_timepoints.csv"
output_dir = r"C:\Users\ASUS\Downloads\new source files\processed"

print("Reading data...")
df = pd.read_csv(data_file)
print(f"Total rows: {len(df)}")
print(f"Groups: {sorted(df['Group'].unique())}")

# Parameters to analyze
parameters = ['f', 'TVb', 'MVb', 'Penh', 'PAU', 'Rpef', 'Comp', 'PIFb', 'PEFb',
              'Ti', 'Te', 'EF50', 'EIP', 'EEP', 'Tr', 'TB', 'TP', 'Tbody', 'Tc', 'RH', 'Rinx', 'BFCF']

# Filter to only parameters that exist in the data
parameters = [p for p in parameters if p in df.columns]
print(f"\nAnalyzing {len(parameters)} parameters")

groups = sorted(df['Group'].unique())
group_pairs = list(combinations(groups, 2))

def get_significance(p_value):
    """Convert p-value to significance indicator"""
    if pd.isna(p_value):
        return "N/A"
    elif p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    else:
        return "ns"

# Create detailed results - one row per parameter per comparison
detailed_results = []

for param in parameters:
    print(f"\nAnalyzing: {param}")
    
    # Get data for each group
    group_data = {}
    for g in groups:
        data = df[df['Group'] == g][param].dropna()
        group_data[g] = data
        print(f"  Group {g.upper()}: n={len(data)}, mean={data.mean():.4f}, std={data.std():.4f}")
    
    # Perform one-way ANOVA first
    valid_data = [group_data[g].values for g in groups if len(group_data[g]) > 1]
    
    if len(valid_data) >= 2:
        f_stat, anova_p = stats.f_oneway(*valid_data)
    else:
        f_stat, anova_p = np.nan, np.nan
    
    # Number of comparisons for Bonferroni correction
    n_comparisons = len(group_pairs)
    
    # Perform pairwise comparisons
    for g1, g2 in group_pairs:
        data1 = group_data[g1]
        data2 = group_data[g2]
        
        comparison = f"{g1.upper()} vs {g2.upper()}"
        
        row = {
            'Parameter': param,
            'Comparison': comparison,
            'Group1': g1.upper(),
            'Group2': g2.upper(),
            'N_Group1': len(data1),
            'N_Group2': len(data2),
            'Mean_Group1': round(data1.mean(), 4) if len(data1) > 0 else np.nan,
            'Mean_Group2': round(data2.mean(), 4) if len(data2) > 0 else np.nan,
            'Std_Group1': round(data1.std(), 4) if len(data1) > 1 else np.nan,
            'Std_Group2': round(data2.std(), 4) if len(data2) > 1 else np.nan,
        }
        
        if len(data1) > 1 and len(data2) > 1:
            # Perform t-test
            t_stat, p_value = stats.ttest_ind(data1, data2)
            # Bonferroni correction
            p_corrected = min(p_value * n_comparisons, 1.0)
            
            row['t_statistic'] = round(t_stat, 4)
            row['p_value_raw'] = round(p_value, 6)
            row['p_value_corrected'] = round(p_corrected, 6)
            row['Significance'] = get_significance(p_corrected)
            row['Is_Significant'] = "YES" if p_corrected < 0.05 else "NO"
        else:
            row['t_statistic'] = np.nan
            row['p_value_raw'] = np.nan
            row['p_value_corrected'] = np.nan
            row['Significance'] = "N/A"
            row['Is_Significant'] = "N/A"
        
        # Add ANOVA info
        row['ANOVA_F'] = round(f_stat, 4) if not pd.isna(f_stat) else np.nan
        row['ANOVA_p'] = round(anova_p, 6) if not pd.isna(anova_p) else np.nan
        row['ANOVA_Significant'] = "YES" if (not pd.isna(anova_p) and anova_p < 0.05) else "NO"
        
        detailed_results.append(row)

# Create DataFrame and save
results_df = pd.DataFrame(detailed_results)

# Reorder columns for clarity
column_order = [
    'Parameter', 'Comparison', 'Group1', 'Group2',
    'N_Group1', 'N_Group2', 'Mean_Group1', 'Mean_Group2', 'Std_Group1', 'Std_Group2',
    't_statistic', 'p_value_raw', 'p_value_corrected', 'Significance', 'Is_Significant',
    'ANOVA_F', 'ANOVA_p', 'ANOVA_Significant'
]
results_df = results_df[column_order]

# Save full detailed results
output_file = f"{output_dir}/statistical_results_detailed.csv"
results_df.to_csv(output_file, index=False)
print(f"\n\nDetailed results saved to: {output_file}")

# Create summary table - significance matrix
print("\n" + "="*100)
print("SIGNIFICANCE MATRIX (showing significance stars)")
print("="*100)

# Pivot table for significance
sig_matrix = results_df.pivot(index='Parameter', columns='Comparison', values='Significance')
sig_matrix = sig_matrix[['A vs B', 'A vs C', 'A vs D', 'A vs E', 'B vs C', 'B vs D', 'B vs E', 'C vs D', 'C vs E', 'D vs E']]
print(sig_matrix.to_string())

sig_matrix_file = f"{output_dir}/significance_matrix.csv"
sig_matrix.to_csv(sig_matrix_file)
print(f"\nSignificance matrix saved to: {sig_matrix_file}")

# Create YES/NO matrix
print("\n" + "="*100)
print("STATISTICAL SIGNIFICANCE MATRIX (YES/NO)")
print("="*100)

yesno_matrix = results_df.pivot(index='Parameter', columns='Comparison', values='Is_Significant')
yesno_matrix = yesno_matrix[['A vs B', 'A vs C', 'A vs D', 'A vs E', 'B vs C', 'B vs D', 'B vs E', 'C vs D', 'C vs E', 'D vs E']]
print(yesno_matrix.to_string())

yesno_file = f"{output_dir}/significance_yesno.csv"
yesno_matrix.to_csv(yesno_file)
print(f"\nYES/NO matrix saved to: {yesno_file}")

# Create p-value matrix
print("\n" + "="*100)
print("P-VALUE MATRIX (Bonferroni corrected)")
print("="*100)

pval_matrix = results_df.pivot(index='Parameter', columns='Comparison', values='p_value_corrected')
pval_matrix = pval_matrix[['A vs B', 'A vs C', 'A vs D', 'A vs E', 'B vs C', 'B vs D', 'B vs E', 'C vs D', 'C vs E', 'D vs E']]
print(pval_matrix.round(4).to_string())

pval_file = f"{output_dir}/pvalue_matrix.csv"
pval_matrix.to_csv(pval_file)
print(f"\nP-value matrix saved to: {pval_file}")

# Summary statistics
print("\n" + "="*100)
print("SUMMARY")
print("="*100)
sig_results = results_df[results_df['Is_Significant'] == 'YES']
print(f"\nTotal significant comparisons: {len(sig_results)}")
print(f"\nSignificant comparisons by parameter:")
for param in parameters:
    param_sig = sig_results[sig_results['Parameter'] == param]
    if len(param_sig) > 0:
        comparisons = param_sig['Comparison'].tolist()
        print(f"  {param}: {', '.join(comparisons)}")

print("\n" + "="*100)
print("FILES CREATED:")
print("="*100)
print(f"1. statistical_results_detailed.csv - Full details for each comparison")
print(f"2. significance_matrix.csv - Significance stars (*, **, ***)")
print(f"3. significance_yesno.csv - YES/NO for each comparison")
print(f"4. pvalue_matrix.csv - Corrected p-values")
print("\nLegend: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")
