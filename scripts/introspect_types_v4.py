from google.genai import types
import inspect

for name, obj in inspect.getmembers(types):
    if "Hyper" in name or "Tuning" in name or "Tune" in name:
        if inspect.isclass(obj):
            print(f"CLASS: {name}")
        else:
            print(f"OTHER: {name}")
