import fitz
import cv2
import numpy as np
from pdf2image import convert_from_path

# Replace 'input_file.pdf' with the path to your PDF file
pdf_file = "TENDER1.pdf"
# pages = convert_from_path(pdf_file, 500, r"C:\Program Files\poppler-23.11.0\Library\\bin")
pages = fitz.open(pdf_file)

print(pages)


def deskew(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated

def resize_to_full_page(image, target_height=1000):
    # Calculate the aspect ratio
    aspect_ratio = image.shape[1] / image.shape[0]

    # Calculate the new width based on the target height and aspect ratio
    target_width = int(target_height * aspect_ratio)

    # Resize the image while maintaining the aspect ratio
    resized_image = cv2.resize(image, (target_width, target_height))

    return resized_image

# Updated deskew function
def deskew(image):
    # Resize the image to obtain a full-page view
    full_page_image = resize_to_full_page(image)

    return full_page_image

import pytesseract

def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text


# Create a list to store extracted text from all pages
extracted_text = []

from PIL import Image

def pix2np(pix):
    im = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    im = np.ascontiguousarray(im[..., [2, 1, 0]])  # rgb to bgr
    return im

for page in pages:
    pix = page.get_pixmap()
    pix = pix2np(pix)
    
    # Step 2: Preprocess the image (deskew)
    preprocessed_image = deskew(pix)
    
    # Step 3: Extract text using OCR
    text = extract_text_from_image(pix)
    extracted_text.append(text)

print(extracted_text)

import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_dates_and_keywords(text):
    # Process the text with spaCy
    doc = nlp(text)

    # Extract dates
    dates = [ent.text for ent in doc.ents if ent.label_ == 'DATE']

    # Extract keywords (assuming keywords are nouns in this example)
    keywords = [token.text for token in doc if token.pos_ == 'NOUN']

    return dates, keywords


# Lists to store dates and keywords
all_dates = []
all_keywords = []

# Process each text in the list
for text in extracted_text:
    dates, keywords = extract_dates_and_keywords(text)
    all_dates.extend(dates)
    all_keywords.extend(keywords)

# Print all dates together
print("Dates:", all_dates)

# Print all keywords together
print("Keywords:", all_keywords)

import nltk
import re

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

def extract_dates_and_keywords(text):
    # Tokenize the text
    words = nltk.word_tokenize(text)

    # Extract dates using regular expressions
    date_pattern = re.compile(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2},? \d{4})\b')
    dates = [match.group() for match in re.finditer(date_pattern, text)]

    # Extract keywords (assuming keywords are nouns in this example)
    pos_tags = nltk.pos_tag(words)
    keywords = [word for word, pos in pos_tags if pos.startswith('N')]

    return dates, keywords



# Lists to store dates and keywords
all_dates = []
all_keywords = []

# Process each text in the list
for text in extracted_text:
    dates, keywords = extract_dates_and_keywords(text)
    all_dates.extend(dates)
    all_keywords.extend(keywords)

# Print all dates together
print("Dates:", all_dates)

# Print all keywords together
print("Keywords:", all_keywords)

from rake_nltk import Rake
import nltk
nltk.download('stopwords')
r=Rake()
for text in extracted_text:
    r.extract_keywords_from_text(text)
    ranked_phrases = r.get_ranked_phrases()
    print("Keywords for text:")
    print(ranked_phrases[0:10])
    print("-" * 50)  # Separator for better readability
# r.extract_keywords_from_text(extracted_text)
# r.get_ranked_phrases()[0:10]

# Convert the list of paragraphs into a single string
full_paragraph = ','.join(extracted_text)
import re
# Print the result
full_paragraph = re.sub(r'\s+', ' ', full_paragraph)

# Print the result
# print(full_paragraph)

import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Process the paragraph with spaCy
doc = nlp(full_paragraph)

# Extract key phrases
key_phrases = [chunk.text for chunk in doc.noun_chunks]

# Print the result
print("Key Phrases:", key_phrases)

import json
import requests

token_access = "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"
headers = {"Authorization": f"Bearer {token_access}"}

API_URL = "https://api-inference.huggingface.co/models/rsvp-ai/bertserini-bert-base-squad"

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# Get user input for question and context
user_question = input("Enter your question: ")
user_context = full_paragraph

# Query the model with user inputs
output = query({
    "inputs": {
        "question": user_question,
        "context": user_context
    },
})

print(output)

import re

def extract_tender_info(text):
    # Extract date
    date_match = re.search(r'Dated (\d{2}/\d{2}/\d{4})', text)
    date = date_match.group(1) if date_match else None

    # Extract Tender Reference Number
    ref_number_match = re.search(r'Tender Reference Number ([\w/-]+)', text)
    ref_number = ref_number_match.group(1) if ref_number_match else None

    # Extract Tender ID
    tender_id_match = re.search(r'Tender ID (\d{4}_\w+)', text)
    tender_id = tender_id_match.group(1) if tender_id_match else None

    # Extract Department
    department_match = re.search(r'Organisation Chain (.*?)\|', text)
    department = department_match.group(1).strip() if department_match else None

    return date, ref_number, tender_id, department


# Call the function to extract information
date, ref_number, tender_id, department = extract_tender_info(full_paragraph)

# Print the extracted information
print(f"Date: {date}")
print(f"Tender Reference Number: {ref_number}")
print(f"Tender ID: {tender_id}")
print(f"Department: {department}")

