"""Try one POINTLIGHT with all known prompt variants. Diagnostic."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad

a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)

a.doc.SetVariable("FILEDIA", 0)
a.doc.SetVariable("CMDDIA", 0)
a.doc.SetVariable("EXPERT", 5)
try:
    a.doc.SetVariable("LIGHTINGUNITS", 2)
    print("LIGHTINGUNITS = 2 ok", flush=True)
except Exception as e:
    print(f"LIGHTINGUNITS: {e}", flush=True)

print(f"before: lights = ", end="", flush=True)
# Count Light entities
n_lights = sum(1 for e in a.ms if "Light" in e.ObjectName)
print(n_lights, flush=True)

# Try POINTLIGHT with explicit position + eXit
cmd = "_.POINTLIGHT\n96,108,119\nX\n"
print(f"sending: {cmd!r}", flush=True)
a.send_command(cmd)
time.sleep(2)
idle = a.wait_idle(15)
print(f"idle: {idle}", flush=True)

# Re-count
n_after = sum(1 for e in a.ms if "Light" in e.ObjectName)
print(f"after:  lights = {n_after}", flush=True)
