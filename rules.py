# -*- coding: utf-8 -*-
"""SIH-2023.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1jiVJ36Kj2xzXrKdI9An-OsZi6pSDHWFQ
"""

from google.colab import drive
drive.mount('/content/drive')

!pip install pdf2image

!apt-get install poppler-utils

from pdf2image import convert_from_path

# Replace 'input_file.pdf' with the path to your PDF file
pdf_file = '/content/drive/MyDrive/SIH-2023/tender1.pdf'
pages = convert_from_path(pdf_file)

import cv2
import numpy as np

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

!pip install pytesseract

import pytesseract

def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text

!apt-get install tesseract-ocr

# Create a list to store extracted text from all pages
extracted_text = []

for page in pages:
    # Step 2: Preprocess the image (deskew)
    preprocessed_image = deskew(np.array(page))

    # Step 3: Extract text using OCR
    text = extract_text_from_image(preprocessed_image)
    extracted_text.append(text)

extracted_text

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

import numpy as np
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense



# Convert keywords to sequences
tokenizer = Tokenizer()
tokenizer.fit_on_texts(all_keywords)
total_words = len(tokenizer.word_index) + 1

input_sequences = []
for keyword in all_keywords:
    sequence = tokenizer.texts_to_sequences([keyword])[0]
    input_sequences.append(sequence)

# Pad sequences
max_sequence_length = max(len(seq) for seq in input_sequences)
padded_input_sequences = pad_sequences(input_sequences, maxlen=max_sequence_length, padding='post')

# Create input-output pairs for training
x = padded_input_sequences[:, :-1]
y = padded_input_sequences[:, 1:]

# Build the LSTM model
model = Sequential()
model.add(Embedding(total_words, 10, input_length=max_sequence_length - 1))
model.add(LSTM(100, return_sequences=True))
model.add(Dense(total_words, activation='softmax'))

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Train the model
model.fit(x, y, epochs=100, verbose=0)

import random

# Function to generate phrases
def generate_phrase(seed_text, next_words, model, tokenizer, max_sequence_length):
    for _ in range(next_words):
        sequence = tokenizer.texts_to_sequences([seed_text])[0]
        sequence = pad_sequences([sequence], maxlen=max_sequence_length - 1, padding='post')

        # Get the predicted word probabilities
        predicted_probs = model.predict(sequence)[0]

        # Get the index of the word with the maximum probability
        predicted_word_index = np.argmax(predicted_probs)

        # Check if the index is within the expected range
        if predicted_word_index in tokenizer.index_word:
            # Convert predicted_word_index to a scalar value
            predicted_word_index = predicted_word_index.item()

            predicted_word = tokenizer.index_word[predicted_word_index]
            seed_text += " " + predicted_word
        else:
            # Handle the case where the index is out of bounds
            print(f"Warning: Index {predicted_word_index} not found in tokenizer dictionary.")
            break

    return seed_text

# Generate phrases for each keyword
generated_phrases = []
for keyword in all_keywords:
    generated_phrase = generate_phrase(seed_text=keyword, next_words=3, model=model, tokenizer=tokenizer, max_sequence_length=max_sequence_length)
    generated_phrases.append(generated_phrase)

# Print the results
for keyword, phrase in zip(all_keywords, generated_phrases):
    print(f"{keyword}: {phrase}")

!pip install rake-nltk

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

