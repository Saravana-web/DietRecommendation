import streamlit as st
import pandas as pd
import numpy as np
import pickle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Diet Recommendation System",
    page_icon="🥗",
    layout="wide"
)

# ---------------- FUNCTIONS ----------------
def calculate_calories(weight, height, age, gender):
    if gender == "Male":
        bmr = 10*weight + 6.25*height - 5*age + 5
    else:
        bmr = 10*weight + 6.25*height - 5*age - 161
    return int(bmr * 1.5)

def calculate_macros(weight, diet_type):
    if "Gain" in diet_type:
        return {"Protein (g)": weight*2, "Carbs (g)": 300, "Fat (g)": 70}
    elif "Loss" in diet_type:
        return {"Protein (g)": weight*1.2, "Carbs (g)": 180, "Fat (g)": 50}
    else:
        return {"Protein (g)": weight*1.5, "Carbs (g)": 250, "Fat (g)": 60}

def disease_guidelines(disease):
    data = {
        "Diabetes": {
            "Avoid": ["Sugar", "White rice", "Sweets"],
            "Prefer": ["Whole grains", "Vegetables", "Low-GI fruits"],
            "Tip": "Eat small frequent meals and monitor blood sugar."
        },
        "Hypertension": {
            "Avoid": ["Salt", "Pickles", "Fried food"],
            "Prefer": ["Fruits", "Vegetables", Low-sodium food"],
            "Tip": "Reduce salt intake and manage stress."
        },
        "Heart Disease": {
            "Avoid": ["Red meat", "Butter", "Fast food"],
            "Prefer": ["Oats", "Fish", "Nuts", "Olive oil"],
            "Tip": "Follow a low-fat, high-fiber diet."
        },
        "None": {
            "Avoid": [],
            "Prefer": ["Balanced meals"],
            "Tip": "Maintain active lifestyle."
        }
    }
    return data.get(disease, data["None"])

def get_diet_plan(diet):
    if "Gain" in diet:
        return {
            "Breakfast": ["Eggs 3 / Paneer 120g", "Banana", "Milk 300ml"],
            "Mid-Morning": ["Fruit bowl", "Peanut chikki"],
            "Lunch": ["Rice 2 cups", "Dal", "Chicken/Paneer 150g", "Veggies"],
            "Evening": ["Boiled peanuts", "Smoothie"],
            "Dinner": ["Chapati 3", "Egg curry / Paneer", "Milk"]
        }
    elif "Loss" in diet:
        return {
            "Breakfast": ["Oats", "Boiled egg", "Green tea"],
            "Mid-Morning": ["Apple", "Coconut water"],
            "Lunch": ["Brown rice", "Vegetables", "Grilled protein"],
            "Evening": ["Roasted chana"],
            "Dinner": ["Vegetable soup", "Salad"]
        }
    else:
        return {
            "Breakfast": ["Idli/Dosa", "Sambar", "Fruit"],
            "Mid-Morning": ["Buttermilk", "Nuts"],
            "Lunch": ["Rice", "Dal", "Veg curry", "Curd"],
            "Evening": ["Fruit salad", "Tea"],
            "Dinner": ["Chapati", "Veg curry", "Milk"]
        }

def weekly_diet_plan():
    return {
        "Monday": "Idli, Rice, Veg curry",
        "Tuesday": "Oats, Chapati, Dal",
        "Wednesday": "Dosa, Rice, Sambar",
        "Thursday": "Upma, Brown rice",
        "Friday": "Poha, Paneer",
        "Saturday": "Smoothie, Fish",
        "Sunday": "Light meals"
    }

def generate_pdf(user, diet, calories):
    file = "diet_report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("<b>Personalized Diet Report</b>", styles["Title"]))
    for k, v in user.items():
        content.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    content.append(Paragraph(f"Diet Type: {diet}", styles["Normal"]))
    content.append(Paragraph(f"Calories/day: {calories}", styles["Normal"]))

    doc.build(content)
    return file

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;'>🥗 Personalized Diet Recommendation System</h1>", unsafe_allow_html=True)

# ---------------- LOAD MODEL ----------------
with open("diet_model.pkl", "rb") as f:
    saved = pickle.load(f)

model = saved["model"]
le_gender = saved["le_gender"]
le_disease = saved["le_disease"]
le_target = saved["le_target"]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("🧑 User Details")
    age = st.slider("Age", 18, 90, 30)
    gender = st.selectbox("Gender", le_gender.classes_)
    weight = st.number_input("Weight (kg)", 30.0, 150.0, 60.0)
    height = st.number_input("Height (cm)", 120.0, 220.0, 170.0)
    bmi = round(weight / ((height/100)**2), 1)
    disease = st.selectbox("Disease", le_disease.classes_)
    submit = st.button("🍽 Get Recommendation")

# ---------------- MAIN LOGIC ----------------
if submit:
    X = [[
        age,
        height,
        weight,
        bmi,
        le_gender.transform([gender])[0],
        le_disease.transform([disease])[0]
    ]]

    pred = int(round(model.predict(X)[0]))
    pred = max(0, min(pred, len(le_target.classes_) - 1))
    diet = le_target.inverse_transform([pred])[0]

    calories = calculate_calories(weight, height, age, gender)
    macros = calculate_macros(weight, diet)
    plan = get_diet_plan(diet)
    disease_info = disease_guidelines(disease)

    st.subheader("✅ Recommendation Summary")
    st.metric("Diet Type", diet)
    st.metric("Calories/day", calories)
    st.metric("BMI", bmi)

    st.subheader("📅 Daily Diet Plan")
    for meal, foods in plan.items():
        st.markdown(f"**{meal}**")
        for f in foods:
            st.write("•", f)

    st.subheader("📆 7-Day Diet Plan")
    for day, meal in weekly_diet_plan().items():
        st.write(f"**{day}:** {meal}")

    st.subheader("📊 Macro Nutrients")
    st.bar_chart(pd.DataFrame(macros, index=[0]).T)

    st.subheader("🩺 Disease-Specific Advice")
    st.write("**Avoid:**", ", ".join(disease_info["Avoid"]))
    st.write("**Prefer:**", ", ".join(disease_info["Prefer"]))
    st.write("**Tip:**", disease_info["Tip"])

    st.subheader("🔔 Meal Reminder")
    meal = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner"])
    time = st.time_input("Reminder Time")
    if st.button("Set Reminder"):
        st.success(f"Reminder set for {meal} at {time}")

    st.subheader("📄 Download Diet Report")
    if st.button("Generate PDF"):
        pdf = generate_pdf(
            {"Age": age, "Gender": gender, "Disease": disease},
            diet,
            calories
        )
        with open(pdf, "rb") as f:
            st.download_button("Download PDF", f, file_name="diet_report.pdf")
