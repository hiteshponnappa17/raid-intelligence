from config.settings import MODEL_DIR
from prediction.ml_model import train_model
_,metrics=train_model(model_path=MODEL_DIR/"raid_rf.joblib")
print(metrics)
