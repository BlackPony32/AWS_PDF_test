import plotly.graph_objects as go
import os
import pandas as pd
zip_cache={}

def get_state_by_zip(zip_code):
    import pandas as pd
    import pgeocode

    nomi = pgeocode.Nominatim('US')


    
    zip_code = str(zip_code)  # Ensure ZIP code is a string
    #print(zip_cache)
    if zip_code in zip_cache:
        #print('here')
        return zip_cache.get('zip_code')
    
    try:
        result = nomi.query_postal_code(zip_code)
        state = result.state_code if result is not None else "Unknown"
        zip_cache.update({zip_code:state})
        #zip_cache[zip_code] = state  # Store in cache
        #print(zip_cache[zip_code])
        return state
    except Exception as e:
        return e

def get_state_by_city(state_name):
    import pandas as pd
    import pgeocode

    nomi = pgeocode.Nominatim('US')


    
    state_name = str(state_name)  # Ensure ZIP code is a string
    #print(zip_cache)
    if state_name in zip_cache:
        #print('here')
        return zip_cache.get('state_name')
    
    try:
        result = nomi.query_postal_code(state_name)
        state = result.state_name if result is not None else "Unknown"
        zip_cache.update({state_name:state})
        #zip_cache[zip_code] = state  # Store in cache
        print(zip_cache[state_name])
        return state
    except Exception as e:
        return e

def load_dataframe(user_folder='test', file_name="cleaned_data.csv"):
    """
    Attempts to load a DataFrame from a CSV file using multiple encodings.
    Returns the loaded DataFrame or raises an exception on failure.
    """
    file_path = os.path.join("FastApi\\src\\uploads\\", user_folder, file_name)
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']

    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            pass  # Try the next encoding

    raise ValueError(f"Failed to read the file {file_path} with provided encodings.")

def visualize_total_cases_by_state(df, plots_dir, summary_dir):
    """
    Generates a choropleth map of total cases by state and writes a summary.
    """
    if df is None or 'STATE' not in df.columns or 'TOTAL_CASES' not in df.columns:
        raise ValueError("Input DataFrame must contain 'STATE' and 'TOTAL_CASES' columns.")

    # Group data by state
    state_cases = df.groupby('STATE')['TOTAL_CASES'].sum().reset_index()

    # Create the choropleth map
    fig = go.Figure(data=go.Choropleth(
        locations=state_cases['STATE'],
        z=state_cases['TOTAL_CASES'],
        locationmode='USA-states',
        colorscale='YlGn',
        colorbar=dict(
            title="Total Cases",
            titlefont=dict(size=14),
            tickfont=dict(size=12)
        ),
    ))

    # Add state labels with total cases
    for _, row in state_cases.iterrows():
        fig.add_trace(go.Scattergeo(
            locationmode='USA-states',
            locations=[row['STATE']],
            text=f"{row['STATE']}: {row['TOTAL_CASES']}",
            mode='text',
            textfont=dict(size=10, color='black'),
            showlegend= False
        ))

    # Zoom into regions with non-zero values
    states_with_values = state_cases[state_cases['TOTAL_CASES'] > 0]['STATE'].tolist()
    fig.update_geos(
        scope='usa',
        fitbounds="locations",
        visible=True,
        projection_scale=3,  # Optimized zoom
    )

    fig.update_layout(
        title=dict(
            text='Total Cases by State',
            font=dict(size=20),
            x=0.5,  # Center the title
            xanchor='center'
        ),
        geo=dict(
            showlakes=True,
            lakecolor='rgb(173, 216, 230)',
            coastlinecolor='rgba(0,0,0,0.5)',
            landcolor='rgba(240, 240, 240, 1)'
        ),
        paper_bgcolor='rgba(255, 255, 255, 1)',
        plot_bgcolor='rgba(255, 255, 255, 1)',
        margin=dict(l=50, r=50, t=50, b=50),
        coloraxis_colorbar_title="Total Cases"  # Simplified legend title
    )

    # Save the plot
    os.makedirs(plots_dir, exist_ok=True)
    chart_path = os.path.join(plots_dir, 'chart_5.png')
    fig.write_image(chart_path)

    # Write the summary
    summary = (
        """
        This map visualization illustrates the total cases distributed across different states in the USA. 
        1. Patterns or Trends: The map highlights states with higher sales volumes, potentially indicating larger markets or more active customer bases.
        2. Outliers: States with significantly higher or lower total cases may suggest unique market dynamics or customer preferences.
        3. Explaining Differences: Differences in total cases by state could be due to population density, economic conditions, or regional product popularity. Understanding these factors can help in strategic planning and resource allocation.
        """
    )

    os.makedirs(summary_dir, exist_ok=True)
    summary_path = os.path.join(summary_dir, 'sum_5.txt')
    with open(summary_path, 'w') as f:
        f.write(summary)

    print(f"Visualization saved to {chart_path}")
    print(f"Summary saved to {summary_path}")



def check_map_columns(user_folder, file_name="cleaned_data.csv"):
    df = load_dataframe(user_folder, file_name)
    #df = df.copy()
    
    #print(df.columns)
    PLOTS_DIR = f'FastApi\\src\\plots\\{user_folder}'
    SUMMARY_DIR = f'FastApi\\src\\summary\\{user_folder}'
    if "STATE" in df.columns:
        visualize_total_cases_by_state(df, PLOTS_DIR, SUMMARY_DIR)
        df.drop(['STATE',"ZIP"], axis=1, inplace=True)
        return True
    elif "ZIP" in df.columns:
        unique_zips = df['ZIP'].unique()
        print(unique_zips)
        # Perform the lookup only once for unique ZIP codes
        results = {zip_code: get_state_by_zip(zip_code) for zip_code in unique_zips}
        # Map the results back to the DataFrame
        df['STATE'] = df['ZIP'].map(results)
        df.to_csv("cleand_with_cities.csv", index=False)
        print("Processing complete! Saved as 'cleaned_with_cities.csv'.")
        visualize_total_cases_by_state(df, PLOTS_DIR, SUMMARY_DIR)
        df.drop(['STATE',"ZIP"], axis=1, inplace=True)
        return True
    elif "CITY" in df.columns:
        pass
        #visualize_total_cases_by_city(df, PLOTS_DIR, SUMMARY_DIR)
        
        return False
    else:
        return False