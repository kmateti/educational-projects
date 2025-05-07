import yaml
import pandas as pd
from src.piano.voices import SectorDistanceToNoteMapper, NoteMapperConfig

def main():
    # Load config
    with open("src/piano/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    rows = []
    for sector in config["sectors"]:
        sector_name = sector["name"]
        mapper = SectorDistanceToNoteMapper(NoteMapperConfig(**sector["note_mapper"]))
        for d_min, d_max, note in mapper.ranges:
            # Round meters to cm precision and convert to feet
            d_min_m = round(d_min, 2)
            d_max_m = round(d_max, 2)
            d_min_ft = round(d_min * 3.28084, 2)
            d_max_ft = round(d_max * 3.28084, 2)
            rows.append({
                "sector": sector_name,
                "note": note,
                "distance_min_m": d_min_m,
                "distance_min_ft": d_min_ft,
                "distance_max_m": d_max_m,
                "distance_max_ft": d_max_ft
            })

    # Write to CSV using pandas
    df = pd.DataFrame(rows)
    df.to_csv("note_distance_table.csv", index=False)

    # Build the converter table
    def format_range(row):
        return f"{row['note']}: {row['distance_min_ft']} - {row['distance_max_ft']}"

    df['range'] = df.apply(format_range, axis=1)

    # Pivot: index is a dummy (range(len)), columns=sector, values=range
    pivot = df.pivot(columns='sector', values='range')

    # Optional: ensure column order
    pivot = pivot[['Bass', 'Tenor', 'Alto', 'Soprano']]

    # Write to CSV
    pivot.to_csv("sector_distance_table.csv", index=False)

if __name__ == "__main__":
    main()