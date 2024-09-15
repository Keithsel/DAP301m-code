import streamlit as st
from streamlit_navigation_bar import st_navbar
import streamlit.components.v1 as components
import pickle
import numpy as np

def map_catalog():
    st.title("Map Catalog")
    st.write("Look for houses in the area.")
    
    map_type = st.selectbox("Select map type", ["Houses and info", "Choropleth map"])

    if map_type == "Houses and info":
        with open("Lab_1/media/housing_map.html") as f:
            body = f.read()
        components.html(body, height=850)
    else:
        with open("Lab_1/media/choropleth.html") as f:
            body = f.read()
        components.html(body, height=850)

def predict_price():
    st.title("House Price Prediction")
    st.write("Predict the price of a house.")

    with open("Lab_1/ridge_poly_model.pkl", "rb") as f:
        model = pickle.load(f)

    bedrooms = st.number_input("Number of Bedrooms", step=1)
    bathrooms = st.number_input("Number of Bathrooms", value=2)

    sqft_lot = st.text_input("Lot Size in Square Feet", value="5000.45")
    sqft_above = st.text_input("Above Ground Square Feet", value="2000.55")
    sqft_basement = st.text_input("Basement Square Feet", value="500.0")
    sqft_living15 = st.text_input("Average living space of the 15 nearest neighbors", value="1500.0")
    sqft_lot15 = st.text_input("Average lot size of the 15 nearest neighbors", value="5000.0")

    try:
        sqft_lot = float(sqft_lot)
        sqft_above = float(sqft_above)
        sqft_basement = float(sqft_basement)
        sqft_living15 = float(sqft_living15)
        sqft_lot15 = float(sqft_lot15)
    except ValueError:
        st.error("Please enter valid numeric values.")

    floors = st.number_input("Number of Floors", min_value=1.0, value=2.0, step=0.5)
    waterfront = st.selectbox("Waterfront (1 for Yes, 0 for No)", options=[0, 1], index=0)
    view = st.slider("View Score", min_value=0, max_value=4, value=2)
    grade = st.slider("Grade", min_value=1, max_value=13, value=7)
    yr_built = st.number_input("Year Built", max_value=2024, value=1990, step=1)
    yr_renovated = st.number_input("Year Renovated (0 if never renovated)", min_value=0, max_value=2024, value=0, step=1)

    if st.button("Predict House Price"):
        input_data = np.array([[bedrooms, bathrooms, sqft_lot, floors, waterfront, view, grade,
                                sqft_above, sqft_basement, yr_built, yr_renovated, sqft_living15, sqft_lot15]])

        predicted_price = model.predict(input_data)[0]

        st.success(f"The predicted house price is ${predicted_price:,.2f}")

def main():
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

    logo = "Lab_1/media/logo.svg"

    style = {
        "nav": {
            "justify-content": "left",
        },
        "img": {
            "padding-right": "14px",
        },
        "span": {
            "color": "white",
            "padding": "14px",
        },
        "active": {
            "background-color": "#DD5746",
            "color": "white",
            "font-weight": "semibold",
            "padding": "14px",
        },
        "hover": {
            "background-color": "white",
            "color": "black",
            "font-weight": "normal",
            "padding": "14px",
        },
        "ul": {
            "justify-content": "flex-start",
        }
    }
    pages = ["Map", "House Price Prediction"]

    page = st_navbar(
        pages,
        selected=pages[0],
        logo_path=logo,
        styles=style
    )
    
    if page == "Map":
        map_catalog()
    elif page == "House Price Prediction":
        predict_price()

if __name__ == "__main__":
    main()