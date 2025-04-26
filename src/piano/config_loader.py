import yaml
from dataclasses import dataclass

@dataclass
class RayConfig:
    azimuth_center: float
    azimuth_span: float
    elevation_center: float
    elevation_span: float

@dataclass
class NoteMapperConfig:
    min_range: float = 0.5
    max_range: float = 3.5
    lowest_note: str = 'C3'
    highest_note: str = 'C4'

@dataclass
class SectorConfig:
    name: str
    color: tuple[int, int, int]
    ray: RayConfig
    note_mapper: NoteMapperConfig

def load_config(config_path: str) -> dict[str, SectorConfig]:
    """
    Load sector configurations from the YAML file.
    Returns a dictionary keyed by sector name.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    sectors_list = config.get('sectors')
    if not sectors_list:
        raise ValueError("No sectors found in configuration.")
    
    sector_configs = {}
    for sec in sectors_list:
        ray_conf = RayConfig(
            azimuth_center=sec['ray']['azimuth_center'],
            azimuth_span=sec['ray']['azimuth_span'],
            elevation_center=sec['ray'].get('elevation_center', 0),
            elevation_span=sec['ray'].get('elevation_span', 0)
        )
        note_mapper_conf = NoteMapperConfig(
            min_range=sec['note_mapper'].get('min_range', 0.5),
            max_range=sec['note_mapper'].get('max_range', 3.5),
            lowest_note=sec['note_mapper'].get('lowest_note', 'C3'),
            highest_note=sec['note_mapper'].get('highest_note', 'C4')
        )
        # Get color from YAML (expects a list of 3 ints) and convert to tuple.
        color = tuple(sec.get('color', [255, 255, 255]))
        sector_configs[sec['name']] = SectorConfig(
            name=sec['name'],
            color=color,
            ray=ray_conf,
            note_mapper=note_mapper_conf
        )
    return sector_configs