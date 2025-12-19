# ================== app.py ==================
import streamlit as st
import pandas as pd
import numpy as np
import pickle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Diet Recommendation System",
    page_icon="🥗",
    layout="wide"
)

# ---------------- HELPER FUNCTIONS ----------------

def calculate_calories(weight, height, age, gender, activity_factor=1.5):
    if gender == "Male":
        bmr = 10*weight + 6.25*height - 5*age + 5
    else:
        bmr = 10*weight + 6.25*height - 5*age - 161
    return int(bmr * activity_factor)

def disease_guidelines(disease):
    data = {
        "Diabetes": {
            "Avoid": ["Sugar", "White rice", "Sweets"],
            "Prefer": ["Whole grains", "Vegetables", "Low-GI fruits"],
            "Tip": "Eat small frequent meals and monitor blood sugar."
        },
        "Hypertension": {
            "Avoid": ["Salt", "Pickles", "Fried food"],
            "Prefer": ["Fruits", "Vegetables", "Low-sodium food"],
            "Tip": "Reduce salt intake and manage stress."
        },
        "Heart Disease": {
            "Avoid": ["Red meat", "Butter", "Fast food"],
            "Prefer": ["Oats", "Fish", "Nuts", "Olive oil"],
            "Tip": "Follow a low-fat, high-fiber diet."
        },
        "None": {
            "Avoid": ["Nothing to avoid you're healthy"],
            "Prefer": ["Balanced meals"],
            "Tip": "Maintain active lifestyle."
        }
    }
    return data.get(disease, data["None"])

def get_diet_plan(diet, disease="None"):
    disease_info = disease_guidelines(disease)
    
    if "Gain" in diet:
        plan = {
            "Breakfast": ["Eggs 3 / Paneer 120g", "Banana", "Milk 300ml"],
            "Mid-Morning": ["Fruit bowl", "Peanut chikki"],
            "Lunch": ["Rice 2 cups", "Dal", "Chicken/Paneer 150g", "Veggies"],
            "Evening": ["Boiled peanuts", "Smoothie"],
            "Dinner": ["Chapati 3", "Egg curry / Paneer", "Milk"]
        }
    elif "Loss" in diet:
        plan = {
            "Breakfast": ["Oats", "Boiled egg", "Green tea"],
            "Mid-Morning": ["Apple", "Coconut water"],
            "Lunch": ["Brown rice", "Vegetables", "Grilled protein"],
            "Evening": ["Roasted chana"],
            "Dinner": ["Vegetable soup", "Salad"]
        }
    else:
        plan = {
            "Breakfast": ["Idli/Dosa", "Sambar", "Fruit"],
            "Mid-Morning": ["Buttermilk", "Nuts"],
            "Lunch": ["Rice", "Dal", "Veg curry", "Curd"],
            "Evening": ["Fruit salad", "Tea"],
            "Dinner": ["Chapati", "Veg curry", "Milk"]
        }

    # Remove foods in Avoid list
    for meal, items in plan.items():
        plan[meal] = [item for item in items if not any(av.lower() in item.lower() for av in disease_info["Avoid"])]
    
    return plan

def weekly_diet_plan(diet, disease="None"):
    plan = {
        "Monday": "Idli, Rice, Veg curry",
        "Tuesday": "Oats, Chapati, Dal",
        "Wednesday": "Dosa, Rice, Sambar",
        "Thursday": "Upma, Brown rice",
        "Friday": "Poha, Paneer",
        "Saturday": "Smoothie, Fish",
        "Sunday": "Light meals"
    }
    disease_info = disease_guidelines(disease)
    for day in plan:
        avoid = ", ".join(disease_info["Avoid"])
        prefer = ", ".join(disease_info["Prefer"])
        plan[day] = f"{plan[day]} | Avoid: {avoid}" if avoid else plan[day]
        plan[day] += f" | Prefer: {prefer}"
    return plan

def display_daily_plan(plan):
    st.subheader("📅 Daily Diet Plan")
    cols = st.columns(len(plan))
    for idx, (meal, foods) in enumerate(plan.items()):
        with cols[idx]:
            st.markdown(f"### {meal}")
            for f in foods:
                st.write("•", f)

