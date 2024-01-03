# 1.
import fitz  # PyMuPDF Extract text from pdf.
import pytesseract
from PIL import Image

def extract_text_from_pdf(pdf_path):
    text = ''
    pdf_document = fitz.open(pdf_path)
    num_pages = pdf_document.page_count

    for page_number in range(num_pages):
        page = pdf_document.load_page(page_number)
        images = page.get_images(full=True)  # Get all images in the page

        if images:
            for img_index, img_info in enumerate(images):
                xref = img_info[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                # Save the image as a temporary file
                temp_image = f"temp_image_{page_number}_{img_index}.png"
                with open(temp_image, 'wb') as temp_file:
                    temp_file.write(image_bytes)

                # Perform OCR on the saved image file
                extracted_text = pytesseract.image_to_string(Image.open(temp_image))
                text += extracted_text + "\n"  # Add a new line after each image's text

                # Remove the temporary image file
                import os
                os.remove(temp_image)

        else:
            text += page.get_text()

    pdf_document.close()
    return text

# 2. chatBot
import json          
import requests

token_access = ""     # replace with your hugging face Token
headers = {"Authorization": f"Bearer {token_access}"}
API_URL = "https://api-inference.huggingface.co/models/rsvp-ai/bertserini-bert-base-squad"

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# 3. Extract important info date,ministry,...
import re
import spacy
from dateutil.parser import parse

def extract_date(paragraph):
    date_pattern = r"\b(?:\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th) of [A-Za-z]+\s*\d{4}|\b[A-Za-z]+\s*\d{1,2})\b"
    matches = re.findall(date_pattern, paragraph)
    parsed_dates = []
    
    for match in matches:
        try:
            parsed_dates.append(parse(match))
        except ValueError:
            # Ignore parsing errors for invalid formats
            pass
    return parsed_dates[0]

def extract_ministry(text):
    # Regular expression to match Ministry of ...
    ministry_pattern = re.compile(r'Ministry of([^\n\d]+)')

    # Use re.search() to find the first occurrence of the ministry pattern
    ministry_match = re.search(ministry_pattern, text)

    # Return the ministry text up to the first occurrence if found, otherwise return None
    return ministry_match.group(1).strip().split('\n')[0] if ministry_match else None

def extract_tender_info(text):

    # Extract Tender Reference Number
    ref_number_match = re.search(r'Tender Reference Number ([\w/-]+)', text)
    ref_number = ref_number_match.group(1) if ref_number_match else None

    # Extract Tender ID
    tender_id_match = re.search(r'Tender ID (\d{4}_\w+)', text)
    tender_id = tender_id_match.group(1) if tender_id_match else None

    # Extract keywords using spaCy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    key_phrases = [chunk.text for chunk in doc.noun_chunks]

    return ref_number, tender_id, key_phrases

# 4. Summary
from sumy.parsers.plaintext import PlaintextParser  # it gives summary of text in input number of lines.
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

def generate_summary(text_data, num_sentences):
    """
    Generates a summary from text data using TextRank summarization.
    Args:
    - text_data (str): The text data to summarize.
    - num_sentences (int): The number of sentences in the summary.
    Returns:
    - summary (str): The generated summary.
    """
    parser = PlaintextParser.from_string(text_data, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    summary = summarizer(parser.document, num_sentences)
    return summary

# 5. give 5 sentences matching with keyword.
import torch
from transformers import BertTokenizer, BertModel
from scipy.spatial.distance import cosine

# Load pre-trained model and tokenizer
model_name = 'bert-base-uncased'  # You can try other models from Hugging Face's model hub
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)

# Function to get sentence embeddings using BERT
def get_bert_embeddings(sentence):
    inputs = tokenizer(sentence, return_tensors='pt', max_length=512, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()  # Squeeze to make it 1D
    return embeddings

# Function to find most similar sentences based on BERT embeddings
def find_similar_sentences_bert(text, keyword, threshold=0):
    keyword_embedding = get_bert_embeddings(keyword)
    sentences = text.split("\n")  # Split by sentences assuming sentences end with period followed by space

    similar_sentences = []
    for sentence in sentences:
        sentence_embedding = get_bert_embeddings(sentence)
        similarity = 1 - cosine(keyword_embedding, sentence_embedding)  # Calculate cosine similarity
        if similarity > threshold:
            # print(f"Sentence: {sentence} - Similarity: {similarity}")
            similar_sentences.append((sentence, similarity))

    # Sort sentences by similarity
    similar_sentences = sorted(similar_sentences, key=lambda x: x[1], reverse=True)

    return similar_sentences[:5]