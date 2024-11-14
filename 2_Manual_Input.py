import os 
import openai
import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import re

# Initialize OpenAI API Key and OCR Reader
openai.api_key = "API-KEY-HERE"
reader = easyocr.Reader(['en'])

# Define CSV file to store water quality data
DATA_FILE = "water_quality_data.csv"

# Known coordinates for San Jose zip codes as fallback
known_zipcode_coords = {
    "95110": (37.3422, -121.8996),
    "95112": (37.3535, -121.8865),
    "95113": (37.3333, -121.8907),
    "95116": (37.3496, -121.8569),
    "95117": (37.3126, -121.9502),
    "95118": (37.2505, -121.8891),
    "95120": (37.2060, -121.8133),
}

# Helper function to find nearest zipcode based on coordinates
def get_nearest_zipcode(lat, lon):
    min_distance = float("inf")
    nearest_zipcode = None
    for zipcode, coord in known_zipcode_coords.items():
        distance = geodesic((lat, lon), coord).miles
        if distance < min_distance:
            min_distance = distance
            nearest_zipcode = zipcode
    return nearest_zipcode

# Function to get zipcode from coordinates using OpenStreetMap
def get_zipcode_from_coordinates(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "address" in data and "postcode" in data["address"]:
            return data["address"]["postcode"]
        else:
            return get_nearest_zipcode(lat, lon)  # Fallback to nearest known zipcode
    except requests.RequestException as e:
        st.warning(f"Could not connect to OpenStreetMap API: {e}")
        return get_nearest_zipcode(lat, lon)

# Helper functions for loading and saving data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Zipcode", "Date", "pH", "Chlorine (mg/L)", "Hardness (mg/L as CaCO3)", "Nitrates (mg/L)", "Lead (µg/L)"])

def save_data(data):
    data.to_csv(DATA_FILE, index=False)

# Rerun page function
def trigger_rerun():
    if 'refresh' not in st.session_state:
        st.session_state['refresh'] = True
    else:
        st.session_state['refresh'] = not st.session_state['refresh']

# Function to parse extracted text and map to water quality parameters
def parse_extracted_text(text):
    patterns = {
        "pH": r"pH[:\s]*([\d.]+)",
        "Chlorine (mg/L)": r"Chlorine[:\s]*([\d.]+)",
        "Hardness (mg/L as CaCO3)": r"Hardness[:\s]*([\d.]+)",
        "Nitrates (mg/L)": r"Nitrates[:\s]*([\d.]+)",
        "Lead (µg/L)": r"Lead[:\s]*([\d.]+)"
    }
    
    readings = {}
    for param, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            readings[param] = float(match.group(1))
    return readings

# Function to extract text from an image using EasyOCR
def extract_text_from_image(image):
    img = np.array(image)
    results = reader.readtext(img)
    extracted_text = " ".join([text for _, text, _ in results])
    return extracted_text

# Set up Streamlit interface
st.title("Water Quality Dashboard")
st.header("Choose Input Method")

# Step 1: Location Selection with Zipcode Detection
st.markdown("### Step 1: Select Your Location")
st.write("Click on the map to choose your location. We’ll detect the zipcode automatically.")

initial_location = [37.3382, -121.8863]
m = folium.Map(location=initial_location, zoom_start=12)
m.add_child(folium.LatLngPopup())
map_output = st_folium(m)

zipcode = ""
if map_output.get("last_clicked"):
    lat, lon = map_output["last_clicked"]["lat"], map_output["last_clicked"]["lng"]
    zipcode = get_zipcode_from_coordinates(lat, lon)
    if zipcode:
        st.success(f"Detected Zipcode: {zipcode}")
    else:
        st.warning("Could not detect a zipcode for the selected location. Try another point or check the network connection.")

# Confirm zipcode input
zipcode = st.text_input("Confirm Zipcode", value=zipcode, max_chars=5)

# Step 2: Select Input Method for Water Quality Data
input_option = st.radio("Select Input Method:", ("Manual Input", "Image Upload"))

# Collect water quality readings based on selected input method
readings = {}
if input_option == "Manual Input":
    readings = {
        "pH": st.number_input("Enter pH level:", min_value=0.0, max_value=14.0, step=0.1),
        "Chlorine (mg/L)": st.number_input("Enter Chlorine (mg/L):", min_value=0.0, max_value=10.0, step=0.1),
        "Hardness (mg/L as CaCO3)": st.number_input("Enter Hardness (mg/L as CaCO3):", min_value=0.0, max_value=500.0, step=1.0),
        "Nitrates (mg/L)": st.number_input("Enter Nitrates (mg/L):", min_value=0.0, max_value=50.0, step=0.1),
        "Lead (µg/L)": st.number_input("Enter Lead (µg/L):", min_value=0.0, max_value=100.0, step=0.1)
    }
elif input_option == "Image Upload":
    uploaded_file = st.file_uploader("Upload an image of your water test kit results...", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        with st.spinner("Extracting text from the image..."):
            extracted_text = extract_text_from_image(image)
        st.subheader("Extracted Text")
        st.write(extracted_text)
        readings = parse_extracted_text(extracted_text)
        if readings:
            st.success("Data extracted and parsed successfully.")
        else:
            st.error("Failed to parse data. Ensure the image contains readable information.")

# Submit Data button
if st.button("Submit Data"):
    if zipcode and readings:
        data = pd.DataFrame([{**readings, "Zipcode": zipcode, "Date": pd.Timestamp.now()}])
        existing_data = load_data()
        updated_data = pd.concat([existing_data, data], ignore_index=True)
        save_data(updated_data)
        st.success("Data submitted successfully.")
    else:
        st.error("Please ensure all data fields are filled out, including a valid zipcode.")

# Display existing data with Edit and Delete options
st.markdown("### Existing Data")
data = load_data()
if not data.empty:
    for i, row in data.iterrows():
        with st.expander(f"Entry {i+1} - Zipcode: {row['Zipcode']} | Date: {row['Date']}"):
            col1, col2 = st.columns(2)

            # Edit button
            if col1.button("Edit", key=f"edit_{i}"):
                edited_zipcode = st.text_input("Zipcode", value=row["Zipcode"], key=f"zipcode_{i}")
                edited_date = st.date_input("Date", value=pd.to_datetime(row["Date"]), key=f"date_{i}")
                edited_ph = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.1, value=row["pH"], key=f"pH_{i}")
                edited_chlorine = st.number_input("Chlorine (mg/L)", min_value=0.0, max_value=10.0, step=0.1, value=row["Chlorine (mg/L)"], key=f"chlorine_{i}")
                edited_hardness = st.number_input("Hardness (mg/L as CaCO3)", min_value=0.0, max_value=500.0, step=1.0, value=row["Hardness (mg/L as CaCO3)"], key=f"hardness_{i}")
                edited_nitrates = st.number_input("Nitrates (mg/L)", min_value=0.0, max_value=50.0, step=0.1, value=row["Nitrates (mg/L)"], key=f"nitrates_{i}")
                edited_lead = st.number_input("Lead (µg/L)", min_value=0.0, max_value=100.0, step=0.1, value=row["Lead (µg/L)"], key=f"lead_{i}")

                if st.button("Save Changes", key=f"save_{i}"):
                    data.at[i, "Zipcode"] = edited_zipcode
                    data.at[i, "Date"] = edited_date
                    data.at[i, "pH"] = edited_ph
                    data.at[i, "Chlorine (mg/L)"] = edited_chlorine
                    data.at[i, "Hardness (mg/L as CaCO3)"] = edited_hardness
                    data.at[i, "Nitrates (mg/L)"] = edited_nitrates
                    data.at[i, "Lead (µg/L)"] = edited_lead
                    save_data(data)
                    st.success("Entry updated successfully.")
                    trigger_rerun()

            # Delete button
            if col2.button("Delete", key=f"delete_{i}"):
                data = data.drop(i).reset_index(drop=True)
                save_data(data)
                st.success("Entry deleted successfully.")
                trigger_rerun()

else:
    st.write("No data available yet. Add data using the input methods on the main page.")

# Footer
st.markdown("---")
st.write("Developed by Orange Team | Powered by Streamlit")
st.write("For inquiries, contact [Your Email Here]")

