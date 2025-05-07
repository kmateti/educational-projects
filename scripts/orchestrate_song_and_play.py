import os
import time
import yaml
import numpy as np

from src.piano.voices import SectorDistanceToNoteMapper, NoteMapperConfig, C_MAJOR_FREQUENCIES
from src.piano.tone_generator import ToneGenerator

bpm = 20  # beats per minute
note_duration = 60 / (bpm * 4)  # Duration of a quarter note in seconds
rest_duration = note_duration * 0.5  # Duration of a rest (half the note duration)

def load_config(config_path: str) -> dict:
    """Load the YAML configuration."""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def get_distance_for_note(note: str, mapper: SectorDistanceToNoteMapper) -> float:
    """
    For the given SectorDistanceToNoteMapper, locate the distance interval assigned to the note.
    Returns the midpoint of the distance interval if found.
    """
    for d_min, d_max, n in mapper.ranges:
        if n == note:
            return (d_min + d_max) / 2.0
    return None

def convert_melody(melody: list, sectors_map: dict) -> list:
    """
    Given a melody (a list of note names) and a mapping of sector names to note mappers,
    return a list of dictionaries where each entry includes the sector name, note, computed distance,
    and target frequency.
    The conversion assigns the note to the first matching sector that covers that note.
    """
    result = []
    for note in melody:
        found = False
        for sector_name, mapper in sectors_map.items():
            distance = get_distance_for_note(note, mapper)
            if distance is not None:
                result.append({
                    "sector": sector_name,
                    "note": note,
                    "distance": distance,
                    "frequency": mapper.get_frequency_from_distance(distance)
                })
                found = True
                break
        if not found:
            result.append({
                "sector": None,
                "note": note,
                "distance": None,
                "frequency": None
            })
    return result

def main():
    # Load configuration from src/piano/config.yaml
    config_path = os.path.join("src", "piano", "config.yaml")
    config = load_config(config_path)
    sectors_list = config.get("sectors")
    if not sectors_list:
        raise ValueError("No sectors found in configuration.")

    # Create a mapping from sector name to its dedicated SectorDistanceToNoteMapper.
    sectors_map = {}
    for sec in sectors_list:
        name = sec["name"]
        mapper_conf = NoteMapperConfig(**sec["note_mapper"])  # Expecting min_range, max_range, lowest_note, highest_note.
        # Create a SectorDistanceToNoteMapper instance for this sector.
        mapper = SectorDistanceToNoteMapper(mapper_conf)
        # The mapper computes its ranges internally.
        sectors_map[name] = mapper

    # Example melody in the key of C (adjust as desired)
    full_scale_melody = [
        "C2", "D2", "E2", "F2", "G2", "A2", "B2", "C3",
        "D3", "E3", "F3", "G3", "A3", "B3", "C4", "D4",
        "E4", "F4", "G4", "A4", "B4", "C5"
    ]

    mary_had_a_little_lamb_melody = [
        "E4", "D4", "C4", "D4", "E4", "E4", "E4", "D4",
        "D4", "D4", "E4", "G4", "G4", "E4", "D4", "C4",
        "D4", "E4", "E4", "E4", "E4", "D4", "D4", "E4",
        "D4", "C4", "C4", "C4"
    ]
    
    count_on_me = [
        # Chorus: "You can count on me like one, two, three"
        'E4', '', 'E4', 'C4', 'E4', 'G4', 'C4', 'B3', 'E4', 'G4', 'B3', '', 'B3',
        # "I'll be there"
        'A3', 'A3'
    ]
    
    melody = count_on_me
    orchestration = convert_melody(melody, sectors_map)
    print("Melody orchestration:")
    for item in orchestration:
        print(f"Sector: {item['sector']}, Note: {item['note']}, Distance: {item['distance']}, Frequency: {item['frequency']}")

    # Create a ToneGenerator instance and start audio output.
    tone_gen = ToneGenerator()
    tone_gen.start()

    
    for item in orchestration:
        freq = item["frequency"]
        if freq is not None:
            # Set the frequency for this note.
            tone_gen.set_frequencies([freq])
            print(f"Playing {item['note']} at {freq:.1f} Hz ({item['distance']:0.2f} m) on {item['sector']}")
            time.sleep(note_duration)
        else:
            # If no mapping is found, silence the tone.
            tone_gen.set_frequencies([])
            print(f"Skipping note {item['note']} (no mapping)")
            time.sleep(rest_duration)
        

    tone_gen.stop()

if __name__ == "__main__":
    main()