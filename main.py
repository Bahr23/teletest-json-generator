import streamlit as st
from parser_functions import get_test_data

st.title('Test Generator')

url = st.text_input(label='Test url')
channel_id = st.number_input(label='Channel id', step=1, min_value=0, key='channel-id-1')

if url:
    data = get_test_data(url, channel_id)
    st.json(data)
