import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to process input text
def process_input_text(input_text):
    if not input_text.strip():  # Check if input_text is empty or only whitespace
        return []  # Return an empty list if input_text is empty

    lower_input_text = input_text.lower()
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz '

    cleaned_text = ""

    for char in lower_input_text:
        if char in allowed_chars:
            cleaned_text += char
        else:
            cleaned_text += " "

    cleaned_text = ' '.join(cleaned_text.split())  # Remove extra spaces

    words_after = list(set(cleaned_text.split()))  # Get unique words after cleaning

    return words_after

# Define the path to your CSV file
csv_file_path = r"C:\Users\style\Downloads\Modified URLs.csv"

# Example input text (replace with your actual input mechanism)
input_text = """(
fuck suck mock dick
   )"""

# Process input text using your function
words_after = process_input_text(input_text)

# Check if there are no words after processing
if not words_after:
    print("Input text is empty or contains no valid words. Exiting script.")
else:
    # Verify that only allowed characters (a-z) and unique words are present
    if not all(word.isalpha() for word in words_after):
        raise ValueError("Input words must only contain lowercase letters (a-z)")

    # Split the input string into a list of individual words
    search_words = words_after

    # Combine the search words into a single regex pattern allowing for specified delimiters or word boundaries
    delimiters = r'(?:[ //./-/_\s])'
    search_pattern = '|'.join([rf'((?<!\w){re.escape(word)}(?!\w)|{delimiters}{re.escape(word)}{delimiters})' for word in search_words])

    # Function to check if a line contains any of the search words
    def contains_search_words(line):
        return bool(re.search(search_pattern, line, re.IGNORECASE))

    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)

    # Check each row in the DataFrame for the search words and print matching words
    found_words = set()  # Set to store found words

    for index, row in df.iterrows():
        for cell in row:
            if contains_search_words(str(cell)):
                for word in search_words:
                    if re.search(rf'((?<!\w){re.escape(word)}(?!\w)|{delimiters}{re.escape(word)}{delimiters})', str(cell), re.IGNORECASE):
                        found_words.add(word)

    if found_words:
        print("Words found:", ', '.join(found_words))
    else:
        print("No matching words found.")

    # Now use the found words for Bangla meaning search
    def search_online(word):
        original_word = word
        if word.endswith('s'):
            word = word[:-1]  # Remove the 's' at the end
        
        url = f"https://www.english-bangla.com/dictionary/{word}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for attempt in range(3):  # Retry up to 3 times
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 404:
                    return f"{original_word} = not found online"
                else:
                    content = response.text
                    soup = BeautifulSoup(content, 'html.parser')
                    span_tags = soup.find_all('span', class_='format1')
                    
                    if not span_tags:
                        alt_meaning_tag = soup.find('span', class_='meaning')
                        if alt_meaning_tag:
                            alt_meaning_text = alt_meaning_tag.text.strip()
                            return f"{original_word} = {alt_meaning_text.split(' ', 1)[-1].strip()}"
                        else:
                            return f"{original_word} = not found online"
                    else:
                        meanings = [span.text.strip().split(' ', 1)[-1].strip() for span in span_tags]
                        return f"{original_word} = {'; '.join(meanings)}"
            except requests.RequestException as e:
                if attempt < 2:
                    continue
                else:
                    return f"{original_word} = error {e}"

    # Main function to handle word search
    def search_meanings(words):
        allowed_chars = set('abcdefghijklmnopqrstuvwxyz ')

        # Filter input text based on allowed characters, replacing disallowed characters with spaces
        filtered_words = []
        for word in words:
            filtered_word = ''.join(char if char in allowed_chars else ' ' for char in word.lower())
            filtered_word = ' '.join(filtered_word.split())  # Remove extra spaces
            if filtered_word:  # Only add non-empty words
                filtered_words.extend(filtered_word.split())  # Split into individual words
        unique_words = list(set(filtered_words))  # Remove duplicates

        if not unique_words:
            print("No valid words to search.")
            return

        results = set()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(search_online, word): word for word in unique_words}
            for future in as_completed(futures):
                result = future.result()
                if "not found" not in result and "error" not in result:
                    results.add(result)

        # Print search results
        for result in results:
            print(result)

    # Start the word search
    search_meanings(found_words)
