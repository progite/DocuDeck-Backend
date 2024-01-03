# Backend@Docudeck
## DocuDeck is a centralized tender procurement platform. It supports automated compliance checking of tenders against existing government policies and memorandums. It enables vendors to take part in bids against published tenders. It also supports compliance check of bids against tender specifications

## Follow the following steps to run the backend in local
### 1. pip install -r requirements.txt
### 2. cd to Backend/
### 3. `flask run`

## DocuDeck offers the following endpoints currently 
### 1. /sign-up : registration of new users
### 2. /login : login to application 
### 3. /add-policy : [only admin] add new tender related policies
### 4. /search-policies : fetch related documents against multiple parameters. Implements keyword search
### 5. /add-tender : compliance check of uploaded tender against existing policies
### 6. /publish-tender : publish compliant tender
### 7. /fetch-tenders : fetch all tenders or tenders published by specific authorities
### 8. /add-bid : bid against a published tender
### 9. /add-bid-docs : compliance check of documents uploaded by bidder(vendor) 
### 10. /fetch-bid : fetch all bids against a published tender
### 11. /bid-chatbot : assistance chatbot for bidder
