from openai import OpenAI
import subprocess
import base64
import json
import os
import logging

# Setting up logging to handle info, warning, and error messages.
logging.basicConfig(level=logging.INFO)

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

def main():
    """
    The main function where the script execution begins.
    """
    prompt = input("You: ")

    messages = [
        {
            "role": "system",
            "content": "You are a web crawler. Your job is to give the user a URL in JSON format. Respond in the following JSON format: {\"url\": \"<put url here>\"}",
        },
        {
            "role": "user",
            "content": prompt,
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
                        "content": "Your job is to answer the user's question based on the given screenshot...",
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