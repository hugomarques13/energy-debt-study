import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def plot_before_after(df: pd.DataFrame, out_path: str = "results_plot.png", show: bool = True) -> None:
	"""Create a 3-panel grouped bar chart for Before/After comparisons.

	Accepts either of these column name sets:
	  - short: 'E Before (J)', 'E After (J)', 'T Before (ms)', 'T After (ms)', 'J/ms Before', 'J/ms After'
	  - long:  'Energy Before (J)', 'Energy After (J)', 'Time Before (ms)', 'Time After (ms)', 'J/ms Before', 'J/ms After'
	The function will normalize column names internally.
	"""
	df = df.copy()
	# normalize column names (map alternate names to our internal ones)
	col_map = {}
	# energy
	if 'E Before (J)' in df.columns:
		col_map['E Before (J)'] = 'E Before (J)'
	elif 'Energy Before (J)' in df.columns:
		col_map['Energy Before (J)'] = 'E Before (J)'
	if 'E After (J)' in df.columns:
		col_map['E After (J)'] = 'E After (J)'
	elif 'Energy After (J)' in df.columns:
		col_map['Energy After (J)'] = 'E After (J)'
	# time
	if 'T Before (ms)' in df.columns:
		col_map['T Before (ms)'] = 'T Before (ms)'
	elif 'Time Before (ms)' in df.columns:
		col_map['Time Before (ms)'] = 'T Before (ms)'
	if 'T After (ms)' in df.columns:
		col_map['T After (ms)'] = 'T After (ms)'
	elif 'Time After (ms)' in df.columns:
		col_map['Time After (ms)'] = 'T After (ms)'
	# j/ms
	if 'J/ms Before' in df.columns:
		col_map['J/ms Before'] = 'J/ms Before'
	if 'J/ms After' in df.columns:
		col_map['J/ms After'] = 'J/ms After'
	# apply mapping
	df = df.rename(columns=col_map)

	projects = df['Project'].astype(str).tolist()
	n = len(projects)
	x = np.arange(n)
	width = 0.35

	fig, axes = plt.subplots(1, 3, figsize=(14, 5))

	# Energy
	axes[0].bar(x - width/2, df['E Before (J)'], width, label='Before', color='#1f77b4')
	axes[0].bar(x + width/2, df['E After (J)'], width, label='After', color='#ff7f0e')
	axes[0].set_title('Energy (J)')
	axes[0].set_xticks(x)
	axes[0].set_xticklabels(projects, rotation=25, ha='right')
	# (Removed per-bar percent annotations to keep the plot clean)

	# Time
	axes[1].bar(x - width/2, df['T Before (ms)'], width, label='Before', color='#1f77b4')
	axes[1].bar(x + width/2, df['T After (ms)'], width, label='After', color='#ff7f0e')
	axes[1].set_title('Time (ms)')
	axes[1].set_xticks(x)
	axes[1].set_xticklabels(projects, rotation=25, ha='right')
	# (Removed per-bar percent annotations to keep the plot clean)

	# J/ms
	axes[2].bar(x - width/2, df['J/ms Before'], width, label='Before', color='#1f77b4')
	axes[2].bar(x + width/2, df['J/ms After'], width, label='After', color='#ff7f0e')
	axes[2].set_title('J/ms')
	axes[2].set_xticks(x)
	axes[2].set_xticklabels(projects, rotation=25, ha='right')
	# (Removed per-bar percent annotations to keep the plot clean)

	# Common legend above plots to avoid overlap
	plt.tight_layout()
	fig.subplots_adjust(top=0.82)
	from matplotlib.patches import Patch
	handles = [Patch(color='#1f77b4', label='Before'), Patch(color='#ff7f0e', label='After')]
	fig.legend(handles=handles, loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.02), fontsize=10)
	fig.savefig(out_path, dpi=200)
	if show:
		plt.show()


