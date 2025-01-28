import secrets
import hashlib
import time
import base64

def generate_proof(number, timestamp, nonce):
    """Generate a cryptographic proof for a random number."""
    proof_string = f"{number}:{timestamp}:{nonce}"
    proof_hash = hashlib.sha256(proof_string.encode()).hexdigest()
    return {
        'number': number,
        'timestamp': timestamp,
        'nonce': nonce,
        'hash': proof_hash
    }

def generate_random_numbers(max_range=1, count=1):
    """
    Generate random numbers within the range of 1 to max_range.

    Args:
        max_range (int): The maximum number in the range (inclusive)
        count (int): Number of random numbers to generate

    Returns:
        tuple: (list of numbers, list of proofs)
    """
    start = 1
    timestamp = int(time.time())

    # Ensure max_range and count are valid
    max_range = max(1, int(max_range))
    count = max(1, min(100, int(count)))  # Limit number of rolls between 1 and 100
    
    numbers = []
    proofs = []
    
    for _ in range(count):
        # Generate random number
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('utf-8')
        number = secrets.randbelow(max_range - start + 1) + start
        
        # Generate proof
        proof = generate_proof(number, timestamp, nonce)
        
        numbers.append(number)
        proofs.append(proof)
    
    return numbers, proofs

def verify_proof(proof):
    """Verify a cryptographic proof."""
    proof_string = f"{proof['number']}:{proof['timestamp']}:{proof['nonce']}"
    verification_hash = hashlib.sha256(proof_string.encode()).hexdigest()
    return verification_hash == proof['hash']

if __name__ == "__main__":
    try:
        numbers, proofs = generate_random_numbers()
        print(f"Generated random numbers: {numbers}")
        print(f"Proofs: {proofs}")
        # Verify proofs
        for proof in proofs:
            is_valid = verify_proof(proof)
            print(f"Proof verification for {proof['number']}: {is_valid}")
    except ValueError as e:
        print(f"Error: {e}") 