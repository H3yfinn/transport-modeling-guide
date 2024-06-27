from encryption import generate_key, load_key, encrypt_password, decrypt_password

# Generate a new key (only do this once)
# generate_key()

# Load the key (verify it's the same key)
key = load_key()
print("Loaded key:", key)

# Encrypt a password
password = "GqJ0kLGjbP1S"
encrypted_password = encrypt_password(password)
print("Encrypted password:", encrypted_password)

# Decrypt the password
decrypted_password = decrypt_password(encrypted_password)
print("Decrypted password:", decrypted_password)

# Verify the decrypted password matches the original
assert decrypted_password == password
