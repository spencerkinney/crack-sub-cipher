# cipher_utils.py
import string
import random
from collections import Counter
from nltk.corpus import words
from nltk.tokenize import word_tokenize
import nltk

# Download necessary NLTK resources
nltk.download('words', quiet=True)
nltk.download('punkt', quiet=True)

# Load English words
ENGLISH_WORDS = set(words.words())

# Complete bigram frequencies from the English language
# https://pi.math.cornell.edu/~mec/2003-2004/cryptography/subs/digraphs.html
ENGLISH_BIGRAMS = {
    'TH': 1.52, 'HE': 1.28, 'IN': 0.94, 'ER': 0.94, 'AN': 0.82, 'RE': 0.68, 'ND': 0.63, 'AT': 0.59, 'ON': 0.57,
    'NT': 0.56, 'HA': 0.56, 'ES': 0.56, 'ST': 0.55, 'EN': 0.55, 'ED': 0.53, 'TO': 0.52, 'IT': 0.50, 'OU': 0.50,
    'EA': 0.47, 'HI': 0.46, 'IS': 0.46, 'OR': 0.43, 'TI': 0.34, 'AS': 0.33, 'TE': 0.27, 'ET': 0.19, 'NG': 0.18,
    'OF': 0.16, 'AL': 0.09, 'DE': 0.09, 'SE': 0.08, 'LE': 0.08, 'SA': 0.06, 'SI': 0.05, 'AR': 0.05, 'VE': 0.04,
    'RA': 0.04, 'LD': 0.02, 'UR': 0.02, 'NO': 0.01
}

class CipherUtils:
    def __init__(self, ciphertext):
        self.ciphertext = ciphertext
        self.alphabet = list(string.ascii_uppercase)
    
    def frequency_analysis(self):
        """Frequency analysis of ciphertext."""
        filtered_text = ''.join(filter(str.isalpha, self.ciphertext))  # Only alphabetic characters
        return Counter(filtered_text)
    
    def generate_random_key(self):
        """Generate a random substitution key."""
        shuffled = self.alphabet[:]
        random.shuffle(shuffled)
        return dict(zip(self.alphabet, shuffled))
    
    def decrypt_with_key(self, key_mapping):
        """Decrypt ciphertext using the substitution key."""
        decrypted_message = []
        for char in self.ciphertext:
            if char in string.ascii_uppercase:
                decrypted_message.append(key_mapping.get(char, char))
            else:
                decrypted_message.append(char)  # Keep non-alphabetic characters unchanged
        return ''.join(decrypted_message)

    def ngram_score(self, text):
        """Calculate bigram score based on English frequencies."""
        score = 0
        bigrams = [text[i:i+2] for i in range(len(text) - 1) if text[i:i+2].isalpha()]
        for bigram in bigrams:
            score += ENGLISH_BIGRAMS.get(bigram.upper(), 0)
        return score

    def valid_word_percentage(self, decoded_message):
        """Calculate percentage of valid English words in the decoded message."""
        words_in_message = word_tokenize(decoded_message)
        valid_words = [word for word in words_in_message if word.lower() in ENGLISH_WORDS]
        if len(words_in_message) == 0:
            return 0
        return (len(valid_words) / len(words_in_message)) * 100

    def hill_climbing_with_restarts(self, max_iterations=5000, restarts=10, callback=None):
        """Hill Climbing algorithm with restarts."""
        best_key = self.generate_random_key()
        best_score = -float('inf')
        best_decrypted = ""

        for restart in range(restarts):
            current_key = self.generate_random_key()
            current_score = self.ngram_score(self.decrypt_with_key(current_key)) + \
                            self.valid_word_percentage(self.decrypt_with_key(current_key))
            
            for i in range(max_iterations):
                new_key = current_key.copy()
                letter1, letter2 = random.sample(self.alphabet, 2)
                new_key[letter1], new_key[letter2] = new_key[letter2], new_key[letter1]
                
                decrypted_message = self.decrypt_with_key(new_key)
                new_score = self.ngram_score(decrypted_message) + self.valid_word_percentage(decrypted_message)
                
                if new_score > current_score:
                    current_key = new_key
                    current_score = new_score
                    
                    if current_score > best_score:
                        best_key = current_key
                        best_score = current_score
                        best_decrypted = decrypted_message
                        if callback:
                            callback(restart * max_iterations + i, best_score, best_decrypted)
        
        return best_decrypted, best_key

    def decrypt(self, max_iterations=10000, restarts=10, callback=None):
        """Decrypt the ciphertext using Hill Climbing with Restarts."""
        return self.hill_climbing_with_restarts(max_iterations, restarts, callback)