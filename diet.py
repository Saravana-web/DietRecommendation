import streamlit as st
import pandas as pd
import numpy as np
import pickle

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Diet Recommendation System",
    page_icon="🥗",
    layout="wide"
)

# ------------------ FUNCTIONS ------------------
def calculate_calories(weight, height, age, gender):
    if gender == "Male":
        bmr = 10*weight + 6.25*height - 5*age + 5
    else:
        bmr = 10*weight + 6.25*height - 5*age - 161
    return int(bmr * 1.5)

def get_diet_plan(predicted_diet):
    if "Gain" in predicted_diet:
        return {
            "Breakfast": [
                "🥚 3 boiled eggs / Paneer 120 g",
                "🍌 1 banana",
                "🥛 Milk 300 ml",
                "🌰 Almonds 6–8"
            ],
            "Mid-Morning": [
                "🍎 Apple / Papaya bowl",
                "🥜 Peanut chikki – 1 piece"
            ],
            "Lunch": [
                "🍚 Rice – 2 cups",
                "🥣 Dal / Sambar – 1.5 cups",
                "🍗 Chicken / Paneer – 150 g",
                "🥗 Vegetables – 1 cup",
                "🥛 Curd – 1 cup"
            ],
            "Evening Snack": [
                "🥜 Boiled peanuts – 1 cup",
                "🥤 Fruit smoothie"
            ],
            "Dinner": [
                "🫓 Chapati – 3",
                "🍳 Egg curry / Paneer – 120 g",
                "🥛 Warm milk – 200 ml"
            ]
        }

    elif "Loss" in predicted_diet:
        return {
            "Breakfast": [
                "🥣 Oats – 40 g",
                "🥚 1 boiled egg / Sprouts 1 cup",
                "🍵 Green tea"
            ],
            "Mid-Morning": [
                "🍊 Orange / Apple",
                "🥥 Coconut water"
            ],
            "Lunch": [
                "🍚 Brown rice – 1 cup",
                "🥗 Boiled vegetables – 1.5 cups",
                "🍗 Grilled chicken / Paneer – 100 g",
                "🥣 Dal – 1 cup"
            ],
            "Evening Snack": [
                "🥜 Roasted chana – handful",
                "🍵 Green tea"
            ],
            "Dinner": [
                "🥣 Vegetable soup – 1 bowl",
                "🥗 Fresh salad",
                "🥚 1 boiled egg"
            ]
        }

    else:  # Balanced Diet
        return {
            "Breakfast": [
                "🥞 2 idli / 1 dosa",
                "🥣 Sambar – 1 cup",
                "🍎 1 fruit"
            ],
            "Mid-Morning": [
                "🥛 Buttermilk – 1 glass",
                "🥜 Groundnuts – handful"
            ],
            "Lunch": [
                "🍚 Rice – 1.5 cups",
                "🥣 Dal – 1 cup",
                "🥗 Vegetable curry – 1 cup",
                "🥛 Curd – 1 cup"
            ],
            "Evening Snack": [
                "🍓 Fruit salad",
                "☕ Tea / Coffee (less sugar)"
            ],
            "Dinner": [
                "🫓 Chapati – 2",
                "🥗 Vegetable curry – 1 cup",
                "🥛 Milk – 1 glass"
            ]
        }

# ------------------ HEADER ------------------
st.markdown(
    "<h1 style='text-align:center;'>🥗 Personalized Diet Recommendation System</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:center;'>Get a scientifically suggested diet plan based on your health profile</p>",
    unsafe_allow_html=True
)

# ------------------ LOAD MODEL ------------------
try:
    with open("diet_model.pkl", "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]
    le_gender = saved["le_gender"]
    le_disease = saved["le_disease"]
    le_target = saved["le_target"]
except:
    st.error("❌ Model file not found. Please upload diet_model.pkl")
    st.stop()

# ------------------ SIDEBAR INPUT ------------------
with st.sidebar:
    st.header("🧑 User Details")
    age = st.slider("Age", 18, 90, 30)
    gender = st.selectbox("Gender", le_gender.classes_)
    weight_kg = st.number_input("Weight (kg)", 30.0, 150.0, 60.0, step=0.5)
    height_cm = st.number_input("Height (cm)", 120.0, 220.0, 170.0, step=0.5)
    bmi = st.number_input("BMI", 15.0, 40.0, round(weight_kg / ((height_cm/100)**2), 1))
    disease_type = st.selectbox("Disease Type", le_disease.classes_)
    st.markdown("---")
    submit = st.button("🍽️ Get Diet Recommendation")

# ------------------ PREDICTION ------------------
if submit:
    test_gender = le_gender.transform([gender])[0]
    test_disease = le_disease.transform([disease_type])[0]

    test_X = pd.DataFrame([[
        age, height_cm, weight_kg, bmi, test_gender, test_disease
    ]], columns=["Age", "Height_cm", "Weight_kg", "BMI", "Gender", "Disease_Type"])

    pred_cont = model.predict(test_X)[0]
    pred_class = int(round(pred_cont))
    pred_class = max(0, min(pred_class, len(le_target.classes_) - 1))
    predicted_diet = le_target.inverse_transform([pred_class])[0]

    calories = calculate_calories(weight_kg, height_cm, age, gender)
    diet_plan = get_diet_plan(predicted_diet)

    # ------------------ RESULTS ------------------
    st.markdown("## ✅ Your Diet Recommendation")
    col1, col2, col3 = st.columns(3)
    col1.metric("🍽 Diet Type", predicted_diet)
    col2.metric("🔥 Calories / day", f"{calories} kcal")
    col3.metric("⚖ BMI", bmi)

    st.markdown("## 📅 Detailed Daily Diet Plan")

    for meal, items in diet_plan.items():
        st.markdown(f"### {meal}")
        for food in items:
            st.write("•", food)