def plot_metric_triptych(
	df: pd.DataFrame,
	metric_specs: list[tuple[str, str, str, str]],
	out_path: str,
	title: str,
	show: bool = True,
) -> None:
	"""Create a clean grouped bar chart for a small set of before/after metrics."""
	df = df.copy()
	projects = df['Project'].astype(str).tolist()
	x = np.arange(len(projects))
	width = 0.35

	fig, axes = plt.subplots(1, len(metric_specs), figsize=(5.2 * len(metric_specs), 5.2))
	if len(metric_specs) == 1:
		axes = [axes]

	for ax, (metric_title, before_col, after_col, y_label) in zip(axes, metric_specs):
		ax.bar(x - width / 2, df[before_col], width, label='Before', color='#1f77b4')
		ax.bar(x + width / 2, df[after_col], width, label='After', color='#ff7f0e')
		ax.set_title(metric_title)
		ax.set_ylabel(y_label)
		ax.set_xticks(x)
		ax.set_xticklabels(projects, rotation=25, ha='right')
		ax.grid(True, axis='y', linestyle='--', linewidth=0.5, alpha=0.25)

	plt.tight_layout()
	fig.subplots_adjust(top=0.82)
	from matplotlib.patches import Patch
	handles = [Patch(color='#1f77b4', label='Before'), Patch(color='#ff7f0e', label='After')]
	fig.legend(handles=handles, loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.02), fontsize=10)
	fig.suptitle(title, y=1.08, fontsize=13, weight='bold')
	fig.savefig(out_path, dpi=200, bbox_inches='tight')
	if show:
		plt.show()


def plot_debt_vs_loc(df: pd.DataFrame, out_path: str = "debt_vs_loc.png", show: bool = True) -> None:
	"""Create a dot graph of debt ratio vs LOC for all projects.

	Plots before/after points from squad_candidates-style columns.
	"""
	df = df.copy()
	if 'project' in df.columns and 'Project' not in df.columns:
		df = df.rename(columns={'project': 'Project'})
	required = ['Project', 'ncloc_r1', 'ncloc_r2', 'debt_ratio_r1', 'debt_ratio_r2']
	missing = [column for column in required if column not in df.columns]
	if missing:
		raise ValueError(f"Missing required columns: {', '.join(missing)}")

	data = df.copy()
	data['Project'] = data['Project'].astype(str)
	data['ncloc_r1'] = pd.to_numeric(data['ncloc_r1'], errors='coerce')
	data['ncloc_r2'] = pd.to_numeric(data['ncloc_r2'], errors='coerce')
	data['debt_ratio_r1'] = pd.to_numeric(data['debt_ratio_r1'], errors='coerce')
	data['debt_ratio_r2'] = pd.to_numeric(data['debt_ratio_r2'], errors='coerce')

	fig, ax = plt.subplots(figsize=(10, 7))
	ax.scatter(
		data['ncloc_r1'],
		data['debt_ratio_r1'],
		label='Before',
		color='#1f77b4',
		alpha=0.7,
		s=45,
		edgecolors='white',
		linewidths=0.5,
	)
	ax.scatter(
		data['ncloc_r2'],
		data['debt_ratio_r2'],
		label='After',
		color='#ff7f0e',
		alpha=0.7,
		s=45,
		edgecolors='white',
		linewidths=0.5,
	)

	ax.set_xscale('log')
	ax.set_xlabel('NCLOC (log scale)')
	ax.set_ylabel('Debt Ratio')
	ax.set_title('Debt vs LOC for All Projects in squad_candidates.csv')
	ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.35)
	ax.legend(loc='upper right')
	fig.tight_layout()
	fig.savefig(out_path, dpi=200)
	if show:
		plt.show()


