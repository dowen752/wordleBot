import subprocess
import sys
import random as rd
import re

# subprocess start
process = subprocess.Popen(
    ["java", "-cp", "code", "Wordle"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # line-buffered
)

# Load words
with open("code/words.txt") as file:
    wordlist = [word.strip() for word in file]

possible_words = wordlist.copy()
last_guess = None
used_letters = set()

COLOR_PATTERN = re.compile(r'(\x1b\[\d{2}m)?([A-Z])(\x1b\[0m)?')

def parse_feedback(line, guess):
    feedback = []
    for match in COLOR_PATTERN.finditer(line):
        color = match.group(1)
        letter = match.group(2)
        if color == '\x1b[42m':
            feedback.append(('green', letter))
        elif color == '\x1b[43m':
            feedback.append(('yellow', letter))
        else:
            feedback.append(('gray', letter))
    return feedback

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
                # Handle gray letters carefully (account for duplicates)
                if letter in guess:
                    allowed = sum(1 for j, (c, l) in enumerate(feedback)
                                  if l == letter and c in ('green', 'yellow'))
                    if word.count(letter) > allowed:
                        match = False
                        break
                else:
                    if letter in word:
                        match = False
                        break
        if match:
            new_words.append(word)
    return new_words

def compute_letter_counts(possible_words):
    counts = {}
    for w in possible_words:
        for c in set(w):  # Only count each letter once per word
            counts[c] = counts.get(c, 0) + 1
    return counts

def score_word(word, counts):
    return sum(counts.get(c, 0) for c in set(word))

def choose_best_guess(possible_words, wordlist, first=False):
    if not possible_words:
        return rd.choice(wordlist)
    counts = compute_letter_counts(possible_words)
    candidates = wordlist if first else possible_words
    scored = [(score_word(word, counts), word) for word in candidates]
    scored.sort(reverse=True)
    return scored[0][1]

def get_probe_word(possible_words, wordlist, used_letters):
    # Find the set of all letters in possible_words not yet guessed
    remaining_letters = set("".join(possible_words)) - used_letters
    best_word = None
    best_score = -1
    for word in wordlist:
        score = len(set(word) & remaining_letters)
        if score > best_score:
            best_score = score
            best_word = word
    return best_word

def positions_with_variation(possible_words):
    # returns a list of positions (0-4) where possible_words differ
    return [i for i in range(5) if len(set(word[i] for word in possible_words)) > 1]

# Main game loop
while True:
    line = process.stdout.readline()
    if not line:
        print("Wordle has completed, exiting.")
        sys.exit()

    print(line, end="")
    sys.stdout.flush()

    # Parse feedback when colors appear
    if last_guess and any(code in line for code in ["\x1b[42m", "\x1b[43m"]):
        feedback = parse_feedback(line, last_guess)
        possible_words = filter_words(possible_words, last_guess, feedback)

    # responding when prompted
    if "Please guess." in line:
        if last_guess is None:
            # First guess: maximize information
            guess = choose_best_guess(possible_words, wordlist, first=True)
        elif len(possible_words) == 1:
            guess = possible_words[0]
        else:
            pos_var = positions_with_variation(possible_words)
            # If only 1 or 2 positions vary and more than 2 possible words, probe
            if len(pos_var) <= 2 and len(possible_words) > 2:
                guess = get_probe_word(possible_words, wordlist, used_letters)
                # Avoid repeating a probe word or using a possible answer as probe
                if guess in used_letters or guess in possible_words:
                    guess = choose_best_guess(possible_words, wordlist)
            else:
                guess = choose_best_guess(possible_words, wordlist)
        last_guess = guess
        used_letters.update(set(guess))
        process.stdin.write(guess + "\n")
        process.stdin.flush()