import streamlit as st
import pandas as pd
import numpy as np
import pickle

def calculate_calories(weight, height, age, gender):
    if gender == "Male":
        bmr = 10*weight + 6.25*height - 5*age + 5
    else:
        bmr = 10*weight + 6.25*height - 5*age - 161
    return int(bmr * 1.5)

def get_diet_plan(predicted_diet):
    if "Gain" in predicted_diet:
        return (
            "\n🌅 Breakfast: Eggs (3) / Paneer 120g, Banana, Milk 300ml\n" +
            "🍛 Lunch: Rice 2 cups, Dal 1.5 cups, Chicken/Paneer 150g\n" +
            "☕ Snack: Peanuts 1 cup, Fruit juice\n" +
            "🌙 Dinner: Chapati 3, Egg curry / Paneer 120g, Milk"
        )
    elif "Loss" in predicted_diet:
        return (
            "\n🌅 Breakfast: Oats 40g, Boiled egg, Green tea\n" +
            "🍛 Lunch: Brown rice 1 cup, Veggies, Grilled protein 100g\n" +
            "☕ Snack: Roasted chana, Green tea\n" +
            "🌙 Dinner: Vegetable soup, Salad, Boiled egg"
        )
    else:
        return (
            "\n🌅 Breakfast: Idli 2 / Dosa 1, Sambar, Fruit\n" +
            "🍛 Lunch: Rice 1.5 cups, Dal, Veggies, Curd\n" +
            "☕ Snack: Fruit salad, Tea (low sugar)\n" +
            "🌙 Dinner: Chapati 2, Veg curry, Milk"
        )

st.title("Diet Recommendation System")

st.write("Enter your details to get a personalized diet recommendation.")

# Load the saved model and encoders
try:
    with open("diet_model.pkl", "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]
    le_gender = saved["le_gender"]
    le_disease = saved["le_disease"]
    le_target = saved["le_target"]
except FileNotFoundError:
    st.error("Model file 'diet_model.pkl' not found. Please ensure it's in the same directory as the app.")
    st.stop()
except Exception as e:
    st.error(f"Error loading model or encoders: {e}")
    st.stop()

# Input fields
with st.sidebar:
    st.header("User Input")
    age = st.slider("Age", 18, 90, 30)
    gender = st.selectbox("Gender", le_gender.classes_)
    weight_kg = st.number_input("Weight (kg)", 30.0, 150.0, 80.0, step=0.5)
    height_cm = st.number_input("Height (cm)", 100.0, 220.0, 170.0, step=0.5)
    bmi = st.number_input("BMI", 15.0, 40.0, 20.8, step=0.1)
    disease_type = st.selectbox("Disease Type", le_disease.classes_)

if st.button("Get Recommendation"):
    try:
        # Prepare input for prediction
        test_gender = le_gender.transform([gender])[0]

        if disease_type in le_disease.classes_:
            test_disease = le_disease.transform([disease_type])[0]
        else:
            test_disease = 0 # Default to 0 for unseen disease types

        test_X = pd.DataFrame([[
            age,
            height_cm,
            weight_kg,
            bmi,
            test_gender,
            test_disease
        ]], columns=["Age", "Height_cm", "Weight_kg", "BMI", "Gender", "Disease_Type"])

        # Make prediction
        pred_cont = model.predict(test_X)[0]
        pred_class = int(round(pred_cont))

        # Get min and max labels from the target encoder (assuming 'y' used during training refers to these)
        # Note: In a real scenario, you would ensure these min/max are consistent with training labels.
        # For this example, we'll use the available encoder info.
        min_label_idx = 0  # Assuming 0 is the minimum encoded label
        max_label_idx = len(le_target.classes_) - 1 # Assuming max is the last encoded label

        pred_class = max(min(pred_class, max_label_idx), min_label_idx)

        predicted_diet = le_target.inverse_transform([pred_class])[0]

        # Display results
        st.subheader("Your Personalized Recommendation:")
        st.write("**Age:**", age)
        st.write("**Gender:**", gender)
        st.write("**Weight (kg):**", weight_kg)
        st.write("**Height (cm):**", height_cm)
        st.write("**BMI:**", bmi)
        st.write("**Disease Type:**", disease_type)

        st.markdown(f"### 🍽️ Predicted Diet Type: {predicted_diet}")

        # Calculate estimated daily calories
        calories = calculate_calories(weight_kg, height_cm, age, gender)
        st.markdown(f"### 🔥 Estimated Daily Calories: {calories} kcal")

        # Display suggested daily diet plan
        st.markdown("### 📅 Suggested Daily Diet Plan")
        st.write(get_diet_plan(predicted_diet))

    except Exception as e:
        st.error(f"An error occurred during prediction: {e}")
