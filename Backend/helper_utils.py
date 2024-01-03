import datetime
from dateutil import parser

def extract_date(date: str):
    # parsed_date = parser.parse(date, fuzzy=True)
    # converted_date = parsed_date.strftime('%Y-%m-%d')
    print("DEBUGGGGG")
    # return converted_date
    # if datetime.datetime.strptime()
    try:
        return datetime.datetime.strptime(date, "%Y-%m-%d")
    except excep:
        print("debug enters hereeee")
        date = datetime.datetime.strptime(date, '%d.%m.%Y')
        return date.strftime('%Y-%m-%d')
        # return 

import base64

def image_to_base64(image_path):
    with open(image_path, 'rb') as image_file:
        # Read the binary image data
        binary_image = image_file.read()

        # Encode binary data as base64
        base64_encoded_image = base64.b64encode(binary_image).decode('utf-8')
    return base64_encoded_image

# image_path = '7.pdf'
# base64_encoded_image = image_to_base64(image_path)
# with open("encoded_img.txt", "w") as file:
#     file.write(base64_encoded_image)