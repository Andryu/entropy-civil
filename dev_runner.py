import subprocess
import time
import sys
import os

def run_backend():
    print("Starting FastAPI Backend (Port 8002)...")
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"], cwd="backend")

def run_simulation():
    print("Starting Simulation Engine...")
    return subprocess.Popen([sys.executable, "simulation.py"], cwd="backend")

if __name__ == "__main__":
    # Check if we are in the root
    if not os.path.exists("backend"):
        print("Please run this from the project root.")
        sys.exit(1)

    backend_proc = run_backend()
    time.sleep(2) # Wait for DB init in main.py
    sim_proc = run_simulation()

    try:
        while True:
            if backend_proc.poll() is not None:
                print("Backend crashed. Restarting...")
                backend_proc = run_backend()
            if sim_proc.poll() is not None:
                print("Simulation finished/crashed. Restarting...")
                sim_proc = run_simulation()
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping services...")
        backend_proc.terminate()
        sim_proc.terminate()
