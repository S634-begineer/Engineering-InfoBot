from flask import Flask, request, jsonify, send_from_directory #flask connects frontend to the backend, request used to receive input from frontend, jsonify Used to send JSON data back to your frontend. 
from flask_cors import CORS #CORS (Cross-Origin Resource Sharing).
import pickle #used to load train  model
import pandas as pd #
# import numpy as np
from openai import OpenAI #Used to generate AI messages using OpenAI API.
import os # in this Used to access environment variables (secret keys).
import traceback

app = Flask(__name__)#creates main flask application object 
CORS(app) #allows frontend JavaScript to communicate with Flask.

# Paths
base_dir = os.path.dirname(__file__)
model_dir = os.path.join(base_dir, "..", "model")
data_dir = os.path.join(base_dir, "..", "model_data")

model_path = os.path.join(model_dir, "college_model.pkl")
#  Load encoders from the correct file
encoders_path = os.path.join(model_dir, "label_encoders.pkl")
#  CSV path to use the final, larger dataset name
data_path = os.path.join(data_dir, "college_data.csv")

# --- Load Data, Model, and Encoders ---
try:
    data = pd.read_csv(data_path)
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(encoders_path, "rb") as f:
        label_encoders = pickle.load(f)

    print("✅ Model, Encoders, and Data loaded successfully!")

except Exception as e:
    print(f"FATAL ERROR loading essential files: {e}")
    traceback.print_exc()

# OpenAI setup
api_key = "YOUR_API_KEY"
client = OpenAI(api_key=api_key)

# Branch normalization
BRANCH_MAP = {
    "cse": "Computer", "computer science": "Computer", "computer": "Computer",
    "it": "IT", "information technology": "IT",
    "mech": "Mechanical", "mechanical": "Mechanical",
    "electrical": "Electrical", "civil": "Civil"
}

# Helper function to format the college output
# Added rank and simplified output for better compatibility
def format_college_output(college_name, branch, url, dept_info, rank):
    """Creates an HTML-formatted string for the college details, including the predicted rank."""
    return f'<a href="{url}" target="_blank">**{college_name}**</a> (Predicted Rank: {rank:.2f}) <br> <span style="font-size: 0.9em; color: #555;">{branch}: {dept_info}</span>'

# @app.route("/")
# def home():
#     return send_from_directory("../Frontend", "index.html")
# @app.route("/<path:path>")
# def frontend_files(path):
#     return send_from_directory("..Frontend", path)

@app.route("/predict", methods=["POST"]) #Run this function whenever the frontend sends data to /predict using POST.
def predict():
    try:
        user_data = request.get_json()#takes user json data from js 
        
        city = user_data.get("city", "").strip().title()#strip removes unwanted spaces like trim()
        branch_input = user_data.get("branch", "").strip().lower()
        branch = BRANCH_MAP.get(branch_input, branch_input.title())#BRANCH_MAP is used to standardize different user inputs for the same branch.
        percentage = float(user_data.get("percentage", 0))
        exam_score = float(user_data.get("exam_score", 0))

        if not city or not branch or percentage == 0:
            return jsonify({"college": "Incomplete details", "ai_message": "Please fill all required details."})

        # VALIDATION AND ENCODING ---
        if city not in label_encoders["City"].classes_:
            return jsonify({"college": f"City '{city}' not found in dataset. Try a major city.", "ai_message": ""})
        if branch not in label_encoders["Branch"].classes_:
            return jsonify({"college": f"Branch '{branch}' not found in dataset.", "ai_message": ""})

        # Encode user inputs (using the encoders saved in train_model.py)
        city_encoded = label_encoders["City"].transform([city])[0]
        branch_encoded = label_encoders["Branch"].transform([branch])[0]
        
        # FILTERING (Based on City and Branch Text) 
        # Filter using the original text columns from the DataFrame 'data'
        eligible_df = data[
            (data["City"] == city) & (data["Branch"] == branch)
        ].copy() 
        
        if eligible_df.empty:
            return jsonify({
                "college": "No colleges found for this city and branch.",
                "ai_message": "Try checking a different city or branch."
            })
            
        #  PREDICT RANK FOR EACH ELIGIBLE COLLEGE
        
        # 1. Prepare user input features for prediction
        user_features = {
            "Percentage": percentage,
            "Exam_Score": exam_score,
            "City_Encoded": city_encoded,
            "Branch_Encoded": branch_encoded
        }
        
        # Create input DataFrame for the model
        num_eligible = len(eligible_df)
        user_input_df = pd.DataFrame([user_features] * num_eligible)
        
        # Select the features the model was trained on
        X_model_input = user_input_df[["Percentage", "Exam_Score", "City_Encoded", "Branch_Encoded"]]

        # Predict the Quality_Rank
        predicted_ranks = model.predict(X_model_input)
        
        # Add the predicted rank back to the DataFrame for sorting
        eligible_df["Predicted_Rank"] = predicted_ranks
        
        # Sort colleges by the predicted rank 
        ranked_colleges = eligible_df.sort_values(by="Predicted_Rank", ascending=False)
        
        #  FORMATTING OUTPUT
        college_with_details = []
        for index, row in ranked_colleges.iterrows():
            formatted_detail = format_college_output(
                college_name=row["Eligible_College"],
                branch=row["Branch"],
                url=row["URL"],
                dept_info=row["Dept_Info"],
                rank=row["Predicted_Rank"]
            )
            college_with_details.append(formatted_detail)

        # AI MESSAGE 
        ai_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful college admission assistant."},
                {"role": "user", "content": (
                    f"A student from {city} scored {percentage}% and exam score {exam_score} in {branch}. "
                    f"The top college predicted is {ranked_colleges.iloc[0]['Eligible_College']}. Add a short encouraging message."
                )}
            ]
        )

        gpt_reply = ai_response.choices[0].message.content #full api response
        #send everything back to frontend
        return jsonify({
            "college": college_with_details, 
            "ai_message": gpt_reply
        })

    except Exception as e:
        print("\n Full error traceback:")
        traceback.print_exc()
        return jsonify({"college": f"Error occurred: {str(e)}", "ai_message": ""})

if __name__ == "__main__":
    print("🚀 Flask server running at http://127.0.0.1:5000")
    app.run(debug=True)