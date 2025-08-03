from elusion_jokes.src.elusion.jokes import JokesSDK

def main():
    sdk = JokesSDK()
    
    random_joke = sdk.jokes.get_random_joke()
    
    print(f"Random joke: {random_joke}")
    
if __name__ == "__main__":
    main()