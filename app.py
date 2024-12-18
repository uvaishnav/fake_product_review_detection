# Library imports
import uvicorn
from fastapi import FastAPI, HTTPException
import joblib
import nltk  # Natural Language Toolkit
from nltk.corpus import stopwords  # For removing stopwords
from nltk.stem import WordNetLemmatizer  # For lemmatizing words
import tensorflow as tf
from tensorflow.keras.models import load_model  # For loading the LSTM model
from config import Review

# Download NLTK data files (if not already downloaded)
nltk.download('stopwords')
nltk.download('wordnet')

# Create the app object
app = FastAPI()

# Load the tokenizer
tokenizer = joblib.load('lstm_tokenizer.pkl')

# Load the LSTM model
model = load_model('best_lstm_model.h5')

@app.get('/')
def index():
    return {'message': 'You detect fake reviews here!'}

def clean_text(text):
    """
    Cleans the input text by performing the following operations:
    1. Converts the text to lowercase.
    2. Removes all non-alphanumeric characters except spaces.
    3. Removes stopwords (common words that do not contribute much meaning).
    4. Lemmatizes the words (reduces words to their base or root form).

    Args:
        text (str): The input text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    text = text.lower()
    text = ''.join([c for c in text if c.isalnum() or c.isspace()])
    text = ' '.join([lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words])
    return text

max_sequence_length = 100

@app.post('/predict')
def predict(review: Review):
    """
    Predicts whether a given review is fake or real.
    Args:
        review (Review): An instance of the Review class containing the review text.
    Returns:
        dict: A dictionary containing the prediction ('Fake review' or 'Real review') 
              and the confidence score (as a percentage).
    Raises:
        HTTPException: If there is an error processing the review.
    Notes:
        The line `prediction = float(model.predict(review_padded)[0][0])` is important 
        because it extracts the prediction from the model's output and converts it to a 
        scalar float value, which is then used to determine if the review is fake or real.
    """
    try:
        review_text = review.dict()['review']
        clean_review = clean_text(review_text)
        review_sequence = tokenizer.texts_to_sequences([clean_review])
        review_padded = tf.keras.preprocessing.sequence.pad_sequences(
            review_sequence, 
            maxlen=max_sequence_length, 
            padding='post'
        )
        
        # Get prediction and convert to scalar
        prediction = float(model.predict(review_padded)[0][0])
        
        return {
            'prediction': 'Fake review' if prediction > 0.5 else 'Real review',
            'confidence': round(prediction * 100, 2)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing review: {str(e)}"
        )

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)

# Run the app with the following command:
# uvicorn app:app --reload
