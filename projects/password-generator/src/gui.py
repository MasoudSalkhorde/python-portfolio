import streamlit as st
from src.password_classes.random_password import RandomGenerator
from src.password_classes.pin_password import PinGenerator
from src.password_classes.memorable_password import MemorableGenerator

st.title("Welcome to the Password Generator Application!")
st.write("Please select one of these passkey options:")

st.radio(
    "Passkey Type",
    options=["Random", "Pin", "Memorable"],
    key="passkey_type"
)

if st.session_state.passkey_type == "Random":
    char_num = st.number_input("How many characters should be included in your password?", min_value=1, step=1)
    has_num = st.checkbox("Include numbers?")
    has_symbol = st.checkbox("Include symbols?")
    if st.button("Generate Password"):
        passkey = RandomGenerator()
        password = passkey.generate(length=char_num, use_numbers=has_num, use_symbols=has_symbol)
        st.success(f"Your password is: {password}")
        
elif st.session_state.passkey_type == "Pin":
    char_num = st.number_input("How many digits should be included in your PIN?", min_value=1, step=1)
    if st.button("Generate PIN"):
        passkey = PinGenerator()
        password = passkey.generate(length=char_num)
        st.success(f"Your PIN is: {password}")
elif st.session_state.passkey_type == "Memorable":
    word_num = st.number_input("How many words should be included in your password?", min_value=1, step=1)
    has_full_words = st.checkbox("Use full words?")
    
    separator = st.selectbox(
        "Which separator do you want to use?",
        options=["Hyphen", "Underline", "Comma", "Pipe"]
    )
    
    capitalized = st.checkbox("Capitalize each word?")
    
    if st.button("Generate Memorable Password"):
        passkey = MemorableGenerator()
        password = passkey.generate(
            num_words=word_num,
            use_full_words=has_full_words,
            separator=separator,
            capitalized=capitalized
        )
        st.success(f"Your memorable password is: {password}")
    