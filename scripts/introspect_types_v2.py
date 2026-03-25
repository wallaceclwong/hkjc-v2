from google.genai import types
import json

all_types = dir(types)
relevant = [t for t in all_types if "Tune" in t or "Config" in t or "Train" in t or "Dataset" in t]
print("Relevant types:", relevant)
