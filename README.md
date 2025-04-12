# RealSense Piano

Project to do something concrete with the Intel RealSense D435i.

Initial idea is to have a fixed D435i, and we detect an object in the scene closer than X, and we beep. But what if we extended to have 4 independent channels of sound?

```mermaid
    flowchart LR
    A["Angular Region"]
    B["Measure Distance"]
    C["Distance to Note"]
    D["Play Note"]
    A-->B
    B-->C
    C-->D
```

```mermaid
graph LR
    A["Depth Camera (Outputs Depth Map)"] --> B{"Horizontal Ray Definition (4 Rays)"};

    subgraph "Bass Voice"
        B --> B1["Bass Ray Depth Data"];
        B1 --> C1{"Distance Calculation (Bass)"};
        C1 --> D1["Distance Quantization (5 Bins - Bass)"];
        D1 --> E1{"Bass Note Selection (5 Notes)"};
        E1 --> F["Audio Output"];
    end

    subgraph "Tenor Voice"
        B --> B2["Tenor Ray Depth Data"];
        B2 --> C2{"Distance Calculation (Tenor)"};
        C2 --> D2["Distance Quantization (5 Bins - Tenor)"];
        D2 --> E2{"Tenor Note Selection (5 Notes)"};
        E2 --> F;
    end

    subgraph "Alto Voice"
        B --> B3["Alto Ray Depth Data"];
        B3 --> C3{"Distance Calculation (Alto)"};
        C3 --> D3["Distance Quantization (5 Bins - Alto)"];
        D3 --> E3{"Alto Note Selection (5 Notes)"};
        E3 --> F;
    end

    subgraph "Soprano Voice"
        B --> B4["Soprano Ray Depth Data"];
        B4 --> C4{"Distance Calculation (Soprano)"};
        C4 --> D4["Distance Quantization (5 Bins - Soprano)"];
        D4 --> E4{"Soprano Note Selection (5 Notes)"};
        E4 --> F;
    end
```

```mermaid
graph LR
    A["Depth Camera (Outputs Depth Map)"] --> B{"Horizontal Ray Definition (4 Rays)"};
    B --> B_bass["Bass Ray Depth Data"];
    B_bass --> C_bass{"Distance Calculation (Bass)"};
    C_bass --> D_bass["Distance Quantization (5 Bins - Bass)"];
    D_bass --> E_bass{"Bass Note Selection (5 Notes)"};
    E_bass --> F_bass["Play Bass Tone"];
    F_bass --> G["Audio Output (Combined)"];
```
Also using this to learn `uv` python management, see [here](https://docs.astral.sh/uv/concepts/projects/layout/#the-pyprojecttoml).

## Development Setup

### Dependencies
This project uses modern Python packaging with `pyproject.toml` and `uv`. 

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies with uv
uv pip install -e .
```

To update dependencies:
```powershell
# Update lock file after changing pyproject.toml
uv pip compile pyproject.toml -o uv.lock

# Install from lock file
uv pip sync uv.lock
```

### Testing

First, generate synthetic test data:
```powershell
# Make sure you're in your virtual environment
.\.venv\Scripts\activate

# Generate test data
python -m scripts.generate_test_data
```

Test data will be saved to `data/test_sequences/four_sectors.pkl`. This synthetic data simulates four moving objects in alternating sectors (creating a four-key piano). Each object oscillates between 0.5m and 3.5m with different phases, allowing testing of both position and distance detection.

Run tests:
```powershell
# Run all tests without GUI
pytest -v

# Run specific tests with GUI visualization
pytest tests/test_bounding_box_detector.py -v --showgui

# Run tests with coverage report
pytest -v --cov=src
```


