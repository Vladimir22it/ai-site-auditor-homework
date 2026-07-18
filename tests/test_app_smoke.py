import py_compile


def test_streamlit_app_compiles():
    py_compile.compile("streamlit_app.py", doraise=True)
