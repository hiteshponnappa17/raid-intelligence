from pathlib import Path
import joblib,pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score,recall_score,f1_score,confusion_matrix,roc_auc_score
from prediction.feature_engineering import FEATURES
from prediction.synthetic_data import generate_synthetic_dataset
def train_model(df=None,model_path=None,seed=42):
    df=generate_synthetic_dataset() if df is None else df
    missing=set(FEATURES+["failure_label"])-set(df.columns)
    if missing: raise ValueError("Missing columns: "+", ".join(sorted(missing)))
    clean=df[FEATURES+["failure_label"]].replace([float("inf"),float("-inf")],float("nan")).dropna()
    clean=clean[(clean[FEATURES]>=0).all(axis=1)]
    if clean.failure_label.nunique()<2: raise ValueError("Dataset must contain both label classes.")
    X,y=clean[FEATURES],clean.failure_label.astype(int)
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=seed,stratify=y)
    model=RandomForestClassifier(n_estimators=120,class_weight="balanced",random_state=seed,n_jobs=-1).fit(Xtr,ytr)
    pred=model.predict(Xte)
    m={"precision":float(precision_score(yte,pred,zero_division=0)),"recall":float(recall_score(yte,pred,zero_division=0)),"f1":float(f1_score(yte,pred,zero_division=0)),"confusion_matrix":confusion_matrix(yte,pred).tolist(),"train_records":len(Xtr),"test_records":len(Xte),"dataset_records":len(clean),"dataset_source":"Synthetic educational dataset"}
    if yte.nunique()==2: m["roc_auc"]=float(roc_auc_score(yte,model.predict_proba(Xte)[:,1]))
    if model_path: Path(model_path).parent.mkdir(parents=True,exist_ok=True); joblib.dump(model,model_path)
    return model,m
def predict_with_model(model,row):
    X=pd.DataFrame([{k:float(row[k]) for k in FEATURES}],columns=FEATURES)
    return {"label":int(model.predict(X)[0]),"score":float(model.predict_proba(X)[0][1])}
