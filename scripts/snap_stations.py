import sumolib
import pandas as pd

# Load the network (gzip-compressed, sumolib handles this automatically)
net = sumolib.net.readNet('osm.net.xml.gz')

# Load metadata, filter to Cupertino bounding box (same as before)
meta = pd.read_csv('d04_text_meta_2026_04_08.txt', sep='\t')

min_lon, min_lat, max_lon, max_lat = -122.132504, 37.264655, -121.985839, 37.361752
meta_filtered = meta[
    (meta['Longitude'].between(min_lon, max_lon)) &
    (meta['Latitude'].between(min_lat, max_lat))
]

# Load our actual flow data to know which stations we need to snap
flow = pd.read_csv('cupertino_traffic_flow.csv', sep=';')
active_ids = set(flow['Detector'].unique())

# Only snap the stations we actually have flow data for
stations_to_snap = meta_filtered[meta_filtered['ID'].isin(active_ids)]

results = []

for _, row in stations_to_snap.iterrows():
    station_id = row['ID']
    lon, lat = row['Longitude'], row['Latitude']
    x, y = net.convertLonLat2XY(lon, lat)

    edges = net.getNeighboringEdges(x, y, r=500)
    edges.sort(key=lambda e: e[1])

    if edges:
        best_edge, dist = edges[0]
        lane = best_edge.getLanes()[0]
        results.append({
            'Station_ID': station_id,
            'Fwy': row['Fwy'],
            'Dir': row['Dir'],
            'Lane_ID': lane.getID(),
            'Edge_ID': best_edge.getID(),
            'Distance_m': round(dist, 1)
        })
    else:
        results.append({
            'Station_ID': station_id,
            'Fwy': row['Fwy'],
            'Dir': row['Dir'],
            'Lane_ID': None,
            'Edge_ID': None,
            'Distance_m': None
        })

results_df = pd.DataFrame(results)

print(f"Total stations processed: {len(results_df)}")
print(f"Successfully snapped: {results_df['Lane_ID'].notna().sum()}")
print(f"Failed to snap (no nearby edge within 500m): {results_df['Lane_ID'].isna().sum()}")
print()
print(results_df)

failed = results_df[results_df['Lane_ID'].isna()]
print("\nFailed stations - IDs to investigate:")
print(failed[['Station_ID', 'Fwy', 'Dir']])

# Flag unreliable matches (likely wrong edge if too far)
DISTANCE_THRESHOLD = 50  # meters
results_df['Reliable'] = results_df['Distance_m'] < DISTANCE_THRESHOLD

print(f"\nReliable matches (<{DISTANCE_THRESHOLD}m): {results_df['Reliable'].sum()}")
print(f"Unreliable matches (excluding from detectors): {(~results_df['Reliable']).sum()}")
print(results_df[~results_df['Reliable']][['Station_ID', 'Fwy', 'Dir', 'Distance_m']])

# Save only the reliable matches — this is what we'll build detectors.det.xml from
reliable_df = results_df[results_df['Reliable']].copy()
reliable_df.to_csv('station_lane_mapping.csv', index=False)

print(f"\nSaved {len(reliable_df)} reliable station-to-lane mappings to station_lane_mapping.csv")