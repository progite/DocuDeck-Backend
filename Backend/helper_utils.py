import datetime
from dateutil import parser

def extract_date(date: str):
    try:
        return datetime.datetime.strptime(date, "%Y-%m-%d")
    except Exception as e:
        date = datetime.datetime.strptime(date, '%d.%m.%Y')
        return date.strftime('%Y-%m-%d')
    
import base64

def image_to_base64(image_path):
    with open(image_path, 'rb') as image_file:
        # Read the binary image data
        binary_image = image_file.read()

        # Encode binary data as base64
        base64_encoded_image = base64.b64encode(binary_image).decode('utf-8')
    return base64_encoded_image
