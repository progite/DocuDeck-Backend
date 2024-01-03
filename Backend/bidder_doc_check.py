# -*- coding: utf-8 -*-
import os


import fitz
from PIL import Image
import pytesseract
import re

def extract_text_from_pdf(pdf_path, output_image_path):
    # Open the PDF file
    doc = fitz.open(pdf_path)

    # Load the first page
    page = doc.load_page(0)

    # Get the pixmap of the page
    pix = page.get_pixmap()

    # Save the pixmap as an image
    pix.save(output_image_path)

    # Close the PDF document
    doc.close()

def extract_text_after_pan_card(text):
    # Define the pattern to match the text after "Permanent Account Number Card"
    pattern = r"Permanent Account Number Card\s+([^\s]+)"

    # Search for the pattern in the text
    match = re.search(pattern, text)

    # If a match is found, return the extracted text; otherwise, return None
    if match:
        extracted_text = match.group(1)
        return extracted_text
    else:
        return None

#PROCESS PAN CARD
def process_pan_card(pdf_path):
    # Extract text from PDF and save as an image
    output_image_path = "output.png"
    extract_text_from_pdf(pdf_path, output_image_path)

    # Extract text from the image
    extracted_text = extract_text_from_image(output_image_path)

    # Extract PAN Card number from the text
    pan_card_number = extract_text_after_pan_card(extracted_text)

    # Check if the PAN Card number has the correct length
    if pan_card_number and len(pan_card_number) == 10:
        return "Correct"
    else:
        return "Incorrect"

# Example usage
# pdf_path = "/content/drive/MyDrive/Pan_Card.pdf"  # Replace with the actual path to your PDF file
# process_pan_card(pdf_path)


#AADHAR CORRECTNESS
def process_pdf_and_check_correctness(pdf_path):
    # Extract text from the first page of the PDF
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap()
    output_image_path = 'output.png'
    pix.save(output_image_path)
    doc.close()

    # Extract text from the image
    extracted_text = extract_text_from_image(output_image_path)

    # Find all numbers in the text (excluding date formats like dd/mm/yyyy and yyyy-mm-dd)
    all_numbers = re.findall(r'\b(?<!\d[-./])\d+\b', extracted_text)

    # Identify numbers occurring more than once
    duplicates = {num for num in all_numbers if all_numbers.count(num) > 1}

    # Display the duplicate numbers
    duplicates_side_by_side = ' '.join(duplicates)
    aadhaar_present =  "aadhaar" in extracted_text.lower()


    # Check correctness based on the specified condition
    if len(duplicates_side_by_side) == 14 or aadhaar_present:
        return "Correct"
    else:
        return "Incorrect"

def extract_text_from_image(pdf_path):
    # Open the image
    image = Image.open(pdf_path)

    # Use pytesseract to perform OCR on the image
    text = pytesseract.image_to_string(image)

    return text

# Example usage
# pdf_path = "/content/drive/MyDrive/Aadhar.pdf"
# result = process_pdf_and_check_correctness(pdf_path)

# print("Result:", result)