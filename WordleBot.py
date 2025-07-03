import subprocess
import sys

process = subprocess.Popen(
    ["java", "-cp", "code", "Wordle"],
    stdin = subprocess.PIPE,
    stdout = subprocess.PIPE,
    stderr = subprocess.PIPE,
    text = True,
    bufsize = 1
    
)

def get_feedback(output_line):
    return output_line.strip()

# with open("code/words.txt") as file:
#     wordlist = [word.strip() for word in file]
    
# for guess in wordlist:
#     print

# Deal with above later, first establish communication btwn files

while True:
    line = process.stdout.readline()
    if not line:
        print("Wordle has completed, exiting.")
        sys.exit()
    print(line)
    if "Please guess." in line:
        guess = "crane"
        process.stdin.write(guess + "\n")
        process.stdin.flush()
    
