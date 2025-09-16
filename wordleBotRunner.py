import subprocess
import re

NUM_RUNS = 100
wins = 0
losses = 0

for i in range(NUM_RUNS):
    process = subprocess.Popen(
        ["python", "WordleBot.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output, _ = process.communicate()
    
    if "YOU WIN TWIN!!!!" in output:
        wins += 1
        match = re.search(r"Solved in 5 turns with (\w+)", output)
        answer = match.group(1) if match else "N/A"
        print(f"Game {i+1}: Win (Answer: {answer})")
    else:
        losses += 1
        match = re.search(r"The correct answer was: (\w+)", output)
        answer = match.group(1) if match else "N/A"
        print(f"Game {i+1}: Loss (Answer: {answer})")

print(f"\nTotal games: {NUM_RUNS}")
print(f"Wins: {wins}")
print(f"Losses: {losses}")
print(f"Success rate: {wins / NUM_RUNS * 100:.2f}%")