def plot_selected_release_story(
	df: pd.DataFrame,
	selected_projects: list[dict[str, str]] | None = None,
	out_path: str = "selected_releases_story.png",
	show: bool = True,
) -> None:
	"""Create a polished scatter plot for a small set of selected releases.

	The full candidate pool is shown in gray. The selected releases are highlighted
	and labeled with their project and release pair.
	"""
	df = df.copy()
	if 'project' in df.columns and 'Project' not in df.columns:
		df = df.rename(columns={'project': 'Project'})
	required = ['Project', 'release_high_td', 'release_low_td', 'loc_change_pct', 'debt_drop_pct']
	missing = [column for column in required if column not in df.columns]
	if missing:
		raise ValueError(f"Missing required columns: {', '.join(missing)}")

	data = df.copy()
	data['Project'] = data['Project'].astype(str)
	data['project_display'] = data['Project'].str.replace('#', '/', regex=False)
	data['release_high_td'] = data['release_high_td'].astype(str)
	data['release_low_td'] = data['release_low_td'].astype(str)
	data['loc_change_pct'] = pd.to_numeric(data['loc_change_pct'], errors='coerce')
	data['debt_drop_pct'] = pd.to_numeric(data['debt_drop_pct'], errors='coerce')
	data = data.dropna(subset=['loc_change_pct', 'debt_drop_pct'])

	if selected_projects is None:
		selected_projects = [
			{'project': 'apache/spark', 'release_high_td': 'v1.2.0', 'release_low_td': 'v1.2.1'},
			{'project': 'apache/spark', 'release_high_td': 'v3.3.1', 'release_low_td': 'v3.3.2'},
			{'project': 'apache/ant-ivy', 'release_high_td': '2.4.0-rc1', 'release_low_td': '2.4.0'},
			{'project': 'apache/arrow-rs', 'release_high_td': '4.3.0', 'release_low_td': '4.4.0'},
		]

	def _normalize_project(value: str) -> str:
		return value.replace('#', '/').strip().lower()

	def _find_row(project: str, release_high_td: str, release_low_td: str) -> pd.Series | None:
		project_key = _normalize_project(project)
		project_mask = data['Project'].map(_normalize_project).eq(project_key)
		low_mask = data['release_low_td'].eq(release_low_td)
		exact = data[project_mask & low_mask & data['release_high_td'].eq(release_high_td)]
		if not exact.empty:
			return exact.iloc[0]
		prefix = data[project_mask & low_mask & data['release_high_td'].str.startswith(release_high_td, na=False)]
		if not prefix.empty:
			return prefix.iloc[0]
		contains = data[project_mask & low_mask & data['release_high_td'].str.contains(release_high_td, na=False)]
		if not contains.empty:
			return contains.iloc[0]
		return None

	selected_rows = []
	for item in selected_projects:
		row = _find_row(item['project'], item['release_high_td'], item['release_low_td'])
		if row is not None:
			selected_rows.append(row)

	fig, ax = plt.subplots(figsize=(11.5, 8.5))
	ax.scatter(
		data['loc_change_pct'],
		data['debt_drop_pct'],
		s=22,
		color='#b0b7bf',
		alpha=0.35,
		label='All candidates',
		edgecolors='none',
		zorder=1,
	)

	# Encourage the upper-left quadrant: low LOC growth and high debt reduction.
	ax.axvspan(0, 5, ymin=0.62, ymax=1.0, color='#e8f5e9', alpha=0.85, zorder=0)
	ax.axvline(5, color='#c8d6cb', linestyle='--', linewidth=1.0, zorder=0)
	ax.axhline(40, color='#c8d6cb', linestyle='--', linewidth=1.0, zorder=0)
	ax.text(0.35, 96, 'Preferred zone', fontsize=10, color='#2e7d32', weight='bold')
	ax.text(0.35, 90, 'low LOC growth + high debt drop', fontsize=9, color='#2e7d32')

	highlight_colors = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a']
	label_offsets = [(14, 16), (14, -42), (-180, 16), (-180, -42)]

	for idx, row in enumerate(selected_rows):
		color = highlight_colors[idx % len(highlight_colors)]
		label_dx, label_dy = label_offsets[idx % len(label_offsets)]
		project_label = f"{row['project_display']}\n{row['release_high_td']} → {row['release_low_td']}"
		metric_label = f"LOC {row['loc_change_pct']:.1f}% | Debt {row['debt_drop_pct']:.1f}%"
		ax.scatter(
			row['loc_change_pct'],
			row['debt_drop_pct'],
			s=120,
			color=color,
			edgecolors='black',
			linewidths=0.8,
			zorder=4,
		)
		ax.annotate(
			f"{project_label}\n{metric_label}",
			xy=(row['loc_change_pct'], row['debt_drop_pct']),
			xytext=(label_dx, label_dy),
			textcoords='offset points',
			ha='left',
			va='bottom',
			fontsize=9,
			bbox=dict(boxstyle='round,pad=0.35', fc='white', ec=color, lw=1.1, alpha=0.96),
			arrowprops=dict(arrowstyle='-', color=color, lw=1.0, shrinkA=0, shrinkB=6),
			zorder=5,
		)

	ax.set_xlabel('LOC change (%)')
	ax.set_ylabel('Debt reduction (%)')
	ax.set_title('Selected releases stand out in the low-LOC / high-debt-drop quadrant')
	ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.25)
	ax.set_xlim(left=-0.5)
	ax.set_ylim(bottom=0)
	ax.legend(loc='lower right')
	fig.tight_layout()
	fig.savefig(out_path, dpi=220)
	if show:
		plt.show()


