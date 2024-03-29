# -*- coding: utf-8 -*-
import requests
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import spacy

from sklearn.feature_extraction.text import CountVectorizer
from sumy.parsers.plaintext import PlaintextParser  # it gives summary of text in input number of lines.
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import datetime
import fitz  # PyMuPDF Extract text from pdf.
import pytesseract
from PIL import *
from PIL import Image, ImageEnhance
import re
import torch
from transformers import BertTokenizer, BertModel
from scipy.spatial.distance import cosine

# Load pre-trained model and tokenizer
model_name = 'bert-base-uncased'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)

token_access = ""     # replace with your hugging face Token
headers = {"Authorization": f"Bearer {token_access}"}

API_URL = "https://api-inference.huggingface.co/models/rsvp-ai/bertserini-bert-base-squad"

def calculate_similarity_and_sort(df1_path, embeddings_tender):
    # Load the first CSV file
    df1 = pd.read_csv(df1_path)

    # Convert the 'Rules' column to strings to handle non-string values
    df1['Rules'] = df1['Rules'].astype(str)

    # Initialize an empty dictionary to store rules policy-wise
    rules_dict_db1 = {}

    # Loop through each row in the first database
    for _, row in df1.iterrows():
        policy = row['Policy']
        rules = row['Rules']

        # If the policy is not in the dictionary, add it with an empty list
        if policy not in rules_dict_db1:
            rules_dict_db1[policy] = []

        # Append the current rule to the list for the current policy
        rules_dict_db1[policy].append(rules)

    # Load the second CSV file
    # df2 = pd.read_csv(df2_path)

    # # Convert the 'Rules' column to strings in the second database as well
    # df2['Rules'] = df2['Rules'].astype(str)

    # Concatenate all rules from the second database into a single string
    # corpus_db2 = ' '.join(df2['Rules'])
    corpus_db2 = ','.join(embeddings_tender)
    print("NEEDED TYPE PLEASE", corpus_db2)
    # Initialize an empty list to store results
    results = []

    # Loop through each policy in the first database
    for policy, rules_db1 in rules_dict_db1.items():
        # Initialize a dictionary to store results for the current policy
        result_for_policy = {'Policy': policy, 'Rules': rules_db1}

        # Initialize CountVectorizer to convert text data to a matrix of token counts
        vectorizer = CountVectorizer().fit_transform([' '.join(rules_db1), corpus_db2])

        # Calculate cosine similarity
        cosine_sim = cosine_similarity(vectorizer)

        # Extract similarity score for the current policy
        overall_score = cosine_sim[1, 0]  # Correct indexing

        # Add the overall score to the result dictionary
        result_for_policy['Overall Similarity Score'] = overall_score

        # Append the results for the current policy to the main list
        results.append(result_for_policy)

    # Sort the results based on the similarity scores in descending order
    sorted_results = sorted(results, key=lambda x: x['Overall Similarity Score'], reverse=True)

    return sorted_results

def complaince_checking_updated(tender_path):
        # Example usage
    # df1_path = pd.read_csv(r'rules_2_Power_Ministry.csv')
    tender_extract, num_pages = extract_text_from_pdf(tender_path)
    summarized_tender = Summarize_doc(tender_extract, num_pages)
    embeddings_tender = list(str(sentence) for sentence in summarized_tender)
    print("tender doc type", type(summarized_tender))
    
    # df1_path = '/content/drive/MyDrive/rules.csv'
    # df2_path = '/content/drive/MyDrive/rules_1.csv'
    # sorted_results = calculate_similarity_and_sort(df1_path, df2_path)
    df1_path = 'rules_2_Power_ministry.csv'
    sorted_results = calculate_similarity_and_sort(df1_path, embeddings_tender)
    # Display the sorted results
    
    compliance_scores = {}
    for result in sorted_results:
        compliance_scores[result['Policy']] = result['Overall Similarity Score']
        # print(f"Policy: {result['Policy']}")
        # print(f"Overall Similarity Score with Second Database: {result['Overall Similarity Score']}")
        # print("\n")
    return compliance_scores

