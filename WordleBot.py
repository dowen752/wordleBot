import os, sys, time, random, re, shlex, subprocess, string
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

try:
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    SK_OK = True
except Exception:
    SK_OK = False
    np = None

ALPHABET = string.ascii_lowercase
LETTER_IDX = {ch: i for i, ch in enumerate(ALPHABET)}

def load_words(path: str, length: int = 5) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        words = [w.strip().lower() for w in f if w.strip()]
    return sorted(set(words))

def letter_freq(words: List[str]) -> Dict[str, float]:
    counts = {c: 1.0 for c in ALPHABET}
    for w in words:
        for c in set(w):
            counts[c] += 1.0
    total = sum(counts.values())
    return {c: counts[c]/total for c in ALPHABET}

# Constraints
# -----------


@dataclass
class Constraint:
    greens: Dict[int,str] = field(default_factory=dict)
    yellows: Dict[str,List[int]] = field(default_factory=dict)
    min_counts: Dict[str,int] = field(default_factory=dict)
    max_counts: Dict[str,int] = field(default_factory=dict)

    def allows(self, word:str) -> bool:
        for i,ch in self.greens.items():
            if word[i]!=ch: return False
        for ch,bads in self.yellows.items():
            if ch not in word: return False
            if any(word[i]==ch for i in bads): return False
        for ch,m in self.min_counts.items():
            if word.count(ch)<m: return False
        for ch,mx in self.max_counts.items():
            if word.count(ch)>mx: return False
        return True

def apply_feedback(con: Constraint, guess: str, mask: str) -> Constraint:
    guess = guess.lower()
    mask = mask.upper()
    need_counts = {}
    not_in_positions = {}

    # First pass: count greens/yellows and their positions
    for i, (gch, m) in enumerate(zip(guess, mask)):
        if m == 'G':
            con.greens[i] = gch
            need_counts[gch] = need_counts.get(gch, 0) + 1
        elif m == 'Y':
            not_in_positions.setdefault(gch, []).append(i)
            need_counts[gch] = need_counts.get(gch, 0) + 1

    # Second pass: set max_counts for 'B' letters
    for i, (gch, m) in enumerate(zip(guess, mask)):
        if m == 'B':
            # If the letter is never green/yellow in this guess, it must not appear at all
            if gch not in need_counts:
                con.max_counts[gch] = 0
            else:
                # If the letter is green/yellow elsewhere, max is the number of green/yellow
                con.max_counts[gch] = need_counts[gch]

    # Update yellow positions
    for ch, bads in not_in_positions.items():
        con.yellows.setdefault(ch, [])
        for i in bads:
            if i not in con.yellows[ch]:
                con.yellows[ch].append(i)

    # Update min_counts
    for ch, m in need_counts.items():
        con.min_counts[ch] = max(con.min_counts.get(ch, 0), m)

    return con

# Feedback parsing
# ----------------

ANSI_RE = re.compile(r'\x1b\[(3\d|4\d)m([A-Za-z])\x1b\[0m')
MASK_RE = re.compile(r'([GYB]{5})')

def parse_feedback_line(line: str) -> Optional[str]:
    # Try to match a mask first
    m = MASK_RE.search(line)
    if m:
        s = m.group(1).upper()
        if len(s) == 5: return s

    # Now handle a line with a mix of colored and uncolored letters
    # This will parse the feedback line from Java
    # Example: '\x1b[42mA\x1b[0m\x1b[43mE\x1b[0mR\x1b[43mO\x1b[0mS'
    mask = []
    i = 0
    while i < len(line):
        if line[i:i+2] == '\x1b[':
            # It's a color code
            end = line.find('m', i)
            color_code = line[i+2:end]
            letter = line[end+1]
            if color_code in ('32', '42'):
                mask.append('G')
            elif color_code in ('33', '43'):
                mask.append('Y')
            else:
                mask.append('B')
            i = end + 2  # Skip past 'm' and the letter
            # Skip the reset code if present
            if line[i:i+4] == '\x1b[0m':
                i += 4
        elif line[i].isalpha():
            # Uncolored letter = gray
            mask.append('B')
            i += 1
        else:
            i += 1
        if len(mask) == 5:
            return ''.join(mask)
    return None

def featurize(words:List[str])->"np.ndarray":
    n=len(words); X=np.zeros((n,5*26+26),dtype=np.float32)
    for r,w in enumerate(words):
        for i,ch in enumerate(w):
            X[r,i*26+LETTER_IDX[ch]]=1.0
        for ch in w:
            X[r,5*26+LETTER_IDX[ch]]+=1.0
        X[r,5*26:]=np.minimum(X[r,5*26:],2.0)
    return X

# Scoring
# -------

