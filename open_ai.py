from openai import OpenAI
import base64 
import logging
import os
from screenshot import take_screenshot
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
    
def get_openai_response(url, prompt, messages):
    exitcode, output = take_screenshot(url)

    if not os.path.exists("screenshot.jpg"):
        logging.warning("ERROR: Trying different URL")
        messages.append({
            "role": "user",
            "content": "I was unable to crawl that site. Please pick a different one."
        })
        return messages

    b64_image = image_b64("screenshot.jpg")
    if not b64_image:
        return messages

    # This part of the script processes the screenshot and uses the OpenAI model to get answers.

    # Convert the screenshot to a base64 encoded string.
    b64_image = image_b64("screenshot.jpg")
    if not b64_image:
        return messages

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
        return messages

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

    return messages
