from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- WordleBot logic ---
with open("code/words.txt") as file:
    wordlist = [word.strip().upper() for word in file]

possible_words = wordlist.copy()

def compute_letter_counts(words):
    counts = {}
    for w in words:
        for c in set(w):
            counts[c] = counts.get(c, 0) + 1
    return counts

def score_word(word, counts):
    # Score by sum of unique letter frequencies
    return sum(counts.get(c, 0) for c in set(word))

def choose_best_guess(possible_words, wordlist, first=False):
    counts = compute_letter_counts(possible_words)
    candidates = wordlist if first else possible_words
    scored = [(score_word(word, counts), word) for word in candidates]
    scored.sort(reverse=True)
    return scored[0][1]

def get_probe_word(possible_words, wordlist, used_letters):
    # Find the set of all letters in possible_words not yet guessed
    remaining_letters = set("".join(possible_words)) - used_letters
    # Find a word in the wordlist that uses as many of these as possible
    best_word = None
    best_score = -1
    for word in wordlist:
        score = len(set(word) & remaining_letters)
        if score > best_score:
            best_score = score
            best_word = word
    return best_word

def filter_words(possible_words, guess, feedback):
    new_words = []
    for word in possible_words:
        match = True
        for i, (color, letter) in enumerate(feedback):
            if color == 'green':
                if word[i] != letter:
                    match = False
                    break
            elif color == 'yellow':
                if letter not in word or word[i] == letter:
                    match = False
                    break
            elif color == 'gray':
                allowed = sum(1 for j, (c, l) in enumerate(feedback)
                              if l == letter and c in ('green', 'yellow'))
                if word.count(letter) > allowed:
                    match = False
                    break
        if match:
            new_words.append(word)
    return new_words

def get_feedback_from_board(driver, row_idx):
    # Each tile in the row has data-state: 'correct', 'present', or 'absent'
    row = driver.find_elements(By.CSS_SELECTOR, f'div[aria-label="Row {row_idx+1}"] div[data-testid="tile"]')
    feedback = []
    for tile in row:
        letter = tile.text.upper()
        color = tile.get_attribute("data-state")
        if color == "correct":
            feedback.append(('green', letter))
        elif color == "present":
            feedback.append(('yellow', letter))
        else:
            feedback.append(('gray', letter))
    return feedback

# --- Selenium setup ---
driver = webdriver.Chrome()
driver.get("https://www.nytimes.com/games/wordle/index.html")
wait = WebDriverWait(driver, 15)

# 1. Click "Play" button if present
try:
    play_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Play') or contains(., 'No Thanks')]"))
    )
    play_button.click()
    time.sleep(1)
except Exception:
    pass

# 2. Close the tutorial overlay if present
try:
    help_dialog = wait.until(
        EC.presence_of_element_located((By.ID, "help-dialog"))
    )
    close_button = help_dialog.find_element(By.CLASS_NAME, "Modal-module_closeIcon__TcEKb")
    close_button.click()
    time.sleep(1)
except Exception:
    pass

actions = driver.find_element(By.TAG_NAME, "body")
last_guess = None
used_letters = set()

for row_idx in range(6):
    # Decide strategy
    if row_idx == 0:
        guess = choose_best_guess(possible_words, wordlist, first=True)
    elif len(possible_words) == 1:
        guess = possible_words[0]
    else:
        # Check for "trap" situation: all possible words differ by only 1 or 2 letters
        # Find positions with more than one unique letter
        positions_with_variation = [i for i in range(5) if len(set(word[i] for word in possible_words)) > 1]
        # If only 1 or 2 positions vary, and there are more than 2 possible words, probe!
        if len(positions_with_variation) <= 2 and len(possible_words) > 2:
            guess = get_probe_word(possible_words, wordlist, used_letters)
            # Avoid repeating a probe word
            if guess in used_letters or guess in possible_words:
                guess = choose_best_guess(possible_words, wordlist)
        else:
            guess = choose_best_guess(possible_words, wordlist)
    last_guess = guess
    used_letters.update(set(guess))
    actions.send_keys(guess)
    actions.send_keys(Keys.RETURN)
    time.sleep(2.5)  # Wait for animation

    feedback = get_feedback_from_board(driver, row_idx)
    print(f"Guess {row_idx+1}: {guess} -> {feedback}")

    if all(color == 'green' for color, _ in feedback):
        print("Solved!")
        break

    possible_words = filter_words(possible_words, guess, feedback)

time.sleep(5)
driver.quit()