def score_words_sklearn(cands:List[str], allw:List[str]):
    neg=[w for w in allw if w not in cands]
    n_pos=len(cands)
    n_neg=min(len(neg), max(200, n_pos*3))
    if n_pos == 0 or n_neg == 0:
        # Not enough classes for logistic regression, fallback to frequency
        return score_words_freq(cands, allw)
    sample=random.sample(neg, n_neg) if n_neg>0 else []
    train=cands+sample; y=[1]*len(cands)+[0]*len(sample)
    X=featurize(train)
    clf=LogisticRegression(max_iter=200,solver='saga')
    clf.fit(X,y)
    probs=clf.predict_proba(featurize(allw))[:,1]
    return list(zip(allw,probs))

def score_words_freq(cands:List[str], allw:List[str]):
    f=letter_freq(cands if cands else allw); scores=[]
    for w in allw:
        score=sum(f.get(ch,0) for ch in set(w))
        if w in cands: score*=1.1
        scores.append((w,score))
    return scores

def pick_guess(scored,used:set)->str:
    for w,_ in sorted(scored,key=lambda t:t[1],reverse=True):
        if w not in used: return w
    return scored[0][0]

def pick_probe_word(cands: List[str], all_words: List[str], used: set) -> Optional[str]:
    # Find all letters in positions that differ among candidates
    differing_positions = []
    for i in range(5):
        letters = set(w[i] for w in cands)
        if len(letters) > 1:
            differing_positions.append((i, letters))
    # Flatten all differing letters
    probe_letters = set()
    for i, letters in differing_positions:
        probe_letters.update(letters)
    # Score all words by how many probe_letters they cover (even if already ruled out)
    best_word = None
    best_score = -1
    for w in all_words:
        score = len(set(w) & probe_letters)
        if score > best_score and w not in used:
            best_score = score
            best_word = w
    return best_word

#  Game loop 
# ----------

def run_game(max_turns=6)->bool:
    base=os.path.dirname(__file__)
    code_dir=os.path.join(base,"code")
    words_path=os.path.join(code_dir,"words.txt")
    all_words=load_words(words_path)
    cands=all_words.copy(); used=set(); con=Constraint()

    proc=subprocess.Popen(
        ["java","-cp","code","Wordle"],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,bufsize=1,cwd=base
    )
    assert proc.stdin and proc.stdout

    won=False
    for turn in range(1, max_turns + 1):
        # Wait for the "Please guess" prompt before making a guess
        prompt_seen = False
        lines = []
        end = time.time() + 30  # up to 30 seconds to see the prompt
        while time.time() < end:
            line = proc.stdout.readline()
            if not line:
                break
            lines.append(line)
            print(f"[Game] {line.strip()}")
            if "Please guess" in line:
                prompt_seen = True
                break
        if not prompt_seen:
            print("[Solver] Did not see 'Please guess' prompt, exiting.")
            break

        # Guessing
        remaining_guesses = max_turns - turn + 1
        if len(cands) > remaining_guesses and remaining_guesses > 1:
            # Probe for information
            guess = pick_probe_word(cands, all_words, used)
            print(f"[Turn {turn}] Probe guess -> {guess.upper()}")
        else:
            # Standard guess
            scored = score_words_sklearn(cands, all_words) if SK_OK else score_words_freq(cands, all_words)
            guess = pick_guess(scored, used)
        
        used.add(guess)
        print(f"[Turn {turn}] Guess -> {guess.upper()}")
        proc.stdin.write(guess + "\n")
        proc.stdin.flush()

        # Now read feedback as before
        mask = None
        lines = []
        end = time.time() + 10  # up to 10 seconds per turn
        while time.time() < end:
            line = proc.stdout.readline()
            if not line:
                break
            lines.append(line)
            print(f"[Game] {line.strip()}")
            parsed = parse_feedback_line(line)
            if parsed:
                mask = parsed
                break
        if not mask:
            for line in lines:
                parsed = parse_feedback_line(line)
                if parsed:
                    mask = parsed
                    break
        if not mask:
            print("[Solver] Could not parse feedback")
            break
        print(f"[Turn {turn}] Feedback mask: {mask}")
        if mask == "GGGGG":
            won = True
            print(f"[Solver] Solved in {turn} turns with {guess.upper()}")
            break
        con = apply_feedback(con, guess, mask)
        cands = [w for w in cands if con.allows(w)]
        print(f"[Solver] Candidates remaining: {len(cands)}")
        if not cands:
            cands = all_words.copy()
    # Wait for the Java process to finish and print the answer
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            print(f"[Game] {line.strip()}")
        print(f"Remaining candidates: {cands}")
    except Exception:
        pass
    proc.terminate()
    return won

if __name__=="__main__":
    ok=run_game(); sys.exit(0 if ok else 1)
