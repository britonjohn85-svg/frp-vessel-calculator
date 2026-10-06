import streamlit as st

st.title("Testing Libraries")

# Test pandas
try:
    import pandas as pd
    st.success("Pandas is working! Version: " + pd.__version__)
except Exception as e:
    st.error("Pandas error: " + str(e))

# Test matplotlib
try:
    import matplotlib.pyplot as plt
    st.success("Matplotlib is working!")
except Exception as e:
    st.error("Matplotlib error: " + str(e))

# Test matplotlib figure in streamlit
try:
    fig, ax = plt.subplots()
    ax.bar(["A", "B", "C"], [1, 2, 3])
    st.pyplot(fig)
    st.success("Chart rendered successfully!")
except Exception as e:
    st.error("Chart error: " + str(e))