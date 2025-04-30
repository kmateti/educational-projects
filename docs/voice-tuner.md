# Voice Tuner

Overall goal: do something where audio is received as input, and some feedback is given visually. One idea is to make a "voice" tuner, and show the user what note they are hitting. Keep it tied to the piano project and use just the key of C to keep it in tune and simple.


### Breaking down the problem 

Assume we use the `pyaudio` to get audio from the user, and we create a visual using Open CV (`cv2`). The basic flow of the application is

```mermaid
    flowchart LR
    A["Get Audio Frames"]
    B["Detect the Dominant Frequency"]
    C["Calculate Delta Frequency to Notes in the Key of C"]
    D["Display Overlay Information to Video Feed"]
    A-->B
    B-->C
    C-->D
```

## Development Setup

### Dependencies
This project uses modern Python packaging with `pyproject.toml` and `uv`. 

```bash
# Install dependencies from lock file
uv sync

# Update lock file (after changing pyproject.toml)
uv lock
```

### Run the Application

```
uv run python src/tuner/main.py
```