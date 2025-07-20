from dotenv import load_dotenv
import os

load_dotenv()

def main():
	print("Hello, World!")
	print(os.getenv("OPENAI_API_KEY"))

if __name__ == "__main__":
	main()
