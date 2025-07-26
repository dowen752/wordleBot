import subprocess
import sys
import random as rd
import re

process = subprocess.Popen(
    ["java", "-cp", "code", "Wordle"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

with open("code/words.txt") as file:
    wordlist = [word.strip() for word in file]

possible_words = wordlist.copy()
last_guess = None

def parse_feedback(line, guess):
    # ANSI color codes from Java
    GREEN = "\u001B[42m"
    YELLOW = "\u001B[43m"
    RESET = "\u001B[0m"
    # Regex to extract colored letters
    pattern = re.compile(r'(\x1b\[\d{2}m)?([A-Z])(\x1b\[0m)?')
    feedback = []
    for match in pattern.finditer(line):
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
                if letter in word:
                    match = False
                    break
        if match:
            new_words.append(word)
    return new_words

while True:
    line = process.stdout.readline()
    if not line:
        print("Wordle has completed, exiting.")
        sys.exit()
    print(line, end="")
    if last_guess and any(code in line for code in ["\x1b[42m", "\x1b[43m"]):
        feedback = parse_feedback(line, last_guess)
        possible_words = filter_words(possible_words, last_guess, feedback)
    if "Please guess." in line:
        if possible_words:
            guess = rd.choice(possible_words)
        else:
            guess = rd.choice(wordlist)
        last_guess = guess
        process.stdin.write(guess + "\n")
        process.stdin.flush()