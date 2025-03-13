def build_bracket(n):
    """
    Recursively builds the bracket ordering for n players (n is power of 2).
    For n == 2, returns [1, 2].
    For larger n, it returns the ordering that ensures top seeds meet last.
    """
    if n == 2:
        return [1, 2]
    previous = build_bracket(n // 2)
    print("Previous: ",previous)
    bracket = []
    for seed in previous:
        print(f"Appending {seed} and {n + 1 - seed}")
        bracket.append(seed)
        bracket.append(n + 1 - seed)
    
    print("Bracket: ",bracket)
    return bracket

def generate_seeded_matches(num_players):
    """
    Returns the first round match pairings for a tournament with num_players,
    ensuring that the best seeds meet only in later rounds.
    """
    # Ensure num_players is a power of 2
    if num_players & (num_players - 1) != 0:
        raise ValueError("Number of players must be a power of 2 (e.g., 8, 16, 32).")
    
    # Obtain the bracket ordering. For example, for 16 players the order might be:
    # [1, 16, 9, 8, 5, 12, 13, 4, 3, 14, 11, 6, 7, 10, 15, 2]
    bracket_order = build_bracket(num_players)
    
    # Pair off seeds for the first round
    matches = [(bracket_order[i], bracket_order[i+1]) for i in range(0, num_players, 2)]
    return matches

# Example use:
if __name__ == "__main__":
    num_players = 16  # Change to 8, 16, 32, ... as needed
    matches = generate_seeded_matches(num_players)
    for match_num, (seed1, seed2) in enumerate(matches, start=1):
        print(f"Match {match_num}: Seed {seed1} vs Seed {seed2}")