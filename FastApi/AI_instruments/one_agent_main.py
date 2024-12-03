
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os
#from t_custom_code_exec_tool import CLITool
from . import code_executing_solution
from crewai_tools import CodeInterpreterTool
from dotenv import load_dotenv
load_dotenv()
from crewai_tools import CSVSearchTool
import asyncio

def AI_generation_plots_summary(_data_dict, user_folder):
    plots_FOLDER = f'FastApi/src/plots/{user_folder}'
    summary_FOLDER = f'FastApi/src/summary/{user_folder}'

    # Ensure folders exist
    if not os.path.exists(plots_FOLDER):
        os.makedirs(plots_FOLDER)
    if not os.path.exists(summary_FOLDER):
        os.makedirs(summary_FOLDER)

    csv_tool = CSVSearchTool()
    OpenAIGpt4 = ChatOpenAI(
        temperature=0,
        model='gpt-4o'
    )

    #______________________agents block__________________________________________
    planner = Agent(
        role="Senior Data Scientist",
        goal="""Write code to visualize the data you have received and an explanation of the visualizations you will create.
                The code should be of the highest quality
                and follow the instructions clearly. Using the tool- run it.""",
        backstory="""You're working with visual studio code with plotly go code.""",
        allow_delegation=False,
        memory=True,
    	verbose=False
    )

    #_______________________tasks block_________________________________________
    plan = Task(
        description="""Task Description:

                        Analyze a CSV dataset and create insightful visualizations using Plotly's Graph Objects (GO) library. 
                        Use distinct chart styles for each visualization to ensure unique and engaging representations. 
                        File paths and folders are already set up, so no need to check for their existence.

                        Input Data
                        You will be provided with basic dataset information:

                        Dataset Head: {head}
                        Descriptive Stats: {describe}
                        DataFrame Info: {info}
                        Missing Values Information: {missing_values}
                        Column Types and Names: {column_types}
                        Shape: {shape}
                        Tasks

                        Data Analysis & Visualization Generation:

                        Analyze the data and design {tasks_for_data_num} specific visualizations.
                        Address negative aspects in the dataset, such as low product sales or supplier issues, 
                        ensuring the last task highlights these (e.g., low revenue, poor sales).
                        Plotly GO Code & Function Requirements

                        Write code using Plotly GO, each in a standalone function named as task_n_visualization(df).
                        Each function should:
                        -don't use pie or donut charts in your visualizations - instead, use 'horizontal bars' with full labeling of visualizations.
                        -An array of visualizations that would be great to use: Marimekko Chart, map visualizations (if addresses are present), Color Palette for Bar Chart
                        -Create an informative visualization, and each visualization style can use only one time (e.g.,one bar graph,one line etc.).
                        -solid #F5F5F5 plot background without grid lines (xaxis_showgrid=False, yaxis_showgrid=False)
                        -Include a summary (1500+ characters) explaining the visual insights and relevant business observations.
                        Summary should teach how to read visualization + answer on these qustions:
                        1. What patterns or trends can be observed in the data?
                        2. Are there any outliers or unexpected values?
                        3. What factors might explain the main differences in the data?
                        -Show only top 15 data values if it many
                        -Use unique colors for each chart, such as Light24.
                        -Use fig.add_trace() to combine graphs if needed. (like bar sales and line data dependency for example)
                        -Save visualizations as PNG files in {plots_dir} (e.g., chart_n.png).
                        -Save each summary in {sum_dir} (e.g., sum_n.txt).
                        Coding Standards 

                        -Only use columns that exist in the dataframe, checking existence with conditionals.
                        -Ensure all functions handle errors using try-except.
                        -Avoid using global variables and written functions for loading datasets.
                        -Optimize visualizations for high-quality output and readability.
                        -You are writing a part of the code, so know that df has already been declared. do not overwrite it.
                        and do not write any variable df ! only import lib, functions and call them
                        Code Example you should follow
                        -always write full code for all {tasks_for_data_num} functions and call it!
                        A good code structure for one function:

                        import plotly.graph_objects as go
                        import plotly.express as px  # Import plotly.express for colors

                        def task_1_visualization(df, sum_dir, plots_dir):
                            try:
                                if df is None:
                                    raise ValueError("Input DataFrame `df` is None. Please provide a valid DataFrame.")

                                if 'Total Sales $' in df.columns and 'DocDate' in df.columns:
                                    # Task 1: Time Series Analysis of Total Sales
                                    sales_over_time = df.groupby('DocDate')['Total Sales $'].sum().reset_index()
                                    fig = go.Figure()
                                    fig.add_trace(go.Scatter(x=sales_over_time['DocDate'], y=sales_over_time['Total Sales $'],
                                                              mode='lines+markers', name='Total Sales',
                                                              line=dict(color=px.colors.qualitative.Light24[0])))
                                    fig.update_layout(title='Total Sales Over Time',
                                                      xaxis_title='Date',
                                                      yaxis_title='Total Sales ($)',
                                                      paper_bgcolor='rgba(245, 245, 245, 1)',
                                                      plot_bgcolor='rgba(245, 245, 245, 1)',
                                                      xaxis_showgrid=False,
                                                      yaxis_showgrid=False)

                                    plots_dir = '{plots_dir}'
                                    if plots_dir is None:
                                        raise ValueError("`plots_dir` is None. Please provide a valid directory path.")
            
                                    os.makedirs(plots_dir, exist_ok=True)
                                    fig.write_image(f'{plots_dir}/chart_1.png')

                                    summary = ('''
                                        This visualization analyzes the total sales over time, plotted as a time series. "
                                        1. Patterns or Trends: The graph indicates fluctuations in total sales, with peaks and troughs corresponding to specific dates. A consistent increase indicates growing sales, while significant decreases might signify seasonal trends or external factors affecting sales performance.
                                        2. Outliers: Any unusually high peaks in the graph signal exceptional sales days, perhaps owing to promotions or new product launches, while unexpected dips may warrant further investigation.
                                        3. Explaining Differences: Various factors may contribute to these fluctuations, including marketing campaigns, holidays, or changes in consumer behavior. Identifying the reasons behind these trends can help in strategic planning.
                                        '''
                                    )

                                    sum_dir = '{sum_dir}'
                                    if sum_dir is None:
                                        raise ValueError("`sum_dir` is None. Please provide a valid directory path.")
            
                                    os.makedirs(sum_dir, exist_ok=True)
                                    with open(f'{sum_dir}/sum_1.txt', 'w') as f:
                                        f.write(summary)

                            except Exception as e:
                                print(f"An error occurred in task 1: e")


                        task_1_visualization(df, sum_dir, plots_dir)
                        
                        Output Requirements
                        The output code must be optimized, error-free, and focused on generating meaningful business insights through visualization.
                        """,
        expected_output= "Summary.txt file with full generated code for viz and summary.Repeat code as final answer.",
        #context = [context],
        output_file = "Summary.txt",
        agent=planner,
        #tools = [csv_tool], #, t_custom_code_exec_tool.CLITool.execute_code
        async_execution = False
    )
    
    #_______________________run Crew_________________________________________
    crew1 = Crew(
        agents=[planner],
        tasks=[plan],
        process=Process.sequential,
        manager_llm=OpenAIGpt4
    )
    #final_answer = agent_answer.get("output")
    
    head = _data_dict.get("head")
    describe = _data_dict.get("describe")
    info = _data_dict.get("info")
    missing_values = _data_dict.get("missing_values")
    column_types = _data_dict.get("column_types")
    shape = _data_dict.get("shape")

    
    data_config ={
        'plots_dir': f"FastApi/src/plots/{user_folder}",
        'sum_dir': f"FastApi/src/summary/{user_folder}",
        'data_path': f'FastApi/src/uploads/{user_folder}/cleaned_data.csv',
        'tasks_for_data_num' : 5,
        'head': str(head),  # First 5 rows of the dataframe as a dictionary
        'describe':str(describe),  # Descriptive statistics of all columns
        'info': str(info),  # DataFrame info as a string
        'missing_values': str(missing_values),  # Count of missing values for each column
        'column_types': str(column_types),  # Data types of each column
        'shape': str(shape)  # Shape of the dataset (rows, columns)

    }

    crew1.kickoff(inputs=data_config) 

    code_executing_solution.extract_and_execute_code("Summary.txt", user_folder)
    return "Everything is ok"