def bid_chatbot(user_query: str, eligibility: str):
    query = {"question": user_query,
             "context": eligibility
             }
    print("QUERY", query)
    response = requests.post(API_URL, headers=headers, json=query)
    print("RESPONSE JSON", response)
    return  response.json()

# Function to get BERT embeddings for a sentence
def get_bert_embeddings(sentence):
    inputs = tokenizer(sentence, return_tensors='pt', max_length=512, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
    return embeddings

# Function to find similarity between a keyword and dictionary values based on BERT embeddings
def find_similarity_with_dict(keyword, my_dict):
    keyword_embedding = get_bert_embeddings(keyword)

    similarity_scores = {}
    for key in my_dict:
        value = my_dict[key]
    # for key, value in my_dict.items():
        value_embedding = get_bert_embeddings(value)
        similarity = 1 - cosine(keyword_embedding, value_embedding)
        similarity_scores[key] = similarity

    # Sort the dictionary by similarity scores and get the top 3 keys
    similar_keys = sorted(similarity_scores, key=similarity_scores.get, reverse=True)[:3]
    return similar_keys

def keyword_similarity(keywords, tags):
    matching_policy_ids = []
    for keyword in keywords:
        matching_policy_ids.extend(find_similarity_with_dict(keyword, tags))
    return matching_policy_ids

nlp = spacy.load("en_core_web_sm")

def extract_text_from_Front_pages(pdf_path):
    pdf_document = fitz.open(pdf_path)
    
    # Extract the first page
    first_page = pdf_document.load_page(0)
    
    # Convert the first page to an image
    first_page_image = first_page.get_pixmap()

    # Save the image as a temporary file
    temp_image = "temp_first_page.png"
    first_page_image.save(temp_image, "png")
    
    # Enhance image quality (example: contrast)
    img = Image.open(temp_image)
    enhanced_img = ImageEnhance.Contrast(img).enhance(2.0)  # Adjust the enhancement factor as needed
    enhanced_img.save(temp_image)
    
    # Close the PDF document
    pdf_document.close()
    
    # Perform OCR on the enhanced image file
    extracted_text = pytesseract.image_to_string(Image.open(temp_image), lang='eng')  # Set the language if needed
    
    # Remove the temporary image file
    import os
    os.remove(temp_image)
    
    return extracted_text

def detect_document_type(text):
    # Process the text using spaCy
    doc = nlp(text.lower())  # Convert text to lowercase for case-insensitive matching

    # Define keywords for each document type
    keywords = {
        "Gazette": ["gazette"],
        "Circular": ["circular"],
        "Rules": ["rule"],
        "Order": ["order"],
        "Manual": ["manual"],
        "OfficeMemorandum": ["memorandum"]
    }

    # Check for keyword matches in the document
    for doc_type, words in keywords.items():
        if all(word in doc.text for word in words):
            return doc_type

    return "Unknown"  

def extract_first_date(text):
    # text = ','.join(text)
    # Regular expression to match various date formats
    date_pattern = re.compile(r'(\d{1,2}(?:[./-]\d{1,2}[./-]\d{2,4}|th\s*\w+\s*\d{4}|/\d{1,2}/\d{2,4}|-\d{1,2}-\d{2,4}|\s+\w{3,}\s+\d{2,4}))')

    # Function to find the first correct date
    def find_first_date(text):
        match = re.search(date_pattern, text)
        return match.group(1) if match else None

    # Use the find_first_date function to get the first correct date
    first_date = find_first_date(text)

    return first_date

def extract_ministry(text):
    # Regular expression to match Ministry of ...
    ministry_pattern = re.compile(r'Ministry of([^\n\d]+)')

    # Use re.search() to find the first occurrence of the ministry pattern
    ministry_match = re.search(ministry_pattern, text)

    # Return the ministry text up to the first occurrence if found, otherwise return None
    return ministry_match.group(1).strip().split('\n')[0] if ministry_match else None

def extract_policy_info(file_path):
    pdf_text, num_pages = extract_text_from_pdf(file_path)
    # text=extract_text_from_pdf(file_path)
    front_text = extract_text_from_Front_pages(file_path)
    
    doc_type=detect_document_type(front_text)
    
    print("debug", type(pdf_text))
    date = extract_first_date(pdf_text)
    print("reaches hereeeee")
    
    department = extract_ministry(pdf_text)
    # Extract keywords using spaCy
    # nlp = spacy.load("en_core_web_sm")
    # os.sleep()
    # doc = nlp(pdf_text)
    # key_phrases = [chunk.text for chunk in doc.noun_chunks]
    key_phrases = []
    print("ENTERS TILL HERE", type(key_phrases))
    date = datetime.datetime.strptime(date, '%m/%d/%Y')

    # Format the date as 'year-month-date'
    date = date.strftime('%Y-%m-%d')

    return date, doc_type, department, key_phrases[:20]

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
                os.remove(temp_image)

        # Always perform OCR for text extraction
        extracted_text = page.get_text()
        text += extracted_text + "\n"  # Add a new line after each page's text

    pdf_document.close()
    return text, num_pages

def Summarize_doc(pdf_text, num_pages):
    # Initialize parser and tokenizer
    parser = PlaintextParser.from_string(pdf_text, Tokenizer("english"))

    # Initialize TextRank summarizer
    summarizer = TextRankSummarizer()

    # Generate summary
    return summarizer(parser.document, num_pages*10)
    summary = summarizer(parser.document, num_pages*10)  # Provide the number of sentences in the summary
    summary_sentences = [str(sentence) for sentence in summary]

# Convert summary sentences into a single string
    summary_text = ' '.join(summary_sentences)

    # Initialize TF-IDF vectorizer
    vectorizer = TfidfVectorizer()

    # Fit and transform the summary text into a TF-IDF vector representation
    summary_vectors = vectorizer.fit_transform([summary_text])

    # Get the TF-IDF matrix (sparse matrix in this case)
    tfidf_matrix = summary_vectors.toarray()

    return tfidf_matrix

def extract_text_between_keywords(paragraph, start_keyword, end_keyword, to_find):
    pattern = re.compile(f'{start_keyword}(.*?){end_keyword}', re.DOTALL | re.IGNORECASE)
    match = pattern.search(paragraph)

    if match:
        extracted_text = match.group(1).strip()
        # Remove ".pdf" from the extracted text
        if to_find == 'pdf':
            extracted_text = extracted_text.replace('.pdf', '')
        return extracted_text
    else:
        return "Pattern not found in the paragraph."

def find_tender_requirements(tender_path):
    start_keywords = ['Cover Details', 'Qualification']
    end_keywords = ['Tender Fee Details', 'Independent']
    to_find = ['pdf', 'eligibility']
    
    print("TENDER PATH", tender_path)
    pdf_text, num_pages = extract_text_from_pdf(tender_path)
    extracted = {}
    for idx in range(2):
        extracted[to_find[idx]] = extract_text_between_keywords(pdf_text, start_keywords[idx], end_keywords[idx], to_find[idx])    
    return extracted

def encode_sentences(sentences, vectorizer):
    # Transform sentences using TF-IDF vectorizer
    embeddings = vectorizer.transform(sentences).toarray()
    return embeddings

def compare_policy_rule_embeddings(embeddings_database1, embeddings_database2):
    # Compare policy embeddings from the first database with rule embeddings from the second database using cosine similarity
    print("[DEBUG], em_tender", embeddings_database1.shape[0], embeddings_database2.shape[0])
    similarity_matrix = cosine_similarity(embeddings_database1, embeddings_database2.reshape((1, 40)))
    return similarity_matrix

import pandas as pd
from sklearn.metrics import confusion_matrix
from difflib import SequenceMatcher

# Function to calculate similarity score using SequenceMatcher
def get_similarity_score(s1, s2):
    return SequenceMatcher(None, s1, s2).ratio()

def find_similarity(tender_path):
    # Assuming you have Excel files with columns named 'Policy' and 'Rules'
    # df_database1 = pd.read_csv(r'rules_1.csv')
    df_database2 = pd.read_csv(r'rules_2_Power_ministry.csv')
    df_database2.dropna()
    tender_extract, num_pages = extract_text_from_pdf(tender_path)
    embeddings_tender = list(Summarize_doc(tender_extract, num_pages))
    # tender_summary = list(tender_summary)
    
    print("[DEBUG] NUMBER OF TENDER RULES", len(embeddings_tender))
    
    similarity_scores = []
    for policy_db1 in embeddings_tender:
    # Calculate similarity scores for the current policy against all rules in the first database
        # scores_policy = []
        # for policy_db1 in embeddings_tender:
        #     policy_db1 = str(policy_db1)
        #     # policy_db1 = policy_db1.text
        #     # print(type(policy_db1), "[DEBUD}", type(policy_db2))
        #     scores_policy.append(get_similarity_score(policy_db2, policy_db1))
        # return
        scores_for_policy = [get_similarity_score(policy_db2, str(policy_db1)) for policy_db2 in df_database2['Rules']]
    
        # Take the maximum similarity score for the current policy
        max_score = max(scores_for_policy)
        
        # Append the maximum similarity score to the list
        similarity_scores.append(max_score)

    # print("similarity score", similarity_scores)
    scores_map = {}
    for i, value in enumerate(similarity_scores, start=1):
        scores_map[f"Policy {i}"] = f"{value:.8f}" 
        # print(f"Policy {i} : {value:.8f}")
    return scores_map
    # print("[DEBUGGG]", type(tender_summary))
    # for index, rule in enumerate(df_database2['Rules']):
    # # Drop NaN values for each rule
    #     df_database2['Rules'][index] = rule.dropna()
    # for rule in df_database2['Rules']:
    #     # rule.dropna()
    #     print('[DEBUGGGGG]', rule, type(rule))
    
    # print(tender_extract)
    
    # Combine 'Rules' from both databases for f itting the vectorizer
    # all_rules = df_database1['Rules'].tolist() + df_database2['Rules'].tolist()
    all_rules =  df_database2['Rules'].tolist()
    
    # print(all_rules)
    with open("test.txt", "w", encoding='utf-8') as file:
        file.write(str(all_rules))
    
    # Create and fit TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    vectorizer.fit(all_rules)

    # print("[DEBUG] RULES DB", df_database2)
    # Encode 'Rules' using the same vectorizer
    # embeddings_database1 = encode_sentences(df_database1['Rules'].tolist(), vectorizer)
    embeddings_database2 = encode_sentences(df_database2['Rules'].tolist(), vectorizer)
    print("debug tender type", type(embeddings_tender))
    print("debug type of embedding", type(embeddings_database2))
    # embeddings_tender = encode_sentences(list(tender_summary), vectorizer)
    # Compare policy embeddings with 'Rules' from the second database
    
    similarity_matrix = compare_policy_rule_embeddings(embeddings_tender, embeddings_database2)

    # Calculate average similarity for each policy against all rules in the second database
    average_similarity_per_policy = np.mean(similarity_matrix, axis=1)

    # Create a DataFrame with Policy and its corresponding average similarity
    # result_df = pd.DataFrame({'Policy': df_database1['Policy'], 'Average_Similarity': average_similarity_per_policy})

    # Display the result DataFrame
    print("Policy - Average Similarity:")
    # print(result_df)
