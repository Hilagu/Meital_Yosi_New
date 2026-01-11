import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# Read the cleaned grouped data (outliers removed)
data_file = r"C:\Users\ASUS\Downloads\new source files\processed\grouped_by_timepoints_cleaned.csv"
output_dir = r"C:\Users\ASUS\Downloads\new source files\processed\graphs"

import os
os.makedirs(output_dir, exist_ok=True)

print("Reading data...")
df = pd.read_csv(data_file)

# Parameters to analyze (excluding constant values)
parameters = ['f', 'TVb', 'MVb', 'Penh', 'PAU', 'Rpef', 'PIFb', 'PEFb',
              'Ti', 'Te', 'EF50', 'EIP', 'EEP', 'Tr', 'TB', 'TP', 'Rinx']

# Filter to only parameters that exist and have variation
parameters = [p for p in parameters if p in df.columns]

groups = sorted(df['Group'].unique())
timepoints = sorted(df['Timepoint'].unique())
group_pairs = list(combinations(groups, 2))

print(f"Groups: {groups}")
print(f"Timepoints: {timepoints}")
print(f"Parameters: {parameters}")

def get_significance_stars(p_value):
    if pd.isna(p_value):
        return ""
    elif p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    else:
        return ""

def calculate_fold_change(mean1, mean2):
    """Calculate fold change (Group2/Group1)"""
    if mean1 == 0 or pd.isna(mean1) or pd.isna(mean2):
        return np.nan
    return mean2 / mean1

def add_significance_bracket(ax, x1, x2, y, h, sig_text):
    """Add a significance bracket with asterisks between two x positions"""
    ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], lw=1.2, c='black')
    ax.text((x1+x2)/2, y+h, sig_text, ha='center', va='bottom', fontsize=10, fontweight='bold')

# Color palette for groups
colors = {'a': '#E74C3C', 'b': '#3498DB', 'c': '#2ECC71', 'd': '#9B59B6', 'e': '#F39C12'}

print("\nGenerating box plots with significance markers...")