def plot_actual_vs_predicted(
	df: pd.DataFrame,
	highlight_projects: list | None = None,
	out_path: str = "actual_vs_predicted.png",
	show: bool = True,
) -> None:
	"""Create a scatter plot comparing predicted debt drop vs actual debt drop.
	
	Shows all successful scans (status='ok'). Highlights specific projects to show
	which ones delivered real results and why they stand out.
	"""
	df = df.copy()
	# Filter for successful scans only
	df = df[df['status'] == 'ok'].copy()
	# Keep only rows with valid actual_drop_pct
	df = df.dropna(subset=['actual_drop_pct', 'squad_drop_pct'])
	
	df['squad_drop_pct'] = pd.to_numeric(df['squad_drop_pct'], errors='coerce')
	df['actual_drop_pct'] = pd.to_numeric(df['actual_drop_pct'], errors='coerce')
	df['project_display'] = df['project'].str.replace('apache#', 'apache/').str.strip()
	df = df.dropna(subset=['squad_drop_pct', 'actual_drop_pct'])
	
	if highlight_projects is None:
		highlight_projects = [
			{'project': 'apache#shardingsphere', 'actual_drop_pct': 50.0},
			{'project': 'apache#maven-enforcer', 'actual_drop_pct': 28.57},
			{'project': 'apache#commons-imaging', 'actual_drop_pct': 41.18},
		]
	
	fig, ax = plt.subplots(figsize=(10, 8))
	
	# All other projects in muted gray
	other = df[~df['project'].isin([p if isinstance(p, str) else p['project'] for p in highlight_projects])]
	ax.scatter(
		other['squad_drop_pct'],
		other['actual_drop_pct'],
		s=60,
		color='#b0b7bf',
		alpha=0.4,
		label='Other successful scans',
		edgecolors='none',
		zorder=1,
	)
	
	# Perfect prediction line (y=x)
	lims = [0, df['squad_drop_pct'].max() * 1.1]
	ax.plot(lims, lims, 'k--', linewidth=1.2, alpha=0.4, label='Perfect prediction (y=x)', zorder=0)
	
	# Highlighted projects
	colors = {'apache#shardingsphere': '#d95f02', 'apache#maven-enforcer': '#1b9e77', 'apache#commons-imaging': '#7570b3'}
	for proj_spec in highlight_projects:
		if isinstance(proj_spec, str):
			project = proj_spec
			proj_data = df[df['project'] == project]
		else:
			project = proj_spec['project']
			target_actual = proj_spec.get('actual_drop_pct')
			proj_data = df[df['project'] == project]
			if target_actual is not None:
				proj_data = proj_data[abs(proj_data['actual_drop_pct'] - target_actual) < 0.1]
		
		if not proj_data.empty:
			color = colors.get(project, '#7570b3')
			row = proj_data.iloc[0]
			ax.scatter(
				row['squad_drop_pct'],
				row['actual_drop_pct'],
				s=200,
				color=color,
				edgecolors='black',
				linewidths=1.0,
				zorder=4,
			)
			# Simple label
			project_short = project.replace('apache#', '')
			ax.text(
				row['squad_drop_pct'] + 2,
				row['actual_drop_pct'],
				project_short,
				fontsize=10,
				weight='bold',
				va='center',
				color=color,
				zorder=5,
			)
	
	ax.set_xlabel('SQuaD Predicted Debt Drop (%)', fontsize=11)
	ax.set_ylabel('Actual Measured Debt Drop (%)', fontsize=11)
	ax.set_title('Prediction Accuracy: SQuaD vs Actual Scan Results', fontsize=12, weight='bold')
	ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.25)
	ax.set_xlim(left=-2)
	ax.set_ylim(bottom=-15)
	ax.legend(loc='lower right', fontsize=10)
	fig.tight_layout()
	fig.savefig(out_path, dpi=220)
	if show:
		plt.show()


