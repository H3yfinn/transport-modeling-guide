from encryption import load_encryption_key, encrypt_data, decrypt_data

# Generate a new key (only do this once)
# generate_key()

# Load the key (verify it's the same key)
key = load_encryption_key()
print("Loaded key:", key)

# Encrypt a password
password = "GqJ0kLGjbP1S"
encrypted_password = encrypt_data(password)
print("Encrypted password:", encrypted_password)

# Decrypt the password
decrypted_password = decrypt_data(encrypted_password)
print("Decrypted password:", decrypted_password)

# Verify the decrypted password matches the original
assert decrypted_password == password
