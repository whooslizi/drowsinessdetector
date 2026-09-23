# Drowsiness Detector

*your eyes get scanned*

A simple python & web app that tracks facial landmarks to check your eyes and predict whether you're sleeping (in class) or not.

## How it works

- Uses MediaPipe Face Mesh to map 468 3D facial landmarks on your face in real time.
- Calculates the Eye Aspect Ratio (EAR) from eye landmark points.
- If your EAR drops below the threshold for too long, it triggers the audio chime and crying baby meme overlay to wake you up.

## Setup

```bash
# 1. install python requirements
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. run python desktop app
python app.py

# 3. or run web UI locally
npm install
npm run dev

# 4. open http://localhost:5173 and enjoy being traumatized!
```

## Deploy

Pushes to the branch automatically build Vite and deploy to GitHub Pages via GitHub Actions (`.github/workflows/deploy.yml`).

## Notes

- This project was made solely for my school project, so it might contain some code that burns your eyes.
