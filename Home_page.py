import streamlit as st  
import pandas as pd
import os

# Define the path to the CSV file used by the Manual Input page
DATA_FILE = "water_quality_data.csv"

# Define safe ranges and friendly descriptions for each parameter
SAFE_RANGES = {
    "pH": {
        "range": (6.5, 8.5),
        "description": "pH indicates the acidity or alkalinity of water. Safe drinking water typically has a pH between 6.5 and 8.5.",
        "health_impact": "Water that is too acidic or too alkaline can cause skin irritation and affect taste."
    },
    "Chlorine (mg/L)": {
        "range": (0, 4),
        "description": "Chlorine is used to disinfect water. Safe levels are below 4 mg/L.",
        "health_impact": "High chlorine levels can cause eye and skin irritation and affect taste."
    },
    "Hardness (mg/L as CaCO3)": {
        "range": (0, 120),
        "description": "Water hardness is caused by dissolved minerals like calcium and magnesium. Ideally, it should be less than 120 mg/L.",
        "health_impact": "Hard water can lead to mineral buildup in pipes and potentially dry out skin."
    },
    "Nitrates (mg/L)": {
        "range": (0, 10),
        "description": "Nitrates in water come from fertilizers and waste. Safe levels are below 10 mg/L.",
        "health_impact": "High nitrate levels can be harmful, especially to infants, causing conditions like 'blue baby syndrome.'"
    },
    "Lead (µg/L)": {
        "range": (0, 15),
        "description": "Lead is a toxic metal, especially dangerous for children. Safe levels are below 15 µg/L.",
        "health_impact": "Exposure to lead can lead to developmental issues in children and health problems in adults."
    }
}

# Helper function to check if a value is within a safe range
def is_within_safe_range(value, min_val, max_val):
    return min_val <= value <= max_val

# Load water quality data from the CSV file
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["Date"])
    return pd.DataFrame(columns=["Zipcode", "Date", "pH", "Chlorine (mg/L)", "Hardness (mg/L as CaCO3)", "Nitrates (mg/L)", "Lead (µg/L)"])

# Set up Streamlit interface
st.title("Water Quality Dashboard for Regular Users")
st.subheader("Understand Your Water Quality and Health Impacts")

# Load data
data = load_data()

# Check if there is data available
if not data.empty:
    # Convert the 'Date' column to datetime format
    data["Date"] = pd.to_datetime(data["Date"])

    # Step 1: Select Zipcode
    st.markdown("### Select Zipcode and Date for Analysis")
    unique_zipcodes = data["Zipcode"].unique()
    selected_zipcode = st.selectbox("Choose a Zipcode to view analysis:", options=unique_zipcodes)

    # Step 2: Select Date
    # Filter data by the selected Zipcode first
    zipcode_data = data[data["Zipcode"] == selected_zipcode]
    available_dates = zipcode_data["Date"].dt.date.unique()
    selected_date = st.selectbox("Choose a Date:", options=available_dates)

    # Step 3: Filter by Date and Zipcode
    selected_data = zipcode_data[zipcode_data["Date"].dt.date == selected_date]

    if not selected_data.empty:
        st.markdown("### Water Quality Measurements on Selected Date and Location")
        
        # Display all entries for the selected Zipcode and Date if there are multiple
        entry_selector = st.selectbox("Select an entry to view details:", options=range(1, len(selected_data) + 1))
        entry_data = selected_data.iloc[entry_selector - 1]  # Select the specific entry

        # Display selected data details
        st.write(f"**Location Zipcode**: {entry_data['Zipcode']}")
        st.write(f"**Date of Measurement**: {entry_data['Date'].date()}")

        # Display each parameter with a user-friendly explanation and health insight
        for param, details in SAFE_RANGES.items():
            st.subheader(param)

            # Current value of the parameter
            current_value = entry_data[param]
            safe_min, safe_max = details["range"]
            in_safe_range = is_within_safe_range(current_value, safe_min, safe_max)

            # Display the current level with color-coded status
            status_icon = "🟢 Safe" if in_safe_range else "🔴 Out of Range"
            st.markdown(f"**Current Level**: {current_value} ({status_icon})")

            # Show description and health impact
            st.write(f"**What it Means**: {details['description']}")
            st.write(f"**Health Impact**: {details['health_impact']}")

            # Visual indicator with progress bar
            st.progress(min(current_value / max(safe_max, current_value), 1.0))

            # Suggest actions if out of safe range
            if not in_safe_range:
                st.warning(f"{param} is out of safe range. Consider using a water filter or consulting local water services.")

        # Display health insights
        st.markdown("### Health Insights")
        st.write("Your water quality looks good overall if all parameters are within safe ranges. "
                 "If any parameters are out of range, consider following the suggestions provided above "
                 "to improve your water quality and protect your health.")
    else:
        st.warning("No data available for the selected date and zipcode. Please try another selection.")
else:
    st.warning("No water quality data available yet. Please use the input page to add data.")

# Footer
st.markdown("---")
st.write("Developed by Orange Team | Powered by Streamlit and OpenAI")
st.write("For inquiries, contact [Your Email Here]")

