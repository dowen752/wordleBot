import subprocess

process = subprocess.Popen(
    ["java", "Wordle"],
    stdin = subprocess.PIPE,
    stdout = subprocess.PIPE,
    stderr = subprocess.PIPE,
    text = TRUE,
    bufsize = 1
    
)

def get_feedback(output_line):
    return output_line.strip()

with open("code/words.txt") as file:
    wordlist = [word.strip() for word in file]
    
# for guess in wordlist:
#     print