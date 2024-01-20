import streamlit as st
import pandas as pd
import random
import json

st.set_page_config(layout="wide")
st.title("Prompt Splitter")

# Function to create layout containers
def create_layout():
    settings_container = st.container()
    dataframe_container = st.container()
    buttons_container = st.container()

    return {
        "settings": settings_container,
        "dataframe": dataframe_container,
        "buttons": buttons_container
    }

layout = create_layout()

def copy_text_to_clipboard_js(text):
    js = f"""<script>
    navigator.clipboard.writeText(`{text}`).then(() => {{
        console.log('Text copied to clipboard');
    }})
    .catch(err => {{
        console.error('Failed to copy text: ', err);
    }});
    </script>"""
    return js


# Function to split prompts into groups with specified rows per prompt
def split_prompts(prompt_list, rows_per_prompt, prefix, suffix, seed_repeats):
    prompts = []
    i = 0
    while i < len(prompt_list):
        prompt = '{' + ', '.join(prompt_list[i:i+rows_per_prompt]) + '}'
        seeds = [str(random.randint(1, 10**10)) for _ in range(seed_repeats)]
        seed_string = ', '.join(seeds)
        prompt_with_suffix = prefix + prompt + suffix + f" --seed {{{seed_string}}}"
        prompts.append(prompt_with_suffix)
        i += rows_per_prompt
    return prompts

# Function to parse the input text and return a list of prompts
def parse_input_prompts(input_text):
    lines = input_text.split('\n')
    prompts = []
    for line in lines:
        if line and not line.startswith('#'):
            prompt = line.split('. ', 1)[-1].strip().replace(',', '\\,')
            prompts.append(prompt)
    return prompts

# Function to display DataFrame in the container
def display_dataframe_in_container(df, highlight_index):
    # Clear the previous contents of the container
    

    # Define a function to apply a background color to the highlighted row
    def highlight_row(row, highlighted_index):
        if row.name == highlighted_index:
            return [f'background-color: lightgreen; color: black;']  # Set both background and text color
        else:
            return ['']

    # Apply styles to the DataFrame
    styled_df = df.style.apply(highlight_row, highlighted_index=highlight_index + 1, axis=1)  # +1 because DataFrame index starts from 1 in this case
    styled_df.set_properties(**{'white-space': 'normal', 'text-align': 'left'})  # Ensure text wrapping and alignment
    styled_df.set_table_styles([{'selector': 'th', 'props': [('font-size', '12pt')]}])  # Style for header

    # Display the DataFrame with full width in the container
    layout['dataframe'].write(styled_df.to_html(escape=False), unsafe_allow_html=True)

# Function to regenerate prompts
def regenerate_prompts():
    # Use the current values from st.session_state
    prompts = split_prompts(parsed_prompts, st.session_state.rows_per_prompt, st.session_state.prefix, st.session_state.suffix, st.session_state.seed_repeats)
    prompt_df = pd.DataFrame({'Prompts': prompts})
    prompt_df.index += 1  # Make index start from 1
    st.session_state['prompt_df'] = prompt_df  # Save updated prompt_df to session state
    st.session_state.prompt_index = 0  # Reset prompt index after update

with layout['settings']:
    # Text area for input prompts
    input_prompts = st.text_area("Enter prompts (one per line, ignore lines starting with '#'):")

    # Parse the input text into a list of prompts
    parsed_prompts = parse_input_prompts(input_prompts)

    # Load presets from file
    presets_file_path = 'presets.json'
    try:
        with open(presets_file_path, 'r') as file:
            presets = json.load(file)
    except FileNotFoundError:
        presets = []

    # Initialize session state variables or use existing ones
    st.session_state.prefix = st.session_state.get('prefix', " --weird {0,50, 100} --s {0,50,100}")
    st.session_state.suffix = st.session_state.get('suffix', " { --v 5.2, --v 5.2 --style raw}")
    st.session_state.rows_per_prompt = st.session_state.get('rows_per_prompt', 3)
    st.session_state.seed_repeats = st.session_state.get('seed_repeats', 1)
    st.session_state.prompt_index = st.session_state.get('prompt_index', 0)
    if 'prompt_df' not in st.session_state:
        regenerate_prompts()  # Generate initial prompts

    # UI for rows per prompt, seed repeats
    rows_per_prompt = st.number_input("How many rows per prompt?", min_value=1, value=st.session_state.rows_per_prompt, key='rows_per_prompt')
    seed_repeats = st.number_input("How many seed repeats?", min_value=1, value=st.session_state.seed_repeats, key='seed_repeats')

    # UI for presets
    selected_preset_index = st.selectbox(
        "Select a favorite preset",
        range(len(presets)),
        format_func=lambda i: f"Favorite {i+1}: {presets[i]['prefix']} {presets[i]['suffix']}"
    )
    # Button to apply preset updates
    if st.button("Apply Preset"):
        st.session_state.prefix = presets[selected_preset_index]['prefix']
        st.session_state.suffix = presets[selected_preset_index]['suffix']
        regenerate_prompts()

    # Text inputs for prefix and suffix
    prefix = st.text_input("Enter prefix:", value=st.session_state.prefix, key='prefix_input')
    suffix = st.text_input("Enter suffix:", value=st.session_state.suffix, key='suffix_input')

    # Button to update prompts based on user input for prefix and suffix
    if st.button("Update Prompts"):
        # Update session state values from the input widgets
        st.session_state.prefix = prefix
        st.session_state.suffix = suffix
        regenerate_prompts()  # Regenerate prompts with updated values
        # Redisplay the DataFrame with the updated prompts
        display_dataframe_in_container(st.session_state['prompt_df'], st.session_state.prompt_index)


# with layout["dataframe"]:
#     display_dataframe_in_container(st.session_state['prompt_df'], st.session_state.prompt_index)

with layout['buttons']:
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Copy to Clipboard", key='copy_button'):
            if 0 <= st.session_state.prompt_index < len(st.session_state['prompt_df']):
                prompt_text = st.session_state['prompt_df'].iloc[st.session_state.prompt_index]['Prompts']
                # Copy to clipboard using JavaScript
                st.markdown(copy_text_to_clipboard_js(prompt_text), unsafe_allow_html=True)
                st.write(f"Prompt {st.session_state.prompt_index + 1} copied to clipboard.")

                # Move to the next prompt
                if st.session_state.prompt_index < len(st.session_state['prompt_df']) - 1:
                    st.session_state.prompt_index += 1
                else:
                    st.session_state.prompt_index = 0

                # Redisplay the DataFrame with the new highlight
                display_dataframe_in_container(st.session_state['prompt_df'], st.session_state.prompt_index)

    # Display the prompts in a data editor
    # st.data_editor(data=st.session_state['prompt_df'], key="prompt_editor")

    with col2:
        if st.button("Previous", key='prev_button'):
            if st.session_state.prompt_index > 0:
                st.session_state.prompt_index -= 1
                # Redisplay the DataFrame with the updated highlight in the container
                display_dataframe_in_container(st.session_state['prompt_df'], st.session_state.prompt_index)

    with col3:
        if st.button("Next", key='next_button'):
            if st.session_state.prompt_index < len(st.session_state['prompt_df']) - 1:
                st.session_state.prompt_index += 1
                # Redisplay the DataFrame with the updated highlight in the container
                display_dataframe_in_container(st.session_state['prompt_df'], st.session_state.prompt_index)
