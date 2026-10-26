from . import build

idx = build()
print("wrote viz3d/scenes/: " + ", ".join(f"{d['id']}({d['scenarios']})" for d in idx))
