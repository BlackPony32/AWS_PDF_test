
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
    plots_FOLDER = f'src/plots/{user_folder}'
    summary_FOLDER = f'src/summary/{user_folder}'

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
    	verbose=True
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
                        -Create an informative visualization, but each visualization style should be unique (e.g., bar graph, etc.).
                        -solid light gray background without grid lines (xaxis_showgrid=False, yaxis_showgrid=False)
                        -Include a summary (1500+ characters) explaining the visual insights and relevant business observations.
                        -Show only top 15 data points, grouping others under 'other.'
                        -Use unique colors for each chart, such as Light24.
                        -Use fig.add_trace() to combine graphs if needed.
                        -Save visualizations as PNG files in {plots_dir} (e.g., chart_n.png).
                        -Save each summary in {sum_dir} (e.g., sum_n.txt).
                        Coding Standards

                        -Only use columns that exist in the dataframe, checking existence with conditionals.
                        -Ensure all functions handle errors using try-except.
                        -Avoid using global variables and written functions for loading datasets.
                        -Optimize visualizations for high-quality output and readability.
                        -You are writing a part of the code, so know that df has already been declared. do not overwrite it.
                        Code Example
                        A good code structure for one function:

                        import plotly.graph_objects as go
                        import plotly.express as px  # Import plotly.express for colors

                        def task_2_visualization(df):
                            try:
                                if 'Item #' in df.columns and 'Qty' in df.columns:
                                    # Task 2: Top 15 Products by Quantity Sold
                                    product_sales = df.groupby('Item #')['Qty'].count().nlargest(15)
                                    fig = go.Figure(data=[go.Pie(labels=product_sales.index, values=product_sales.values, hole=0.3)])
                                    fig.update_traces(marker=dict(colors=px.colors.qualitative.Light24))
                                    fig.update_layout(title='Top 15 Products by Quantity Sold')

                                    plots_dir = 'src/plots/68cd4df2-a031-11ef-9654-70665514def7'
                                    os.makedirs(plots_dir, exist_ok=True)
                                    fig.write_image(f'{plots_dir}/chart_2.png')

                                    summary = (
                                        "This donut chart illustrates the top 15 products by the quantity sold. "
                                        "Such a visualization is crucial for identifying which products are in high demand. "
                                        "It helps the business in inventory management and resource allocation, ensuring that the most popular products are always in stock. "
                                        "By recognizing trends in product sales, the company can adjust its procurement strategies and optimize its supply chain operations effectively."
                                    )

                                    sum_dir = 'src/summary/68cd4df2-a031-11ef-9654-70665514def7'
                                    os.makedirs(sum_dir, exist_ok=True)
                                    with open(f'{sum_dir}/sum_2.txt', 'w') as f:
                                        f.write(summary)

                            except Exception as e:
                                print(f"An error occurred in task 2: e")


                        task_2_visualization(df)
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
        'plots_dir': f"src/plots/{user_folder}",
        'sum_dir': f"src/summary/{user_folder}",
        'data_path': f'src/uploads/{user_folder}/cleaned_data.csv',
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