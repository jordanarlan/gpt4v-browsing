from openai import OpenAI
import json
import logging
from importlib.machinery import SourceFileLoader
import pandas as pd
from api import get_filtered_results
from open_ai import get_openai_response

# Setting up logging to handle info, warning, and error messages.
logging.basicConfig(level=logging.INFO)

# Initialize the OpenAI model with a timeout of 10 seconds.
model = OpenAI()
model.timeout = 10
def format_df_for_llm(df):
    """
    Converts the DataFrame into a string format suitable for the language model.
    """
    formatted_str = "Here are the recent updates for Destiny 2:\n"
    for _, row in df.iterrows():
        formatted_str += f"Title: {row['Title']}, Link: {row['Link']}, Date: {row['PubDate']}, Description: {row['Description']}\n"
    return formatted_str

def main():
    """
    The main function where the script execution begins.
    """
    prompt = input("You: ")

    # Get the filtered results from the API
    df = get_filtered_results()

    # Format the DataFrame for LLM
    df_str = format_df_for_llm(df)

    messages = [
        {
            "role": "system",
            "content": "You are a language model assisting with selecting relevant links from a dataset. Your job is to give the user a URL in JSON format. Respond in the following JSON format: {\"url\": \"<put url here>\"}",
        },
        {
            "role": "user",
            "content": prompt,
        },
        {
            "role": "assistant",
            "content": df_str,
        }
    ]
    
    while True:
        # Try to get a response from the OpenAI model.
        try:
            response = model.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=messages,
                max_tokens=1024,
                response_format={"type": "json_object"},
                seed=2232,
            )
        except Exception as e:
            logging.error(f"Error with OpenAI API call: {e}")
            break

        message = response.choices[0].message
        message_json = json.loads(message.content)
        url = message_json["url"]

        messages.append({
            "role": "assistant",
            "content": message.content,
        })

        logging.info(f"Crawling {url}")

        messages = get_openai_response(url, prompt, messages)

# This line checks if the script is being run as the main program and not being imported.
if __name__ == "__main__":
    main()