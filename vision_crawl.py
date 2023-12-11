from openai import OpenAI
import subprocess
import base64
import json
import os
import logging
import requests
from importlib.machinery import SourceFileLoader
import pandas as pd

# Setting up logging to handle info, warning, and error messages.
logging.basicConfig(level=logging.INFO)

import requests
import os
from importlib.machinery import SourceFileLoader
import pandas as pd


try:
    config = SourceFileLoader("config", "config.py").load_module()

    bungie_api_key = config.BUNGIE_API_KEY
    endpoint = "https://www.bungie.net/Platform/Content/Rss/NewsArticles/{pageToken}/"
    page_token = "0"
    include_body = True
    headers = {
        "X-API-Key": bungie_api_key
    }
    params = {
        "includebody": include_body
    }

    results = []

    while page_token is not None:
        response = requests.get(endpoint.format(pageToken=page_token), headers=headers, params=params)

        if response.status_code == 200:
            json_response = response.json()
            if 'NewsArticles' in json_response['Response']:
                results.extend(json_response['Response']['NewsArticles'])
            else:
                print("No NewsArticles found in the response.")
                break
            page_token = json_response['Response']['NextPaginationToken']
        else:
            print("Error:", response.status_code)
            print("Response:", response.text)
            break
except Exception as e:
    print("An error occurred:", str(e))
    
# Desired keys
keys = ['Title', 'Link', 'PubDate', 'Description']

# Filtering the results
filtered_results = [{key: item[key] for key in keys} for item in results]

# Convert the filtered list into a DataFrame
df = pd.DataFrame(filtered_results)

import re
pattern = r'Update|Hotfix'
df = df[df['Title'].str.contains(pattern, regex=True, flags=re.IGNORECASE)]
df = df.iloc[0:25].reset_index()
# Print the filtered DataFrame

base_url = "https://www.bungie.net"

# Prepending the base URL to each 'Link' in the DataFrame
df['Link'] = df['Link'].apply(lambda x: base_url + x)


# Initialize the OpenAI model with a timeout of 10 seconds.
model = OpenAI()
model.timeout = 10

def image_b64(image):
    """
    This function takes an image file path, reads the image, 
    and returns its base64 encoded string. 
    If an error occurs, it logs the error and returns None.
    """
    try:
        with open(image, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        logging.error(f"Error reading image file: {e}")
        return None

def take_screenshot(url):
    """
    This function takes a URL, uses a subprocess to run a Node.js script 
    that takes a screenshot of the webpage at the URL, and saves it as 'screenshot.jpg'.
    It returns the exit code and the output of the subprocess.
    If an error occurs during the subprocess, it logs the error.
    """
    if os.path.exists("screenshot.jpg"):
        os.remove("screenshot.jpg")

    try:
        result = subprocess.run(
            ["node", "screenshot.cjs", url],
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout
    except Exception as e:
        logging.error(f"Error taking screenshot: {e}")
        return None, None
    
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

        exitcode, output = take_screenshot(url)

        if not os.path.exists("screenshot.jpg"):
            logging.warning("ERROR: Trying different URL")
            messages.append({
                "role": "user",
                "content": "I was unable to crawl that site. Please pick a different one."
            })
            continue

        b64_image = image_b64("screenshot.jpg")
        if not b64_image:
            continue

 # This part of the script processes the screenshot and uses the OpenAI model to get answers.

        # Convert the screenshot to a base64 encoded string.
        b64_image = image_b64("screenshot.jpg")
        if not b64_image:
            continue

        # Append the screenshot in base64 format and the user's prompt to the messages.
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{b64_image}",
                },
                {
                    "type": "text",
                    "text": prompt,
                }
            ]
        })

        # Try to get a response from the OpenAI model using the screenshot.
        try:
            response = model.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "Your job is to answer the user's question based on the given screenshot of a website. Answer the user as an assistant, but don't tell that the information is from a screenshot or an image. Pretend it is information that you know. If you can't answer the question, simply respond with the code `ANSWER_NOT_FOUND` and nothing else.",
                    }
                ] + messages[1:],
                max_tokens=1024,
            )
        except Exception as e:
            logging.error(f"Error with OpenAI API call: {e}")
            continue

        # Extract the message content from the response.
        message = response.choices[0].message
        message_text = message.content

        # Check if the answer was found or not.
        if "ANSWER_NOT_FOUND" in message_text:
            logging.warning("ERROR: Answer not found")
            messages.append({
                "role": "user",
                "content": "I was unable to find the answer on that website. Please pick another one"
            })
        else:
            # If an answer is found, print it and prompt for the next user input.
            print(f"GPT: {message_text}")
            prompt = input("\nYou: ")
            messages.append({
                "role": "user",
                "content": prompt,
            })

# This line checks if the script is being run as the main program and not being imported.
if __name__ == "__main__":
    main()