# GLOSA Traffic Engine — Cupertino

I'm building an AI system that tells drivers exactly what speed to hold so they hit every
green light — a "catch the green wave" advisory engine. This repo is the first piece: a
digital twin of Cupertino traffic in SUMO, fed with real Caltrans sensor data, that I'll
eventually use to train a model on how the actuated traffic lights actually behave.

## The Big Picture

**Phase 1 (done):** Get a realistic Cupertino traffic simulation running, using real
sensor data instead of made-up numbers.

**Phase 2 (next):** Use that simulation to learn how the actuated traffic lights change —
when do they turn green based on how much traffic is waiting?

**Phase 3 (later):** Combine that with basic math to tell a driver "slow to 22 mph and
you'll catch the green."

## What's Actually Working Right Now

- Real Cupertino street map pulled from OSM
- Real week of Caltrans (PeMS) sensor data, filtered down to just the Cupertino stretch
  of 280/85
- Sensors matched to actual road lanes in the simulation
- `dfrouter` turning that sensor data into real vehicle routes
- Combined with OSM's background traffic so local streets aren't empty too — freeway AND
  neighborhood traffic both showing up now

## Problems I Ran Into (and how I fixed them)

Keeping this so I don't re-break stuff later.

**1. Data was pulling in San Jose and SF, not just Cupertino**
Filtering by freeway number (280/85) isn't enough — those freeways run through the whole
Bay Area. Fixed by adding a real geographic filter using the map's actual bounding box, so
I only keep sensors that are physically inside Cupertino.

**2. Off-ramp-only data was way too thin**
Started with just off-ramp (`FR`) sensors thinking that was the right signal — only 3
stations existed in my area. Added mainline (`ML`) sensors too, which brought it up to 41
usable stations.

Quick PeMS cheat sheet since this trips me up constantly: `ML` = mainline, `OR` = on-ramp,
`FR` = off-ramp, `FF` = freeway-to-freeway connector.

**3. Some sensors were snapping to the wrong road entirely**
When matching sensor coordinates to actual lanes in the map, a few matched to roads
300m+ away — basically random, not the real location. Fixed by widening the search radius
so nothing failed outright, but throwing out anything that matched more than 50m away as
unreliable. Ended up with 35 solid, trustworthy matches out of 41.

**4. Off-ramp sensors don't report speed**
`dfrouter` needs a speed value for every reading, but PeMS off-ramp sensors only track
vehicle counts, not speed — that's just how Caltrans built them, not a bug on my end. Kept
real speeds where I had them (mainline sensors) and used a placeholder (40 km/h) only for
the sensors that never had speed data to begin with.

**5. dfrouter couldn't find anywhere for cars to start**
I'd set every sensor's type to "between" by default, which left no source for traffic to
originate from. Just removed that setting entirely and let dfrouter figure out
source/sink/between on its own — it's built to do that automatically.

**6. Simulation only showed cars on the freeway, streets were dead**
Real sensor data only covers the freeway and ramps, so that's all that was showing up.
Fixed by loading OSM's own auto-generated background traffic alongside my real data, so
local streets have believable traffic too:
```
sumo-gui --net-file osm.net.xml.gz --route-files osm.passenger.trips.xml \
  --additional-files routes.rou.xml,vehicles.rou.xml
```

## Folder Layout

- `data_pipeline.ipynb` — pulls and filters the raw Caltrans data
- `scripts/` — everything that turns filtered data into an actual SUMO simulation
  (lane snapping, detector files, dfrouter formatting)
- `data/` — the actual data files: filtered flow data, station-to-lane mappings, detector
  definitions, dfrouter outputs

## What's Next

- Pull in on-ramp (`OR`) sensor data too, skipped it this round
- Run the simulation repeatedly and log how traffic buildup relates to when actuated
  lights turn green
- Train a small model on that relationship
- Turn predicted green-light timing into an actual speed recommendation
- Build a simple demo: pick a start and end point on one corridor (De Anza Blvd probably),
  show the recommended speed and a visualization of catching the green wave
