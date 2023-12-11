import base64
import logging

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