def generate_pdf(user, diet, calories, daily_plan, weekly_plan):
    file = "diet_report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("<b>Personalized Diet Report</b>", styles["Title"]))
    content.append(Spacer(1, 10))
    for k, v in user.items():
        content.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    content.append(Paragraph(f"Diet Type: {diet}", styles["Normal"]))
    content.append(Paragraph(f"Calories/day: {calories} kcal", styles["Normal"]))
    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Daily Diet Plan:</b>", styles["Heading2"]))
    for meal, foods in daily_plan.items():
        content.append(Paragraph(f"{meal}:", styles["Heading3"]))
        for f in foods:
            content.append(Paragraph(f"• {f}", styles["Normal"]))
    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Weekly Diet Plan:</b>", styles["Heading2"]))
    for day, meal in weekly_plan.items():
        content.append(Paragraph(f"{day}: {meal}", styles["Normal"]))

    doc.build(content)
    return file

# ---------------- LOAD MODEL ----------------
with open("diet_model.pkl", "rb") as f:
    saved = pickle.load(f)
model = saved["model"]
le_gender = saved["le_gender"]
le_disease = saved["le_disease"]
le_target = saved["le_target"]

# ---------------- USER INPUT ----------------
with st.sidebar:
    st.header("🧑 User Details")
    age = st.slider("Age", 18, 90, 30)
    gender = st.selectbox("Gender", le_gender.classes_)
    weight = st.number_input("Weight (kg)", 30.0, 150.0, 70.0)
    height = st.number_input("Height (cm)", 120.0, 220.0, 170.0)
    bmi = round(weight / ((height/100)**2), 1)
    disease = st.selectbox("Disease", le_disease.classes_)

    st.header("🔔 Meal Reminder")
    reminder_meal = st.selectbox("Meal for Reminder", ["Breakfast", "Lunch", "Dinner"])
    reminder_time = st.time_input("Reminder Time", value=datetime.time(8,0))

    submit = st.button("🍽 Get Recommendation")

# ---------------- MAIN LOGIC ----------------
if submit:
    # Prepare input for prediction
    X = [[
        age,
        height,
        weight,
        bmi,
        le_gender.transform([gender])[0],
        le_disease.transform([disease])[0]
    ]]
    pred = int(round(model.predict(X)[0]))
    pred = max(0, min(pred, len(le_target.classes_)-1))
    diet_type = le_target.inverse_transform([pred])[0]

    calories = calculate_calories(weight, height, age, gender)

    st.set_page_config(
    page_title="Diet Recommendation System",
    page_icon="🥗",
    layout="wide"
    )

    # Display metrics
    st.metric("🔥 Estimated Daily Calories", f"{calories} kcal")
    st.metric("⚖ BMI", bmi)

    # Display daily & weekly diet
    daily_plan = get_diet_plan(diet_type, disease)
    display_daily_plan(daily_plan)

    weekly_plan = weekly_diet_plan(diet_type, disease)
    st.subheader("📆 Weekly Diet Plan")
    weekly_df = pd.DataFrame(list(weekly_plan.items()), columns=["Day", "Plan"])
    st.dataframe(weekly_df, use_container_width=True)

    # Macro nutrient chart
    st.subheader("📊 Macro Nutrients")
    macros = {
        "Protein (g)": weight*1.5 if "Loss" not in diet_type else weight*1.2,
        "Carbs (g)": 250 if "Loss" not in diet_type else 180,
        "Fat (g)": 60 if "Loss" not in diet_type else 50
    }
    st.bar_chart(pd.DataFrame(macros, index=[0]).T)

    # Disease-specific advice
    st.subheader("🩺 Disease-Specific Advice")
    info = disease_guidelines(disease)
    st.write("**Avoid:**", ", ".join(info["Avoid"]))
    st.write("**Prefer:**", ", ".join(info["Prefer"]))
    st.write("**Tip:**", info["Tip"])

    # PDF download
    st.subheader("📄 Download Diet Report")
    pdf_file = generate_pdf(
        {"Age": age, "Gender": gender, "Weight": weight, "Height": height, "BMI": bmi, "Disease": disease},
        diet_type, calories, daily_plan, weekly_plan
    )
    with open(pdf_file, "rb") as f:
        st.download_button("Download PDF", f, file_name="diet_report.pdf")

    # Reminder display (demo)
    st.subheader("🔔 Meal Reminder Status")
    now = datetime.datetime.now()
    reminder_dt = datetime.datetime.combine(now.date(), reminder_time)
    if reminder_dt < now:
        reminder_dt += datetime.timedelta(days=1)
    st.info(f"Reminder set for {reminder_meal} at {reminder_dt.strftime('%H:%M')}")

    if st.button(f"Trigger {reminder_meal} Reminder Now"):
        st.success(f"🔔 Time to have your {reminder_meal}!")
