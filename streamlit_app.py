import streamlit as st
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Get the customer's name.
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Connect to the active Snowflake session.
session = get_active_session()

# Get the available fruit options.
fruit_df = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"))
    .to_pandas()
)

# Allow the customer to choose up to five ingredients.
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

if ingredients_list:
    # Combine the selected fruits into one string.
    ingredients_string = " ".join(ingredients_list)

    # Prepare the SQL statement.
    my_insert_stmt = """
        INSERT INTO SMOOTHIES.PUBLIC.ORDERS
            (ingredients, name_on_order)
        VALUES (?, ?)
    """

    # Save the order when the customer clicks the button.
    time_to_insert = st.button("Submit Order")

    if time_to_insert:
        session.sql(
            my_insert_stmt,
            params=[ingredients_string, name_on_order]
        ).collect()

        st.success("Your Smoothie is ordered!", icon="✅")
