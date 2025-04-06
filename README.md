# RealSense Audio Alarm

Project to do something concrete with the Intel RealSense D435i.

Initial idea is to have a fixed D435i, and we detect an object in the scene closer than X, and we beep.

Now, we can extend that idea to detect three people, and based on their distance to the camera, they play a different note. Notes should be in one key, and get higher pitched when coming towards the camera. The basic test could be to have three "columns" extending from the camera to represent three notes. Some visual feedback would show people that they aren't standing in the right spot. Then playing three notes could make chords.

Also using this to learn `uv` python management, see [here](https://docs.astral.sh/uv/concepts/projects/layout/#the-pyprojecttoml).


## Development Setup

### Dependencies
This project uses modern Python packaging with `pyproject.toml` and `uv`. 

```bash
# Install dependencies from lock file
uv pip install -r requirements.lock

# Update lock file (after changing pyproject.toml)
uv pip compile pyproject.toml -o requirements.lock
```

### Git LFS Setup
Large files (like .bag recordings) are managed with Git LFS:

```bash
git lfs install
git lfs track "*.bag"
```

