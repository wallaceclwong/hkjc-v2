from google.genai import types
config = types.CreateTuningJobConfig()
attrs = [a for a in dir(config) if not a.startswith("_") and a[0].islower()]
print("Relevant attributes:", attrs)
