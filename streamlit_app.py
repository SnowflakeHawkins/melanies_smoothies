import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from snowflake.snowpark.functions import col


st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Get the customer's name.
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Connect to Snowflake.
cnx = st.connection("snowflake")
session = cnx.session()

# Get the display names and API search values.
fruit_df = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"), col("SEARCH_ON"))
    .to_pandas()
)

# Show friendly fruit names in the selection box.
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

if ingredients_list:
    # Store the selected display names with the order.
    ingredients_string = " ".join(ingredients_list)

    # Load nutrition information for each selected fruit.
    for fruit_chosen in ingredients_list:
        st.subheader(f"{fruit_chosen} Nutrition Information")

        # Find the API search value for this fruit.
        search_on = fruit_df.loc[
            fruit_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        # Skip requests when SEARCH_ON has not been filled in.
        if pd.isna(search_on) or not str(search_on).strip():
            st.warning(
                f"SEARCH_ON is missing for {fruit_chosen}. "
                "Update this fruit in your Snowflake FRUIT_OPTIONS table."
            )
            continue

        fruit_api_name = quote(str(search_on).strip(), safe="")
        fruit_url = (
            f"https://my.smoothiefroot.com/api/fruit/{fruit_api_name}"
        )

        try:
            response = requests.get(fruit_url, timeout=30)
            response.raise_for_status()
            nutrition_data = response.json()

        except requests.exceptions.RequestException as error:
            st.warning(
                f"Could not load nutrition information for {fruit_chosen}."
            )
            st.code(str(error))

        except ValueError:
            st.warning(
                f"The nutrition service did not return valid JSON "
                f"for {fruit_chosen}."
            )

        else:
            nutrition_df = pd.json_normalize(nutrition_data)

            if nutrition_df.empty:
                st.warning(
                    f"No nutrition information was returned "
                    f"for {fruit_chosen}."
                )
            else:
                st.dataframe(
                    nutrition_df,
                    width="stretch",
                    hide_index=True
                )

    # Prepare the order statement.
    my_insert_stmt = """
        INSERT INTO SMOOTHIES.PUBLIC.ORDERS
            (ingredients, name_on_order)
        VALUES (?, ?)
    """

    # Save the order only when the button is clicked.
    if st.button("Submit Order"):
        if not name_on_order.strip():
            st.warning("Please enter a name for your smoothie.")
        else:
            session.sql(
                my_insert_stmt,
                params=[
                    ingredients_string,
                    name_on_order.strip()
                ]
            ).collect()

            st.success("Your Smoothie is ordered!", icon="✅")

else:
    st.info("Select at least one fruit to customize your smoothie.")
