import subprocess
import sys
import os
import re
import math
from collections import Counter, defaultdict

# --- Start the Java Wordle process ---
process = subprocess.Popen(
    ["java", "-cp", "code", "Wordle"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    cwd=os.path.dirname(__file__)
)

# --- Load words ---
words_path = os.path.join(os.path.dirname(__file__), "code", "words.txt")
with open(words_path) as file:
    wordlist = [word.strip().upper() for word in file]

possible_words = wordlist.copy()
last_guess = None
used_letters = set()

COLOR_PATTERN = re.compile(r'(\x1b\[\d{2}m)?([A-Z])(\x1b\[0m)?')

def parse_feedback(line):
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

def feedback_pattern(guess: str, answer: str) -> str:
    res = ['B'] * 5
    a_counts = Counter(answer)
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            res[i] = 'G'
            a_counts[g] -= 1
    for i, g in enumerate(guess):
        if res[i] == 'G':
            continue
        if a_counts[g] > 0:
            res[i] = 'Y'
            a_counts[g] -= 1
    return ''.join(res)

def filter_words(possible_words, guess, feedback):
    # Build sets for green, yellow, and gray letters
    green_positions = {}
    yellow_letters = set()
    gray_letters = set()
    for i, (color, letter) in enumerate(feedback):
        if color == 'green':
            green_positions[i] = letter
        elif color == 'yellow':
            yellow_letters.add(letter)
        elif color == 'gray':
            gray_letters.add(letter)

    # Only keep gray letters that are not also green/yellow elsewhere
    confirmed_letters = set(green_positions.values()) | yellow_letters
    truly_gray = gray_letters - confirmed_letters

    new_words = []
    for word in possible_words:
        match = True
        # Green check
        for i, letter in green_positions.items():
            if word[i] != letter:
                match = False
                break
        # Yellow check
        for i, (color, letter) in enumerate(feedback):
            if color == 'yellow':
                if letter not in word or word[i] == letter:
                    match = False
                    break
        # Gray check
        for letter in truly_gray:
            if letter in word:
                match = False
                break
        if match:
            new_words.append(word)
    return new_words

def guess_entropy(guess, candidates):
    bucket = defaultdict(int)
    n = len(candidates)
    for ans in candidates:
        pat = feedback_pattern(guess, ans)
        bucket[pat] += 1
    H = 0.0
    for cnt in bucket.values():
        p = cnt / n
        H -= p * math.log2(p)
    return H

def choose_by_entropy(candidates, wordlist, allow_probe=True):
    search_space = wordlist if allow_probe else candidates
    best_guess, best_H = None, -1.0
    for g in search_space:
        H = guess_entropy(g, candidates)
        if H > best_H or (H == best_H and g in candidates):
            best_H, best_guess = H, g
    return best_guess

def choose_best_guess(possible_words, wordlist, first=False):
    if first:
        return "SALET"
    n = len(possible_words)
    if n <= 2:
        return possible_words[0]
    if n <= 100:
        return choose_by_entropy(possible_words, wordlist, allow_probe=False)
    return choose_by_entropy(possible_words, wordlist, allow_probe=True)

while True:
    line = process.stdout.readline()
    if not line:
        print("Wordle has completed, exiting.")
        err = process.stderr.read()
        if err:
            print("Java error output:")
            print(err)
        sys.exit()

    print(line, end="")
    sys.stdout.flush()

    # Parse feedback when colors appear
    if last_guess and any(code in line for code in ["\x1b[42m", "\x1b[43m"]):
        feedback = parse_feedback(line)
        possible_words = filter_words(possible_words, last_guess, feedback)

    # Respond with a guess when prompted
    if "Please guess." in line:
        if last_guess is None:
            guess = choose_best_guess(possible_words, wordlist, first=True)
        elif len(possible_words) == 1:
            guess = possible_words[0]
        else:
            guess = choose_best_guess(possible_words, wordlist)
        last_guess = guess
        used_letters.update(set(guess))
        process.stdin.write(guess + "\n")
        process.stdin.flush()