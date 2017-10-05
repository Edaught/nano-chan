"""
Actually runs the code
"""
from bot import Nanochan
from cogs import Spoils, Filter, Janitor, Moderation, Stats


def run():
    bot = Nanochan()
    cogs = [
      Spoils(bot),
      Filter(bot),
      Janitor(bot),
      Moderation(bot),
      Stats(bot)
    ]
    bot.start_bot(cogs)


if __name__ == '__main__':
    run()
