import os
import sys
from pathlib import Path
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    uvicorn.run("source_simulator.app:app", host=os.getenv("SIMULATOR_HOST", "127.0.0.1"), port=int(os.getenv("SIMULATOR_PORT", "8099")))
