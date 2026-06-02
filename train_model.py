import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

# Load dataset
data = pd.read_csv("new_file.csv")

# Drop unnecessary columns
data = data.drop(['nameOrig', 'nameDest'], axis=1, errors='ignore')

# Encode 'type'
le = LabelEncoder()
data['type'] = le.fit_transform(data['type'])

# Features & target
X = data.drop('isFraud', axis=1)
y = data['isFraud']

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Save model + encoder
joblib.dump(model, "model.pkl")
joblib.dump(le, "encoder.pkl")

print("✅ Model saved!")