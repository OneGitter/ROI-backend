import requests
import pandas as pd
import json

# Function to load CSV data using pandas
def load_csv_data(csv_file_path):
    try:
        data = pd.read_csv(csv_file_path)
        return data
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None

# Function to convert DataFrame to a string suitable for inclusion in a prompt
def convert_df_to_string(data):
    return data.to_string(index=False)

# Function to create a marketing analysis prompt based on CSV columns
def create_marketing_prompt(data_string):
    return f"""
    You are an expert marketing analyst. Analyze the following dataset and provide insights:

    Columns:
    converted_user_journey: This column contains lists where each element represents:
    The user journey, which is a sequence of mediums the user interacted with before converting.
    The number of conversions associated with that specific journey.
    non_converted_user_journey: This column contains lists structured similarly to the converted journey column, but it tracks journeys where users did not convert. Each element represents:
    The user journey, which shows the sequence of mediums the user interacted with.
    The number of non-conversions (i.e., instances where users followed this path but did not convert).
    to_state: Represents the edges showing where the user journey leads after interacting with the current medium. Similarly, each list element contains:
    The state to which the user moves (e.g., "(conversion)" or another channel).
    The probability of moving from the current state to the next.
    from_state: Represents the edges that show where the user journey begins (i.e., the "from" states). Each list element contains two components:
    The state from which the user came (e.g., "(start)" or another channel).
    The probability of transitioning from that state to the current medium.
    
    Please analyze the best and worst user journeys based on conversion rates and value, and provide the ideal budget allocation for the channels to maximize conversions.

    Suggest a detailed explanation and actionable steps to improve the performance.

    Make sure to give the response in json and do not use markup, also don't use escape characters and whitespaces in the json as it's having parsing issues.

    Dataset:
    {data_string}
    """

# Function to interact with the OpenAI API using raw HTTP requests
def query_openai(api_key, prompt, model="gpt-4o"):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert marketing analyst."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Check if the request was successful
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error querying OpenAI API: {e}")
        return None

# Function to get insights based on the CSV data
def get_marketing_insights(api_key, csv_file_path, user_history):
    data = load_csv_data(csv_file_path)
    if data is None:
        return None

    # Convert DataFrame to a string suitable for the prompt
    data_string = convert_df_to_string(data)

    # Create the detailed marketing analyst prompt based on the CSV data
    prompt = create_marketing_prompt(data_string)

    # print(prompt)

    # Query the OpenAI API with the generated prompt
    insights = query_openai(api_key, prompt)
    
    if insights:
        # Store the user session and insights in history
        user_history.append({
            "prompt": prompt,
            "response": insights
        })

        # Prepare the JSON response for the frontend
        response = {   # Placeholder for GPT response
            "insights": insights
        }
        return response
    else:
        return None

# Function to generate insights, save to JSON, and keep user history
def generate_insights_json(api_key, csv_file_path, output_json_path, user_history):
    insights_json = get_marketing_insights(api_key, csv_file_path, user_history)
    if insights_json:
        try:
            with open(output_json_path, 'w') as json_file:
                json.dump(insights_json, json_file, indent=4)
            print(f"Insights generated and saved to {output_json_path}")
        except Exception as e:
            print(f"Error writing to JSON file: {e}")
    else:
        print("No insights generated.")

user_history = []