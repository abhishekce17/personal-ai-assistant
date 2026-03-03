
from db.models import ModelUpdate
try:
    m = ModelUpdate(model_name="test")
    print(f"model_name: {m.model_name}")
except Exception as e:
    print(f"Error: {e}")
