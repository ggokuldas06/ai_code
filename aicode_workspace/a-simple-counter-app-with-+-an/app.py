import sys

class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

    def get_count(self):
        return self.count


def main():
    counter = Counter()
    print("Counter App")
    print("Commands:")
    print("  inc   - Increment")
    print("  dec   - Decrement")
    print("  show  - Show count")
    print("  exit  - Exit")

    while True:
        command = input("Enter command: ").strip().lower()
        if command == 'inc':
            counter.increment()
            print(f"Count incremented to {counter.get_count()}")
        elif command == 'dec':
            counter.decrement()
            print(f"Count decremented to {counter.get_count()}")
        elif command == 'show':
            print(f"Current count: {counter.get_count()}")
        elif command == 'exit':
            print("Exiting the Counter App. Goodbye!")
            break
        else:
            print("Invalid command. Please enter one of: inc, dec, show, exit.")

if __name__ == "__main__":
    main()