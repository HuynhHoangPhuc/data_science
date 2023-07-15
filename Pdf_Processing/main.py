import re
import PyPDF2
import concurrent.futures
import pandas as pd


def process_page(page_num, page_text, word):
    """
    Extracts sentences from a page of a PDF file containing a specified word.

    Args:
    - page_num: int, the page number
    - page_text: str, the text of the page
    - word: str, the word to search for

    Returns:
    - results: list, a list of tuples containing the sentence and the page number
    """
    # Set the correct encoding for Vietnamese text
    page_text = page_text.encode('utf-8').decode('utf-8')

    # Split the text into sentences using regular expressions
    page_sentences = re.split(r'[.!?]', page_text)

    # Initialize an empty list to store the results
    results = []

    # Iterate over each sentence and check if it contains the specified word
    for sentence in page_sentences:
        if word in sentence:
            sentence = sentence.replace('”', '') \
                .replace('“', '') \
                .replace('\n', ' ') \
                .replace('\x03', ' ') \
                .replace('[0-9]', '')
            sentence = re.sub(' +', ' ', sentence)
            results.append((sentence.strip(), page_num + 1))

    return results


def find_sentences_with_word(pdf_file_path, word, num_threads=None):
    """
    Extracts text from each page of a PDF file and returns a pandas DataFrame
    containing all sentences containing a specific word along with their page numbers.

    Args:
    - pdf_file_path: str, the path to the PDF file
    - word: str, the word to search for
    - num_threads: int, the number of threads to use for processing pages

    Returns:
    - df: pandas DataFrame, a DataFrame of all sentences containing the specified word
      along with their page numbers
    """
    # Open the PDF file in binary mode
    with open(pdf_file_path, 'rb') as file:
        # Create a PDF reader object
        reader = PyPDF2.PdfReader(file)

        # Initialize an empty list to store the results
        results = []

        # Create a ThreadPoolExecutor with the specified number of threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Iterate over each page in the PDF file
            for page_num in range(len(reader.pages)):
                # Get the text of the current page
                page_text = reader.pages[page_num].extract_text()

                # Submit a new task to the executor to process the page
                future = executor.submit(process_page, page_num, page_text, word)

                # Add the future to a list
                results.append(future)

            # Initialize an empty list to store the final results
            final_results = []

            # Iterate over the futures and get the results
            for future in concurrent.futures.as_completed(results):
                final_results.extend(future.result())

        # Create a pandas DataFrame from the final results
        df = pd.DataFrame(final_results, columns=['sentence', 'page'])

        return df


def write_results_to_excel(output_file_path, data):
    pd.ExcelWriter(output_file_path, engine='openpyxl')
    data.to_excel(output_file_path, index=False)


if __name__ == '__main__':
    # Find all sentences containing the word 'mèo' in the PDF file
    cat = find_sentences_with_word('file.pdf', 'mèo')
    beghemot = find_sentences_with_word('file.pdf', 'Beghemot')

    # Sort the results by page number
    cat = cat.sort_values(by='page').reset_index(drop=True)
    beghemot = beghemot.sort_values(by='page').reset_index(drop=True)

    # Write the results to an Excel file
    write_results_to_excel('cat.xlsx', cat)
    write_results_to_excel('beghemot.xlsx', beghemot)