def plot_debt_variation_selected(
	df: pd.DataFrame,
	selected_projects: list[str] | None = None,
	out_path: str = "debt_variation_ratio_selected.png",
	show: bool = True,
) -> None:
	"""Scatter plot for debt variation projects highlighting selected projects."""
	df = df.copy()
	required = ['project', 'ratio_low_to_high', 'delta_minutes']
	missing = [column for column in required if column not in df.columns]
	if missing:
		raise ValueError(f"Missing required columns: {', '.join(missing)}")

	if selected_projects is None:
		selected_projects = [
			'apache#commons-csv',
			'apache#commons-email',
			'apache#maven-enforcer',
			'apache#commons-logging',
		]

	data = df.copy()
	data['project'] = data['project'].astype(str)
	data['ratio_low_to_high'] = pd.to_numeric(data['ratio_low_to_high'], errors='coerce')
	data['delta_minutes'] = pd.to_numeric(data['delta_minutes'], errors='coerce')
	data = data.dropna(subset=['ratio_low_to_high', 'delta_minutes'])

	fig, ax = plt.subplots(figsize=(11, 8))

	others = data[~data['project'].isin(selected_projects)]
	ax.scatter(
		others['ratio_low_to_high'],
		others['delta_minutes'],
		s=50,
		color='#b0b7bf',
		alpha=0.45,
		edgecolors='none',
		label='Other projects',
		zorder=1,
	)

	colors = {
		'apache#commons-csv': '#1b9e77',
		'apache#commons-email': '#d95f02',
		'apache#maven-enforcer': '#7570b3',
		'apache#commons-logging': '#e7298a',
	}
	label_offsets = {
		'apache#commons-csv': (8, 10),
		'apache#commons-email': (8, -14),
		'apache#maven-enforcer': (8, 10),
		'apache#commons-logging': (8, -14),
	}

	for project in selected_projects:
		row = data[data['project'] == project]
		if row.empty:
			continue
		row = row.iloc[0]
		color = colors.get(project, '#333333')
		ax.scatter(
			row['ratio_low_to_high'],
			row['delta_minutes'],
			s=170,
			color=color,
			edgecolors='black',
			linewidths=0.9,
			zorder=3,
		)
		dx, dy = label_offsets.get(project, (8, 8))
		ax.annotate(
			project.replace('apache#', ''),
			xy=(row['ratio_low_to_high'], row['delta_minutes']),
			xytext=(dx, dy),
			textcoords='offset points',
			fontsize=10,
			weight='bold',
			color=color,
		)

	ax.set_xlabel('Ratio (low debt / high debt)')
	ax.set_ylabel('Debt delta in minutes')
	ax.set_title('Projects with real debt variation (ratio vs delta minutes)')
	ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.3)
	ax.legend(loc='lower right')
	fig.tight_layout()
	fig.savefig(out_path, dpi=220)
	if show:
		plt.show()


