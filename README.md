# RealSense Audio Alarm

Project to do something concrete with the Intel RealSense D435i.

Initial idea is to have a fixed D435i, and we detect an object in the scene closer than X, and we beep.

Now, we can extend that idea to detect three people, and based on their distance to the camera, they play a different note. Notes should be in one key, and get higher pitched when coming towards the camera. The basic test could be to have three "columns" extending from the camera to represent three notes. Some visual feedback would show people that they aren't standing in the right spot. Then playing three notes could make chords.

Also using this to learn `uv` python management, see [here](https://docs.astral.sh/uv/concepts/projects/layout/#the-pyprojecttoml).


## Development Setup

### Dependencies
This project uses modern Python packaging with `pyproject.toml` and `uv`. 

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
uv pip install -e .
uv pip install pytest pytest-cov
```

### Testing

First, generate synthetic test data:
```powershell
# Make sure you're in your virtual environment
.\.venv\Scripts\activate

# Generate test data
python -m scripts.generate_test_data
```

Run tests:
```powershell
# Run all tests without GUI
pytest -v

# Run specific tests with GUI visualization
pytest tests/test_bounding_box_detector.py -v --showgui

# Run tests with coverage report
pytest -v --cov=src
```

Test data will be saved to `data/test_sequences/three_sectors.pkl`. This synthetic data simulates three moving objects in different sectors for testing the detection algorithms.

### Git LFS Setup
Large files (like .bag recordings) are managed with Git LFS:

```bash
git lfs install
git lfs track "*.bag"
```

