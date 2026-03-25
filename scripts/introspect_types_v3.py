from google.genai import types
import inspect

for name, obj in inspect.getmembers(types):
    if inspect.isclass(obj):
        if "Tune" in name or "Config" in name or "Dataset" in name:
            print(f"{name}")