if __name__ == '__main__':
	# Scatter plot from the full squad_candidates.csv file
	all_projects = pd.read_csv('squad_candidates.csv')
	plot_debt_vs_loc(all_projects, out_path='debt_vs_loc.png', show=True)
	plot_selected_release_story(all_projects, out_path='selected_releases_story.png', show=True)

	# Scatter plot from the pipeline candidates CSV
	pipeline_projects = pd.read_csv('squad_pipeline_candidates.csv')
	plot_debt_vs_loc(pipeline_projects, out_path='debt_vs_loc_pipeline.png', show=True)

	# Actual scan results: predicted vs actual debt drop
	auto_scan = pd.read_csv('auto_scan_results.csv')
	plot_actual_vs_predicted(auto_scan, out_path='actual_vs_predicted.png', show=True)

	# Example dataset from the user's table
	data = [
		{
			'Project': 'commons-csv',
			'E Before (J)': 200.0,
			'E After (J)': 90.0,
			'T Before (ms)': 7670,
			'T After (ms)': 2978,
			'J/ms Before': 0.0261,
			'J/ms After': 0.0302,
		},
		{
			'Project': 'commons-email',
			'E Before (J)': 91.7,
			'E After (J)': 259.9,
			'T Before (ms)': 3953,
			'T After (ms)': 9294,
			'J/ms Before': 0.0232,
			'J/ms After': 0.0280,
		},
	]
	df = pd.DataFrame(data)
	plot_before_after(df, out_path='results_plot.png', show=True)

	# Second dataset (alternate column names) from the user's new table
	data2 = [
		{
			'Project': 'commons-csv',
			'Energy Before (J)': 370.5,
			'Energy After (J)': 410.5,
			'Time Before (ms)': 21843,
			'Time After (ms)': 32720,
			'J/ms Before': 0.0170,
			'J/ms After': 0.0125,
		},
		{
			'Project': 'commons-email',
			'Energy Before (J)': 95.4,
			'Energy After (J)': 130.7,
			'Time Before (ms)': 3465,
			'Time After (ms)': 4405,
			'J/ms Before': 0.0275,
			'J/ms After': 0.0297,
		},
	]
	df2 = pd.DataFrame(data2)
	plot_before_after(df2, out_path='results_plot2.png', show=True)

	# Energy-style results plot for the two highlighted release pairs
	energy_metrics = pd.DataFrame([
		{
			'Project': 'maven-enforcer',
			'E Before (J)': 93.19,
			'E After (J)': 139.61,
			'T Before (ms)': 3330,
			'T After (ms)': 4657,
			'J/ms Before': 0.0280,
			'J/ms After': 0.0300,
		},
		{
			'Project': 'shardingsphere',
			'E Before (J)': 179.60,
			'E After (J)': 189.10,
			'T Before (ms)': 6838,
			'T After (ms)': 7043,
			'J/ms Before': 0.0263,
			'J/ms After': 0.0268,
		},
	])
	plot_before_after(energy_metrics, out_path='energy_results_plot.png', show=True)

	# Dot graph from the debt-variation summary table
	variation_data = pd.DataFrame([
		{'project': 'apache#commons-csv', 'delta_minutes': 5046.0, 'delta_days': 10.5, 'ratio_low_to_high': 0.21},
		{'project': 'apache#asterixdb', 'delta_minutes': 4457.0, 'delta_days': 9.3, 'ratio_low_to_high': 0.20},
		{'project': 'apache#flink-connector-aws', 'delta_minutes': 4439.0, 'delta_days': 9.2, 'ratio_low_to_high': 0.23},
		{'project': 'apache#apisix-dashboard', 'delta_minutes': 4402.0, 'delta_days': 9.2, 'ratio_low_to_high': 0.20},
		{'project': 'apache#commons-logging', 'delta_minutes': 4193.0, 'delta_days': 8.7, 'ratio_low_to_high': 0.21},
		{'project': 'apache#maven-enforcer', 'delta_minutes': 4187.0, 'delta_days': 8.7, 'ratio_low_to_high': 0.20},
		{'project': 'apache#maven-dependency-plugin', 'delta_minutes': 4149.0, 'delta_days': 8.6, 'ratio_low_to_high': 0.20},
		{'project': 'apache#commons-email', 'delta_minutes': 4035.0, 'delta_days': 8.4, 'ratio_low_to_high': 0.21},
		{'project': 'apache#hertzbeat', 'delta_minutes': 3940.0, 'delta_days': 8.2, 'ratio_low_to_high': 0.20},
		{'project': 'apache#shiro', 'delta_minutes': 3771.0, 'delta_days': 7.9, 'ratio_low_to_high': 0.21},
		{'project': 'apache#uniffle', 'delta_minutes': 3679.0, 'delta_days': 7.7, 'ratio_low_to_high': 0.21},
		{'project': 'apache#rocketmq-dashboard', 'delta_minutes': 3598.0, 'delta_days': 7.5, 'ratio_low_to_high': 0.24},
		{'project': 'apache#flink-connector-jdbc', 'delta_minutes': 3430.0, 'delta_days': 7.1, 'ratio_low_to_high': 0.24},
		{'project': 'apache#flink-kubernetes-operator', 'delta_minutes': 3427.0, 'delta_days': 7.1, 'ratio_low_to_high': 0.23},
		{'project': 'apache#celeborn', 'delta_minutes': 3249.0, 'delta_days': 6.8, 'ratio_low_to_high': 0.24},
		{'project': 'apache#doris-spark-connector', 'delta_minutes': 3206.0, 'delta_days': 6.7, 'ratio_low_to_high': 0.26},
		{'project': 'apache#buildstream', 'delta_minutes': 3129.0, 'delta_days': 6.5, 'ratio_low_to_high': 0.24},
		{'project': 'apache#incubator-kie-kogito-apps', 'delta_minutes': 3096.0, 'delta_days': 6.4, 'ratio_low_to_high': 0.24},
		{'project': 'apache#openwebbeans-meecrowave', 'delta_minutes': 2996.0, 'delta_days': 6.2, 'ratio_low_to_high': 0.34},
		{'project': 'apache#mina-ftpserver', 'delta_minutes': 2826.0, 'delta_days': 5.9, 'ratio_low_to_high': 0.42},
	])
	plot_debt_variation_selected(
		variation_data,
		selected_projects=[
			'apache#commons-csv',
			'apache#commons-email',
			'apache#maven-enforcer',
			'apache#commons-logging',
		],
		out_path='debt_variation_ratio_selected.png',
		show=True,
	)

