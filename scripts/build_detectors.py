import pandas as pd

df = pd.read_csv('station_lane_mapping.csv')

lines = ['<detectors>']

for _, row in df.iterrows():
    detector_id = row['Station_ID']
    lane_id = row['Lane_ID']
    # type="source" for on-ramps (traffic entering), "sink" for off-ramps (traffic leaving),
    # "between" for mainline stations (traffic just passing through)
    # We'll default everyone to "between" for now — dfrouter can work with this
    # and it's the safest default when we don't have per-station ramp classification

    line = f'    <detectorDefinition id="{detector_id}" lane="{lane_id}" pos="10"/>'
    lines.append(line)

lines.append('</detectors>')

with open('detectors.det.xml', 'w') as f:
    f.write('\n'.join(lines))

print(f"Wrote {len(df)} detector definitions to detectors.det.xml")