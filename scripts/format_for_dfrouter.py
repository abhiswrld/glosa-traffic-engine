import pandas as pd

# Load your existing flow data
df = pd.read_csv('cupertino_traffic_flow.csv', sep=';')

# Only keep detectors that made it into our reliable station-to-lane mapping
mapping = pd.read_csv('station_lane_mapping.csv')
reliable_ids = set(mapping['Station_ID'].unique())
df = df[df['Detector'].isin(reliable_ids)].copy()

# Convert the Time column (raw timestamp strings) into minutes since the
# start of the dataset, which is what dfrouter requires
df['Time'] = pd.to_datetime(df['Time'], format='%m/%d/%Y %H:%M:%S')
start_time = df['Time'].min()
df['Time'] = (df['Time'] - start_time).dt.total_seconds() / 60
df['Time'] = df['Time'].round().astype(int)

# Rename columns to dfrouter's required names
df = df.rename(columns={'Flow': 'qPKW', 'Speed': 'vPKW'})

# vPKW (speed): PeMS only reports real speed for mainline (ML) sensors —
# off-ramp (FR) sensors only report counts, so their speed column is
# genuinely 0/missing at the source, not a bug in our pipeline.
# For FR detectors (speed == 0), substitute a reasonable placeholder:
# 40 km/h (~25 mph), typical for a car slowing down onto a ramp.
# Real ML speeds are kept as-is since we have actual data for those.
df.loc[df['vPKW'] == 0, 'vPKW'] = 40

# Keep only the columns dfrouter needs, in a clean order
df = df[['Detector', 'Time', 'qPKW', 'vPKW']]

df.to_csv('dfrouter_flows.csv', sep=';', index=False)

print(f"Wrote {len(df)} rows to dfrouter_flows.csv")
print(f"Detectors included: {df['Detector'].nunique()}")
print(f"Time range: {df['Time'].min()} to {df['Time'].max()} minutes")
print(df.head())
