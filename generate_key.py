from cryptography.fernet import Fernet

def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)
    print("Key generated and saved to secret.key, make sure to save it to .env file to use it in the application.")

if __name__ == "__main__":
    generate_key()