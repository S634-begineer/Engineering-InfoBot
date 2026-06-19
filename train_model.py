# train_model.py
import pandas as pd #pandas help to work with csv data or excel 
from sklearn.model_selection import train_test_split # use to split the data into 80 percent training and 20 percent testing 
from sklearn.preprocessing import LabelEncoder #This converts text data into numbers. bcoz ml understand or work with numbers 
from sklearn.linear_model import LinearRegression # ml algorithm use to pridict the output 
import pickle # use for once the model is train it store it as a file with extenssion .pkl then there is no need to train again if we work with more data
import os #used to work with file paths 

# Define folder paths
model_folder = "model"
data_folder = "model_data"

# creating folder model for storing pkl file
os.makedirs(model_folder, exist_ok=True)

# Load CSV file (Using the new CSV file name)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR,"model_data", "college_data.csv")
try:
    data = pd.read_csv(data_path)
except FileNotFoundError:
    print(f"FATAL ERROR: CSV file not found at {data_path}.")
    exit()

# Encode text columns for model features and save them
label_encoders = {}
for col in ["City", "Branch", "Eligible_College"]: 
    le = LabelEncoder()
    # Create new encoded columns to keep original text for filtering in app.py
    data[col + '_Encoded'] = le.fit_transform(data[col])
    label_encoders[col] = le

# Features and Target
# Use the NEW encoded columns for features (X)
X = data[["Percentage", "Exam_Score", "City_Encoded", "Branch_Encoded"]] 
# Target (y) must be Quality_Rank for Linear Regression
y = data["Quality_Rank"] 

# here the model is train the data is split into the 80% of traiining and 20% of testing 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)#random_state=42 always ensures the spilts is same 
model = LinearRegression() 
model.fit(X_train, y_train)#trains the model by learning patterns from the training data (X_train, y_train), so that later it can generate new results/predictions for unseen inputs.

# Save model
with open(os.path.join(model_folder, "college_model.pkl"), "wb") as f:
    pickle.dump(model, f)

# Save the Label Encoders (This resolves your FileNotFoundError)
with open(os.path.join(model_folder, "label_encoders.pkl"), "wb") as f:
    pickle.dump(label_encoders, f)


print("✅ Model, Encoders, and Data trained and saved successfully!")