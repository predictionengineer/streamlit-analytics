from typing import Union
from contextlib import contextmanager
from pathlib import Path
import json

import streamlit as st

from . import session_state


# Dict that holds all analytics results. Note that this is persistent across users,
# as modules are only imported once by a streamlit app.
counts = {"pageviews": 0, "script_runs": 0, "widgets": {}}

# Store original streamlit functions. They will be monkey-patched with some wrappers
# in `start_tracking` (see wrapper functions below).
_orig_button = st.button
_orig_checkbox = st.checkbox
_orig_radio = st.radio
_orig_selectbox = st.selectbox
_orig_multiselect = st.multiselect
_orig_slider = st.slider
_orig_select_slider = st.select_slider
_orig_text_input = st.text_input
_orig_number_input = st.number_input
_orig_text_area = st.text_area
_orig_date_input = st.date_input
_orig_time_input = st.time_input
_orig_file_uploader = st.file_uploader


def _track_user():
    """Track individual pageviews by storing user id to session state."""
    counts["script_runs"] += 1
    sess = session_state.get(user_tracked=False)
    if not sess.user_tracked:
        sess.user_tracked = True
        counts["pageviews"] += 1
        # print("Tracked new user")


def _button_wrapper(label, *args, **kwargs):
    clicked = _orig_button(label, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = 0
    if clicked:
        counts["widgets"][label] += 1
    # if verbose:
    #     print(f"Tracked button '{label}' -> clicked: {clicked}")
    return clicked


def _checkbox_wrapper(label, *args, **kwargs):
    checked = _orig_checkbox(label, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = 0
    if checked:
        counts["widgets"][label] += 1
    return checked


def _radio_wrapper(label, options, *args, **kwargs):
    selected = _orig_radio(label, options, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    for option in options:
        if option not in counts["widgets"][label]:
            counts["widgets"][label][option] = 0
    counts["widgets"][label][selected] += 1
    return selected


def _selectbox_wrapper(label, options, *args, **kwargs):
    selected = _orig_selectbox(label, options, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    for option in options:
        if option not in counts["widgets"][label]:
            counts["widgets"][label][option] = 0
    counts["widgets"][label][selected] += 1
    # if verbose:
    #     print(f"Tracked selectbox '{label}' -> selected: {selected}")
    return selected


def _multiselect_wrapper(label, options, *args, **kwargs):
    selected = _orig_multiselect(label, options, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    for option in options:
        if option not in counts["widgets"][label]:
            counts["widgets"][label][option] = 0
    for sel in selected:
        counts["widgets"][label][sel] += 1
    return selected


# TODO: Maybe do more of a histogram thing here.
def _slider_wrapper(label, *args, **kwargs):
    number = _orig_slider(label, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    if number not in counts["widgets"][label]:
        counts["widgets"][label][number] = 0
    counts["widgets"][label][number] += 1


def _select_slider_wrapper(label, options, *args, **kwargs):
    selected = _orig_select_slider(label, options, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    for option in options:
        if option not in counts["widgets"][label]:
            counts["widgets"][label][option] = 0
    counts["widgets"][label][selected] += 1
    # if verbose:
    #     print(f"Tracked selectbox '{label}' -> selected: {selected}")
    return selected


def _text_input_wrapper(label, *args, **kwargs):
    text = _orig_text_input(label, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    if text not in counts["widgets"][label]:
        counts["widgets"][label][text] = 0
    counts["widgets"][label][text] += 1


def _number_input_wrapper(label, *args, **kwargs):
    number = _orig_number_input(label, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    if number not in counts["widgets"][label]:
        counts["widgets"][label][number] = 0
    counts["widgets"][label][number] += 1


def _text_area_wrapper(label, *args, **kwargs):
    text = _orig_text_area(label, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    if text not in counts["widgets"][label]:
        counts["widgets"][label][text] = 0
    counts["widgets"][label][text] += 1


def _date_input_wrapper(label, *args, **kwargs):
    date = _orig_date_input(label, *args, **kwargs)
    date = str(date)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    if date not in counts["widgets"][label]:
        counts["widgets"][label][date] = 0
    counts["widgets"][label][date] += 1


def _time_input_wrapper(label, *args, **kwargs):
    time = _orig_time_input(label, *args, **kwargs)
    time = str(time)
    if label not in counts["widgets"]:
        counts["widgets"][label] = {}
    if time not in counts["widgets"][label]:
        counts["widgets"][label][time] = 0
    counts["widgets"][label][time] += 1


def _file_uploader_wrapper(label, *args, **kwargs):
    uploaded_file = _orig_file_uploader(label, *args, **kwargs)
    if label not in counts["widgets"]:
        counts["widgets"][label] = 0
    if uploaded_file is not None:
        counts["widgets"][label] += 1
    return uploaded_file


def start_tracking(verbose: bool = False):
    """
    Start tracking user inputs to a streamlit app.
    
    If you call this function directly, you NEED to call 
    `streamlit_analytics.stop_tracking()` at the end of your streamlit script.
    For a more convenient interface, wrap your streamlit calls in 
    `with streamlit_analytics.track():`. 
    """

    _track_user()

    # Monkey-patch streamlit to call the wrappers above.
    st.button = _button_wrapper
    st.checkbox = _checkbox_wrapper
    st.radio = _radio_wrapper
    st.selectbox = _selectbox_wrapper
    st.multiselect = _multiselect_wrapper
    st.slider = _slider_wrapper
    st.select_slider = _select_slider_wrapper
    st.text_input = _text_input_wrapper
    st.number_input = _number_input_wrapper
    st.text_area = _text_area_wrapper
    st.date_input = _date_input_wrapper
    st.time_input = _time_input_wrapper
    st.file_uploader = _file_uploader_wrapper

    if verbose:
        print()
        print("Tracking script execution with streamlit-analytics...")


def stop_tracking(
    unsafe_password: str = None,
    save_to_json: Union[str, Path] = None,
    verbose: bool = False,
):
    """
    Stop tracking user inputs to a streamlit app.
    
    Should be called after `streamlit-analytics.start_tracking()`. This method also
    shows the analytics results below your app if you attach `?analytics=on` to the URL.
    """
    if verbose:
        print("Finished script execution. New counts:")
        print(counts)
        print("-" * 80)

    # Reset streamlit functions.
    st.button = _orig_button
    st.checkbox = _orig_checkbox
    st.radio = _orig_radio
    st.selectbox = _orig_selectbox
    st.multiselect = _orig_multiselect
    st.slider = _orig_slider
    st.select_slider = _orig_select_slider
    st.text_input = _orig_text_input
    st.number_input = _orig_number_input
    st.text_area = _orig_text_area
    st.date_input = _orig_date_input
    st.time_input = _orig_time_input
    st.file_uploader = _orig_file_uploader

    # Dump the counts to json file if `save_to_json` is set.
    # TODO: Make sure this is not locked if writing from multiple threads.
    if save_to_json is not None:
        with Path(save_to_json).open("w") as f:
            json.dump(counts, f)
        if verbose:
            print("Storing results to file:", save_to_json)

    # Show analytics results in the streamlit app if `?analytics=on` is set in the URL.
    query_params = st.experimental_get_query_params()
    if "analytics" in query_params and "on" in query_params["analytics"]:
        st.write("---")
        st.title("Analytics")
        st.markdown(
            """
            Psst! 👀 You found a secret section generated by 
            [streamlit-analytics](https://github.com/jrieke/streamlit-analytics). 
            If you didn't mean to go here, remove `?analytics=on` from the URL.
            """
        )
        show_results = True
        if unsafe_password is not None:
            password_input = st.text_input("Enter password to show results")
            if password_input != unsafe_password:
                show_results = False
                if len(password_input) > 0:
                    st.write("Nope, that's not correct ☝️")
        if show_results:
            st.markdown(
                """
                <sub>Note: The widget counts add +1 each time streamlit executes your 
                script (= each time the user input changes). E.g. for st.selectbox, it 
                adds +1 for the currently selected option each time a user interacts 
                with ANY component in your app.</sub>
                """,
                unsafe_allow_html=True,
            )
            st.write(counts)


@contextmanager
def track(
    unsafe_password: str = None, save_to_json: Union[str, Path] = None, verbose=False
):
    """
    Context manager to start and stop tracking user inputs to a streamlit app.
    
    To use this, wrap all calls to streamlit in `with streamlit_analytics.track():`. 
    This also shows the analytics results below your app if you attach 
    `?analytics=on` to the URL.
    """
    start_tracking(verbose=verbose)
    # Yield here to execute the code in the with statement. This will call the wrappers
    # above, which track all inputs.
    yield
    stop_tracking(
        unsafe_password=unsafe_password, save_to_json=save_to_json, verbose=verbose
    )
