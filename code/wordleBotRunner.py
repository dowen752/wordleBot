import subprocess


# runs WordleBot.py many times to test the bot's performance
# prints the number of wins, losses, and success rate
NUM_RUNS = 200
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
    else:
        losses += 1
    print(f"Game {i+1}: {'Win' if 'YOU WIN TWIN!!!!' in output else 'Loss'}")

print(f"\nTotal games: {NUM_RUNS}")
print(f"Wins: {wins}")
print(f"Losses: {losses}")
print(f"Success rate: {wins / NUM_RUNS * 100:.2f}%")