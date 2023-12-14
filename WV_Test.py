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
            ["node", "screenshot.cjs", url, "viewport"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logging.error(f"Screenshot script failed with exit code {result.returncode}")
            logging.error(f"Script output: {result.stdout}")
            logging.error(f"Script error output: {result.stderr}")
        return result.returncode, result.stdout
    except Exception as e:
        logging.error(f"Error taking screenshot: {e}")
        return None, None
    
def main():
    """
    The main function where the script execution begins.
    """
    while True:
        # Prompt the user to input a URL directly.
        url = input("Please enter a URL or type 'exit' to quit: ")

        if url.lower() == 'exit':
            break

        logging.info(f"Crawling {url}")

        exitcode, output = take_screenshot(url)

        if not os.path.exists("screenshot.jpg"):
            logging.warning("ERROR: Unable to take a screenshot of the provided URL")
            continue

        b64_image = image_b64("screenshot.jpg")
        if not b64_image:
            continue

        while True:
            user_prompt = input("Please enter your question or prompt related to the website: ")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{b64_image}",
                        },
                        {
                            "type": "text",
                            "text": user_prompt,
                        }
                    ]
                }
            ]

            # Try to get a response from the OpenAI model using the screenshot.
            try:
                response = model.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": "Your job is to answer the user's question based on the given screenshot of a website. Answer the user as an assistant. If you can't answer the question, simply respond with the code `ANSWER_NOT_FOUND` and nothing else.",
                        }
                    ] + messages,
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
                retry = input("Would you like to try another question for the same picture? (yes/no): ")
                if retry.lower() != 'yes':
                    break  # Exit the inner loop if the user doesn't want to retry.
            else:
                # If an answer is found, print it.
                print(f"GPT: {message_text}")

                # Ask if the user wants to try another question or a new URL.
                next_action = input("Would you like to try another question for this picture or a new URL? (question/new/exit): ")
                if next_action.lower() == 'exit':
                    return  # Exit the program.
                elif next_action.lower() == 'new':
                    break  # Exit the inner loop to input a new URL.
                # Continue the inner loop if the user wants to try another question.
                
# This line checks if the script is being run as the main program and not being imported.
if __name__ == "__main__":
    main()
