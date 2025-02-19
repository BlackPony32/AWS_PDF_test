
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os
#from t_custom_code_exec_tool import CLITool
from . import code_executing_solution
import tiktoken
#from crewai_tools import CodeInterpreterTool
from dotenv import load_dotenv
load_dotenv()
# Pricing rates (per 1,000 tokens)
INPUT_COST_PER_1K_TOKENS = 0.003  # for 1000 GPT-4о input
OUTPUT_COST_PER_1K_TOKENS = 0.012  # for 1000 GPT-4о output
#from crewai_tools import CSVSearchTool
import asyncio
import logging
log_file_path = "preprocess_log.log"
logger = logging.getLogger(__name__)

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count the number of tokens in a text using tiktoken."""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)

def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost of the request and response in dollars."""
    input_cost = (input_tokens / 1000) * INPUT_COST_PER_1K_TOKENS
    output_cost = (output_tokens / 1000) * OUTPUT_COST_PER_1K_TOKENS
    total_cost = input_cost + output_cost
    return total_cost

def AI_generation_plots_summary(_data_dict, user_folder, page_numb):
    plots_FOLDER = f'FastApi/src/plots/{user_folder}'
    summary_FOLDER = f'FastApi/src/summary/{user_folder}'

    # Ensure folders exist
    if not os.path.exists(plots_FOLDER):
        os.makedirs(plots_FOLDER)
    if not os.path.exists(summary_FOLDER):
        os.makedirs(summary_FOLDER)

    #csv_tool = CSVSearchTool()
    OpenAIGpt4 = ChatOpenAI(
        temperature=0,
        model='o1-mini'
        #model='gpt-4o'
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
    	verbose=False,
        llm=OpenAIGpt4
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
                        -Create an informative visualization, and each visualization style can use only one time (e.g.,one bar graph,one line etc.).
                        -solid #F5F5F5 plot background without grid lines (xaxis_showgrid=False, yaxis_showgrid=False)
                        -Include a summary (500+ characters) explaining what is shown in the graph and relevant business observations.
                        Summary should teach how to read visualization + answer on these qustions:
                        1. What patterns or trends can be observed in the data?
                        2. Are there any outliers or unexpected values?
                        3. What factors might explain the main differences in the data?
                        -Show only top 15 data values if it many
                        -Use unique colors for each chart, such as Light24 color palette per plot.
                        -Use fig.add_trace() to combine graphs if needed. (like bar sales and line data dependency for example)
                        -Save visualizations as PNG files in {plots_dir} (e.g., chart_n.png).
                        -Save each summary in {sum_dir} (e.g., sum_n.txt).
                        Coding Standards

                        -Only use columns that exist in the dataframe, checking existence with conditionals.
                        -Try to use state or zip code data to make map charts.
                        -Ensure all functions handle errors using try-except.
                        -Avoid using global variables and written functions for loading datasets.
                        -Optimize visualizations for high-quality output and readability.
                        -You are writing a part of the code, so know that df has already been declared. do not overwrite it.
                        and do not write any variable df ! only import lib, functions and call them
                        Code Example you should follow
                        -always write full code for all {tasks_for_data_num} functions and call it!
                        A good code structure for one function that good to follow:

                        import plotly.graph_objects as go
                        import plotly.express as px  # Import plotly.express for colors

                        def task_1_visualization(df, sum_dir, plots_dir):
                            try:
                                if df is None:
                                    raise ValueError("Input DataFrame `df` is None. Please provide a valid DataFrame.")

                                required_columns = ['MailCity', 'Total Sales $']
                                for col in required_columns:
                                    if col not in df.columns:
                                        raise ValueError(f"Required column 'col' is missing from the DataFrame.")

                                # Aggregate sales data by city
                                sales_by_city = df.groupby('MailCity')['Total Sales $'].sum().reset_index()
                                sales_by_city = sales_by_city.sort_values('Total Sales $', ascending=True).tail(15)

                                # Format the sales values for display
                                sales_by_city['Formatted Sales'] = sales_by_city['Total Sales $'].round(2)

                                # Create the bar chart
                                fig = go.Figure()
                                fig.add_trace(go.Bar(
                                    x=sales_by_city['Total Sales $'],
                                    y=sales_by_city['MailCity'],
                                    orientation='h',
                                    marker=dict(color=px.colors.qualitative.Light24),
                                    name='Total Sales',
                                    text=sales_by_city['Formatted Sales'].astype(str)  # Use formatted sales for text
                                ))

                                # Update layout with descriptive labels
                                fig.update_layout(
                                    title='Top 15 Cities by Total Sales',
                                    xaxis_title='Total Sales in USD',
                                    yaxis_title='City Name',
                                    paper_bgcolor='rgba(245, 245, 245, 1)',
                                    plot_bgcolor='rgba(245, 245, 245, 1)',
                                    xaxis_showgrid=False,
                                    yaxis_showgrid=False
                                )

                                # Save the chart to a file
                                os.makedirs(plots_dir, exist_ok=True)
                                fig.write_image(os.path.join(plots_dir, 'chart_1.png'))

                                summary = '''This horizontal bar chart highlights total sales distribution across the top 15 mail cities. Cities with longer bars indicate higher sales, reflecting strong market presence or demand.

Trends: Identifies key sales hubs and geographical performance.
Outliers: Highlights cities with unusually high or low sales, signaling market strengths or opportunities.
Factors: Sales variations stem from population density, economic conditions, competition, and marketing efforts.
Understanding these patterns helps optimize resource allocation, marketing strategies, and supply chain management.'''

                                os.makedirs(sum_dir, exist_ok=True)
                                with open(os.path.join(sum_dir, 'sum_1.txt'), 'w') as f:
                                    f.write(summary.strip())

                            except Exception as e:
                                print(f"An error occurred in task 1: e")


                        task_1_visualization(df, sum_dir, plots_dir)
                        
                        -Do not comment function calling. ALWAYS call written functions!
                        Output Requirements
                        The output code must be optimized, error-free, and focused on generating meaningful business insights through visualization.
                        """,
        expected_output= "Summary.txt file with full generated code for viz and summary.Repeat code as final answer.",
        #context = [context],
        output_file = f"FastApi/src/uploads/{user_folder}/Summary.txt",
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

    data_path = f'FastApi/src/uploads/{user_folder}/AI_cleaned.csv'
    if os.path.exists(data_path):
        pass
    else:
        data_path = f'FastApi/src/uploads/{user_folder}/cleaned_data.csv'
    
    data_config ={
        'plots_dir': f"FastApi/src/plots/{user_folder}",
        'sum_dir': f"FastApi/src/summary/{user_folder}",
        'data_path': str(data_path),
        'tasks_for_data_num' : str(page_numb),
        'head': str(head),  # First 5 rows of the dataframe as a dictionary
        'describe':str(describe),  # Descriptive statistics of all columns
        'info': str(info),  # DataFrame info as a string
        'missing_values': str(missing_values),  # Count of missing values for each column
        'column_types': str(column_types),  # Data types of each column
        'shape': str(shape)  # Shape of the dataset (rows, columns)

    }

    try:
        # Count input tokens
        assert isinstance(plan.description, str), "Plan description must be a string!"
        input_tokens = count_tokens(plan.description.format(**data_config))
        
        # Kickoff the crew
        assert all(isinstance(value, str) for value in data_config.values()), "All values in data_config must be strings!"
        result = crew1.kickoff(inputs=data_config)
        
        # Count output tokens
        output_tokens = count_tokens(str(result))
        
        # Calculate the cost
        total_cost = calculate_cost(input_tokens, output_tokens)
        
        # Print the cost
        logger.info(f"Input tokens: {input_tokens} to {user_folder}")
        logger.info(f"Output tokens: {output_tokens} to {user_folder}")
        logger.info(f"Total cost: ${total_cost:.4f} to {user_folder}")
        #print(f"Input tokens: {input_tokens}")
        #print(f"Output tokens: {output_tokens}")
        #print(f"Total cost: ${total_cost:.4f}")
    
    except Exception as e:
        import traceback
        logger.error(f"Error during crew execution: {e}")
        #print(f"Error during crew execution: {e}")
        traceback.print_exc()

    try:
        code_executing_solution.extract_and_execute_code(f"FastApi/src/uploads/{user_folder}/Summary.txt", user_folder)
    except Exception as e:
        logger.error(f"Error during AI code run: {e}")
        #print(f"Error during AI code run: {e}")
        return "Error during AI code run"
    return "Everything is ok"