import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to process input text (unchanged)
def process_input_text(input_text):
    if not input_text.strip():
        return []

    lower_input_text = input_text.lower()
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz '

    cleaned_text = ""
    for char in lower_input_text:
        if char in allowed_chars:
            cleaned_text += char
        else:
            cleaned_text += " "

    cleaned_text = ' '.join(cleaned_text.split())
    words_after = list(set(cleaned_text.split()))

    return words_after

# Define delimiters globally
delimiters = r'(?:[ //./-/_\s])'

# Function to define search pattern
def define_search_pattern(words):
    return '|'.join([rf'((?<!\w){re.escape(word)}(?!\w)|{delimiters}{re.escape(word)}{delimiters})' for word in words])

# Define the path to your CSV file (unchanged)
csv_file_path = r"C:\Users\style\Downloads\Modified URLs.csv"

# Example input text (unchanged)
input_text = """(
Donald Trump called on Americans Sunday to stand united after he was injured in an assassination attempt – a shocking incident that opened a dark new chapter in an already polarized US presidential race.

The 78-year-old former president was hit in the ear at a campaign rally in Butler, Pennsylvania, while the shooter and a bystander were killed and two spectators critically injured in the worst act of US political violence in decades.

"In this moment, it is more important than ever that we stand United," Trump said in a statement on his Truth Social network, adding that Americans should not allow "Evil to win".

The Republican added that it was "God alone who prevented the unthinkable from happening" and that he would "FEAR NOT".

The gunman has been identified as 20-year-old Thomas Matthew Crooks of Bethel Park, Pennsylvania, about an hour's drive from the rally site, according to an FBI statement early Sunday.
   )"""

# Process input text using your function (unchanged)
words_after = process_input_text(input_text)

if not words_after:
    print("Input text is empty or contains no valid words. Exiting script.")
else:
    if not all(word.isalpha() for word in words_after):
        raise ValueError("Input words must only contain lowercase letters (a-z)")

    search_words = words_after

    # Define search pattern using processed words
    search_pattern = define_search_pattern(search_words)

    # Function to check if a line contains any of the search words (now defined with search_pattern available)
    def contains_search_words(line):
        return bool(re.search(search_pattern, line, re.IGNORECASE))

    # Read the CSV file into a DataFrame (unchanged)
    df = pd.read_csv(csv_file_path)

    found_words = set()

    # Check each row in the DataFrame for the search words and add found words to the set (unchanged)
    for index, row in df.iterrows():
        for cell in row:
            if contains_search_words(str(cell)):
                for word in search_words:
                    if re.search(rf'((?<!\w){re.escape(word)}(?!\w)|{delimiters}{re.escape(word)}{delimiters})', str(cell), re.IGNORECASE):
                        found_words.add(word)

    if not found_words:
        print("No matching words found in the CSV file.")
    else:
        print("Found words:", ', '.join(found_words))

        # Function to search for meanings online (unchanged)
        def search_online(word):
            original_word = word
            if word.endswith('s'):
                word = word[:-1]

            url = f"https://www.english-bangla.com/dictionary/{word}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            for attempt in range(3):
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

        # Function to search meanings for found words (unchanged)
        def search_meanings(words):
            allowed_chars = set('abcdefghijklmnopqrstuvwxyz ')

            filtered_words = []
            for word in words:
                filtered_word = ''.join(char if char in allowed_chars else ' ' for char in word.lower())
                filtered_word = ' '.join(filtered_word.split())
                if filtered_word:
                    filtered_words.extend(filtered_word.split())
            unique_words = list(set(filtered_words))

            if not unique_words:
                print("No valid words to search.")
                return

            results = set()
            not_found_in_bangla = set()

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(search_online, word): word for word in unique_words}
                for future in as_completed(futures):
                    result = future.result()
                    if "not found" not in result and "error" not in result:
                        results.add(result)
                    elif "not found" in result:
                        word = result.split(' ')[0]
                        not_found_in_bangla.add(word)

            for result in results:
                print(result)

            # Print words not found in Bengali meanings
            if not_found_in_bangla:
                for word in not_found_in_bangla:
                    print(f"{word} found in CSV but no Bengali meaning found.")

        # Start the word search (invoke only if found_words is not empty)
        search_meanings(found_words)
