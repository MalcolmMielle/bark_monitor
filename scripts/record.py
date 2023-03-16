from bark_monitor.very_bark_bot import VeryBarkBot


def main():
    threshold = 10_000
    VeryBarkBot(bark_level=threshold)


if __name__ == "__main__":
    main()
