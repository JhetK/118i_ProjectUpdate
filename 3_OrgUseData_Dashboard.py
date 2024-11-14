import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import os

# Load data function
DATA_FILE = "water_quality_data.csv"
def load_data():
    if os.path.isfile(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["Date"], dtype={"Zipcode": str})
    return pd.DataFrame(columns=["Zipcode", "Date", "pH", "Chlorine (mg/L)", "Hardness (mg/L as CaCO3)", "Nitrates (mg/L)", "Lead (µg/L)"])

# Define regulatory standards for water quality parameters
REGULATORY_STANDARDS = {
    "pH": (6.5, 8.5),
    "Chlorine (mg/L)": (0, 4),
    "Hardness (mg/L as CaCO3)": (0, 120),
    "Nitrates (mg/L)": (0, 10),
    "Lead (µg/L)": (0, 15)
}

# Load the water quality data
data = load_data()

st.title("Professional Water Quality Dashboard")
st.subheader("Advanced Insights for Water Quality Professionals")

# Display loaded data
st.write("### Loaded Data")
if not data.empty:
    st.dataframe(data)
else:
    st.warning("No data available. Please ensure data is submitted on the input page.")

# Step 1: Filter data by selected parameters
st.markdown("### Step 1: Choose Analysis Parameters")
selected_zipcodes = st.multiselect("Select Zipcodes for Analysis", options=data["Zipcode"].unique())
selected_date_range = st.date_input("Select Date Range", [])

# Filter data based on user input
if selected_zipcodes and selected_date_range:
    filtered_data = data[
        data["Zipcode"].isin(selected_zipcodes) &
        (data["Date"] >= pd.to_datetime(selected_date_range[0])) &
        (data["Date"] <= pd.to_datetime(selected_date_range[1]))
    ]
else:
    filtered_data = data

# Display filtered data in a comparison table
st.markdown("### Step 2: Comparison Table of Selected Data Entries")
if not filtered_data.empty:
    st.dataframe(filtered_data)
else:
    st.warning("No data available for the selected parameters. Please adjust the filters or add data.")

# Step 3: Historical Trends Visualization
st.markdown("### Step 3: Historical Trends by Parameter")
for param, (min_val, max_val) in REGULATORY_STANDARDS.items():
    if param in filtered_data.columns:
        st.subheader(f"{param} Over Time")
        plt.figure(figsize=(10, 4))
        for zipcode in selected_zipcodes:
            zip_data = filtered_data[filtered_data["Zipcode"] == zipcode]
            if not zip_data.empty:
                plt.plot(zip_data["Date"], zip_data[param], marker='o', label=f"Zipcode {zipcode}")
        plt.axhline(y=min_val, color='green', linestyle='--', label=f"Min Standard ({min_val})")
        plt.axhline(y=max_val, color='red', linestyle='--', label=f"Max Standard ({max_val})")
        plt.fill_between(filtered_data["Date"], min_val, max_val, color='lightgreen', alpha=0.3)
        plt.xlabel("Date")
        plt.ylabel(param)
        plt.title(f"{param} Levels Over Time")
        plt.legend()
        st.pyplot(plt)

# Step 4: Compliance Monitoring and Alerts
st.markdown("### Step 4: Compliance Monitoring and Alerts")
for param, (min_val, max_val) in REGULATORY_STANDARDS.items():
    if param in filtered_data.columns:
        non_compliant_data = filtered_data[(filtered_data[param] < min_val) | (filtered_data[param] > max_val)]
        if not non_compliant_data.empty:
            st.warning(f"**{param}** levels out of safe range in {len(non_compliant_data)} entries for selected period and zipcodes.")
            st.write(non_compliant_data[["Zipcode", "Date", param]])
        else:
            st.success(f"All **{param}** values are within the regulatory standards for the selected period.")

# Step 5: Interactive Map for Zipcode-based Analysis
st.markdown("### Step 5: Interactive Map for Zipcode-based Analysis")
map_center = [37.3382, -121.8863]  # Centered on San Jose

# Initialize map
m = folium.Map(location=map_center, zoom_start=12)

# Known coordinates for San Jose zip codes
known_zipcode_coords = {
    "95110": (37.3422, -121.8996),
    "95112": (37.3535, -121.8865),
    "95113": (37.3333, -121.8907),
    "95116": (37.3496, -121.8569),
    "95117": (37.3126, -121.9502),
    "95118": (37.2505, -121.8891),
    "95120": (37.2060, -121.8133)
}

# Add markers for each selected zipcode
for zipcode in selected_zipcodes:
    if zipcode in known_zipcode_coords:
        lat, lon = known_zipcode_coords[zipcode]
        folium.Marker(
            location=[lat, lon],
            popup=f"Zipcode: {zipcode}",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

st_folium(m, width=700, height=500)

# Step 6: Download Filtered Data for Offline Analysis
st.markdown("### Step 6: Download Data for Offline Analysis")
csv_data = filtered_data.to_csv(index=False)
st.download_button(label="Download CSV", data=csv_data, mime="text/csv", file_name="water_quality_filtered_data.csv")

# Footer
st.markdown("---")
st.write("Developed by Orange Team | Powered by Streamlit")
st.write("For inquiries, contact [Your Email Here]")
