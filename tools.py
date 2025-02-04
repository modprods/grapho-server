import hashlib

def generate_grapho_id(input_string):
    """
    Generate a stable integer hash based on the input string using SHA-256.
    There may be a good argument to keep using integer ids once Neo4j deprecates them 
    so prepping 
    
    Parameters:
    input_string (str): The string to hash.
    
    Returns:
    int: The stable integer hash of the input string.
    """
    # Create a SHA-256 hash object
    sha256 = hashlib.sha256()
    
    # Update the hash object with the bytes of the input string
    sha256.update(input_string.encode('utf-8'))
    
    # Get the hexadecimal digest of the hash
    hex_digest = sha256.hexdigest()
    
    # Convert the hexadecimal digest to an integer
    return int(hex_digest, 16)

# Example usage:
input_str = "5:b1b34cd3-b9a1-456e-89ed-4359603f8be7:197"
hash_value = generate_grapho_id(input_str)
print(hash_value)
