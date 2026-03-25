from google.genai import types
if hasattr(types, "CreateTuningJobConfig"):
    print("YES: CreateTuningJobConfig exists")
else:
    print("NO: CreateTuningJobConfig does not exist")
    # Search for something similar
    for t in dir(types):
        if "Create" in t and "Tune" in t:
            print(f"FOUND: {t}")
