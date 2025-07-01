import os
import google.generativeai as genai
import time
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') 

genai.configure(api_key=GEMINI_API_KEY)

BOOK_FILE_PATH = "test.txt" 

SENDER_EMAIL = os.getenv('SENDER_EMAIL') 
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECIPIENT_EMAIL = "find.nishita@outlook.com" 

def send_email(subject, body, to_email):
    """Sends an email using SMTP."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Email sender credentials not set. Skipping email.")
        print("Please set SENDER_EMAIL and SENDER_PASSWORD in your .env file or script.")
        return

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # For Gmail, use smtp.gmail.com and port 587
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: # Use 465 for SSL or 587 for TLS
            # smtp.starttls() # Only if using port 587
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"Newsletter email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        print("Possible issues: Incorrect email/password, App Password needed for Gmail 2FA, less secure apps access for older accounts.")
        print("For Gmail with 2FA, generate an App Password: https://support.google.com/accounts/answer/185833")


def read_book_text(file_path):
    """Reads a plain text file and returns its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Book file not found at {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred while reading the book: {e}")
        return None


def call_gemini_api(prompt_text):
    """Helper function to call the Gemini API."""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt_text)
        return response.text # Gemini API often returns response.text directly
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def summarize_text_hierarchically(text, chunk_size=8000, final_summary_words=500):
    """
    Summarizes long text by breaking it into chunks, summarizing chunks,
    and then summarizing those summaries.
    """
    print("Starting hierarchical summarization...")
    summaries = []
    text_chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    for i, chunk in enumerate(text_chunks):
        print(f"Summarizing chunk {i+1}/{len(text_chunks)}...")
        prompt = f"Summarize the following text in 150 words or less, focusing on key information and removing redundancies:\n\n{chunk}"
        chunk_summary = call_gemini_api(prompt)
        if chunk_summary:
            summaries.append(chunk_summary)
            time.sleep(1) # Small delay to respect rate limits
        else:
            print(f"Warning: Could not get summary for chunk {i+1}.")

    if not summaries:
        return "Could not generate any summaries from chunks."

    combined_summaries = "\n\n".join(summaries)
    print(f"Combined {len(summaries)} chunk summaries. Total length: {len(combined_summaries)} characters.")

    final_summary_prompt = f"""Combine and refine the following summaries into a comprehensive book summary of about {final_summary_words} words. Make it engaging and highlight the main plot, characters, and themes:

    {combined_summaries}"""

    final_book_summary = call_gemini_api(final_summary_prompt)
    return final_book_summary if final_book_summary else "Could not generate final book summary."

def generate_newsletter(book_summary, book_title="The Book"):
    """Generates newsletter content based on a book summary."""
    print("Generating newsletter content...")
    newsletter_prompt = f"""Using the following book summary, create a compelling newsletter for a general audience.
    The newsletter should be about the book "{book_title}".
    It should be structured with:
    1. A catchy title for the newsletter.
    2. A brief, engaging introduction.
    3. 3-4 bullet points highlighting key insights or interesting aspects of the book.
    4. A concluding paragraph encouraging readers to explore the book.
    Maintain an enthusiastic and informative tone.

    Book Summary:
    {book_summary}"""

    newsletter_content = call_gemini_api(newsletter_prompt)
    return newsletter_content if newsletter_content else "Could not generate newsletter content."


def main():
    print(f"Starting book processing for: {BOOK_FILE_PATH}")
    book_content = read_book_text(BOOK_FILE_PATH)

    if book_content:
        print(f"Successfully read book. Total characters: {len(book_content)}")
        #print("First 500 characters:\n", book_content[:500])
        final_book_summary = summarize_text_hierarchically(book_content)
        print("\n--- Final Book Summary ---")
        print(final_book_summary)
        print("-------------------------\n")

        book_title_for_newsletter = "Test Summary" # <<< REPLACE OR MAKE DYNAMIC
        newsletter_text = generate_newsletter(final_book_summary, book_title_for_newsletter)
        print("\n--- Generated Newsletter ---")
        print(newsletter_text)
        print("----------------------------\n")
        email_subject = f"Your Book Newsletter: {book_title_for_newsletter}"
        send_email(email_subject, newsletter_text, RECIPIENT_EMAIL)

    else:
        print("Could not read book content. Exiting.")
        return # Exit if no content


if __name__ == "__main__":
    main()