for param in parameters:
    print(f"\nCreating plot for: {param}")
    
    # Check if parameter has valid data
    param_data = df[param].dropna()
    if len(param_data) == 0 or param_data.std() == 0:
        print(f"  Skipping {param}: No variation in data")
        continue
    
    # Create figure with subplot for graph and table
    fig = plt.figure(figsize=(18, 14))
    
    # Box plot area (top)
    ax_box = fig.add_axes([0.06, 0.42, 0.90, 0.52])
    
    # Prepare data for box plot
    positions = []
    box_data = []
    box_colors = []
    labels = []
    
    pos = 0
    group_positions = {}  # To store x positions for each group at each timepoint
    
    for tp_idx, tp in enumerate(timepoints):
        tp_data = df[df['Timepoint'] == tp]
        group_positions[tp] = {}
        
        for g_idx, g in enumerate(groups):
            data = tp_data[tp_data['Group'] == g][param].dropna().values
            if len(data) > 0:
                box_data.append(data)
                positions.append(pos)
                box_colors.append(colors[g])
                group_positions[tp][g] = pos
                labels.append(f"{g.upper()}")
            pos += 1
        pos += 1.5  # Gap between timepoints
    
    # Create box plot
    bp = ax_box.boxplot(box_data, positions=positions, patch_artist=True, widths=0.7)
    
    # Color the boxes
    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Set x-axis labels
    ax_box.set_xticks(positions)
    ax_box.set_xticklabels(labels, fontsize=9)
    
    # Add timepoint labels
    tp_label_positions = []
    for tp_idx, tp in enumerate(timepoints):
        if tp in group_positions and group_positions[tp]:
            tp_positions = list(group_positions[tp].values())
            tp_label_positions.append((np.mean(tp_positions), f"{tp} min"))
    
    # Add timepoint markers
    ax2 = ax_box.twiny()
    ax2.set_xlim(ax_box.get_xlim())
    ax2.set_xticks([p[0] for p in tp_label_positions])
    ax2.set_xticklabels([p[1] for p in tp_label_positions], fontsize=11, fontweight='bold')
    
    ax_box.set_ylabel(param, fontsize=12, fontweight='bold')
    ax_box.set_title(f'Box Plot: {param} by Group and Timepoint\n(Significant comparisons marked with brackets)', 
                     fontsize=14, fontweight='bold', pad=20)
    ax_box.grid(True, alpha=0.3, axis='y')
    
    # Add legend
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=colors[g], alpha=0.7, label=f'Group {g.upper()}') 
                       for g in groups]
    ax_box.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    # Calculate statistics and add significance brackets
    n_comparisons = len(group_pairs)
    table_data = []
    significant_pairs = []
    
    for g1, g2 in group_pairs:
        comparison = f"{g1.upper()} vs {g2.upper()}"
        
        data1 = df[df['Group'] == g1][param].dropna()
        data2 = df[df['Group'] == g2][param].dropna()
        
        mean1 = data1.mean()
        mean2 = data2.mean()
        
        if len(data1) > 1 and len(data2) > 1:
            # Using uncorrected t-test (least strict - no multiple comparison correction)
            t_stat, p_value = stats.ttest_ind(data1, data2)
            fold_change = calculate_fold_change(mean1, mean2)
            sig = get_significance_stars(p_value)  # Use raw p-value, no correction
            
            table_data.append([
                comparison,
                f"{mean1:.4f}",
                f"{mean2:.4f}",
                f"{fold_change:.3f}" if not pd.isna(fold_change) else "N/A",
                f"{p_value:.4f}",  # Raw uncorrected p-value
                sig if sig else "ns"
            ])
            
            # Store significant pairs for drawing brackets
            if sig:
                significant_pairs.append((g1, g2, sig, p_value))
        else:
            table_data.append([comparison, "N/A", "N/A", "N/A", "N/A", "N/A"])
    
    # Add significance brackets on the graph
    # Get the y-axis range
    y_max = ax_box.get_ylim()[1]
    y_min = ax_box.get_ylim()[0]
    y_range = y_max - y_min
    
    # Sort significant pairs by p-value (most significant first)
    significant_pairs.sort(key=lambda x: x[3])
    
    # Draw brackets for each timepoint
    bracket_offset = 0
    for tp in timepoints:
        if tp not in group_positions:
            continue
            
        # Get positions for this timepoint
        tp_group_pos = group_positions[tp]
        
        # Find significant pairs that exist in this timepoint
        tp_sig_pairs = []
        for g1, g2, sig, pval in significant_pairs:
            if g1 in tp_group_pos and g2 in tp_group_pos:
                tp_sig_pairs.append((g1, g2, sig, pval, tp_group_pos[g1], tp_group_pos[g2]))
        
        # Draw brackets (limit to top 3 most significant to avoid clutter)
        for i, (g1, g2, sig, pval, x1, x2) in enumerate(tp_sig_pairs[:3]):
            # Calculate bracket height
            bracket_y = y_max + (y_range * 0.02) + (y_range * 0.08 * i)
            bracket_h = y_range * 0.02
            
            # Draw the bracket
            ax_box.plot([x1, x1, x2, x2], [bracket_y, bracket_y + bracket_h, bracket_y + bracket_h, bracket_y], 
                       lw=1.2, c='black')
            ax_box.text((x1 + x2) / 2, bracket_y + bracket_h + (y_range * 0.01), sig, 
                       ha='center', va='bottom', fontsize=9, fontweight='bold', color='red')
    
    # Adjust y-axis to accommodate brackets
    new_y_max = y_max + (y_range * 0.35)
    ax_box.set_ylim(y_min, new_y_max)
    
    # Create table (bottom)
    ax_table = fig.add_axes([0.06, 0.02, 0.90, 0.35])
    ax_table.axis('off')
    
    # Use uncorrected p-values (least strict test)
    col_labels = ['Comparison', 'Mean G1', 'Mean G2', 'Fold Change\n(G2/G1)', 'p-value\n(uncorrected)', 'Sig.']
    
    # Create table
    table = ax_table.table(
        cellText=table_data,
        colLabels=col_labels,
        loc='center',
        cellLoc='center',
        colWidths=[0.18, 0.13, 0.13, 0.15, 0.18, 0.12]
    )
    
    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    
    # Color header
    for i in range(len(col_labels)):
        table[(0, i)].set_facecolor('#2C3E50')
        table[(0, i)].set_text_props(color='white', fontweight='bold')
    
    # Color significant rows
    for row_idx, row in enumerate(table_data):
        if row[-1] in ['*', '**', '***']:
            for col_idx in range(len(col_labels)):
                table[(row_idx + 1, col_idx)].set_facecolor('#D5F5E3')
    
    # Add note
    ax_table.text(0.5, -0.02, 'Significance: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant. Fold Change = Mean G2 / Mean G1. Using uncorrected t-test (no multiple comparison correction)',
                  transform=ax_table.transAxes, ha='center', fontsize=8, style='italic')
    
    # Save figure
    output_file = os.path.join(output_dir, f'boxplot_{param}.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: boxplot_{param}.png")

# Create summary figure with all significant parameters
print("\n\nCreating summary of significant findings...")

sig_params = ['TVb', 'MVb', 'EF50', 'Rinx', 'PEFb', 'Rpef']
sig_params = [p for p in sig_params if p in df.columns]

if len(sig_params) > 0:
    n_params = len(sig_params)
    n_cols = 2
    n_rows = (n_params + 1) // 2
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6*n_rows))
    axes = axes.flatten() if n_params > 1 else [axes]
    
    for idx, param in enumerate(sig_params):
        ax = axes[idx]
        
        positions = []
        box_data = []
        box_colors = []
        labels = []
        group_positions_summary = {}
        
        pos = 0
        for tp in timepoints:
            tp_data = df[df['Timepoint'] == tp]
            group_positions_summary[tp] = {}
            for g in groups:
                data = tp_data[tp_data['Group'] == g][param].dropna().values
                if len(data) > 0:
                    box_data.append(data)
                    positions.append(pos)
                    box_colors.append(colors[g])
                    group_positions_summary[tp][g] = pos
                    labels.append(f"{g.upper()}")
                pos += 1
            pos += 1.5
        
        bp = ax.boxplot(box_data, positions=positions, patch_artist=True, widths=0.6)
        for patch, color in zip(bp['boxes'], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylabel(param, fontsize=10, fontweight='bold')
        ax.set_title(f'{param}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Calculate and show significant pairs
        significant_pairs = []
        for g1, g2 in group_pairs:
            data1 = df[df['Group'] == g1][param].dropna()
            data2 = df[df['Group'] == g2][param].dropna()
            if len(data1) > 1 and len(data2) > 1:
                t_stat, p_value = stats.ttest_ind(data1, data2)
                sig = get_significance_stars(p_value)
                if sig:
                    significant_pairs.append((g1, g2, sig, p_value))
        
        # Sort by p-value
        significant_pairs.sort(key=lambda x: x[3])
        
        # Draw brackets for first timepoint only (to avoid clutter in summary)
        if timepoints[0] in group_positions_summary:
            tp_group_pos = group_positions_summary[timepoints[0]]
            y_max = ax.get_ylim()[1]
            y_min = ax.get_ylim()[0]
            y_range = y_max - y_min
            
            for i, (g1, g2, sig, pval) in enumerate(significant_pairs[:3]):
                if g1 in tp_group_pos and g2 in tp_group_pos:
                    x1, x2 = tp_group_pos[g1], tp_group_pos[g2]
                    bracket_y = y_max + (y_range * 0.02) + (y_range * 0.1 * i)
                    bracket_h = y_range * 0.03
                    ax.plot([x1, x1, x2, x2], [bracket_y, bracket_y + bracket_h, bracket_y + bracket_h, bracket_y], 
                           lw=1, c='black')
                    ax.text((x1 + x2) / 2, bracket_y + bracket_h, sig, 
                           ha='center', va='bottom', fontsize=8, fontweight='bold', color='red')
            
            ax.set_ylim(y_min, y_max + y_range * 0.4)
    
    # Hide empty subplots
    for idx in range(len(sig_params), len(axes)):
        axes[idx].set_visible(False)
    
    # Add legend
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=colors[g], alpha=0.7, label=f'Group {g.upper()}') 
                       for g in groups]
    fig.legend(handles=legend_elements, loc='upper center', ncol=5, fontsize=10, bbox_to_anchor=(0.5, 0.98))
    
    plt.suptitle('Summary: Parameters with Significant Group Differences\n(Brackets show significant comparisons)', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    summary_file = os.path.join(output_dir, 'summary_significant_parameters.png')
    plt.savefig(summary_file, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: summary_significant_parameters.png")

print("\n" + "="*60)
print("BOX PLOTS WITH SIGNIFICANCE MARKERS COMPLETE!")
print("="*60)
print(f"\nOutput folder: {output_dir}")
print(f"\nFiles created:")
for param in parameters:
    print(f"  - boxplot_{param}.png")
print(f"  - summary_significant_parameters.png")
