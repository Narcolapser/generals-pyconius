import random
from string import ascii_letters
import sys

import commentjson
import numpy as np

from generalsio import Tile, GameClient, GameClientListener, WorldUnderstanding


CONFIG_FILENAME = 'config.json'





class Bot(GameClientListener):
    def __init__(self, user_id, username, custom_game_name):
        self.client = GameClient(user_id, username)
        self.world = WorldUnderstanding()
        self.client.add_listener(self)
        self.game_over = False
        self.client.join_custom(custom_game_name)
        self.printed_map = False

    def handle_game_update(self, half_turns, tiles, armies, cities, enemy_position, 
                           enemy_total_army, enemy_total_land):
        self.world.update(tiles, armies, cities, enemy_position, enemy_total_army, enemy_total_land)
        self.printed_map = True
        
        # Move randomly, sometimes into mountains.
        delta_moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        moves = []
        for tile in self.world.player_owned:
            for delta in delta_moves:
                position = (tile[0] + delta[0], tile[1] + delta[1])
                moves.append((tile,position))

        move = random.choice(moves)
        self.client.attack(move[0], move[1])

    def handle_game_start(self, map_size, start_pos, enemy_username):
        print('Starting game')
        self.world.map_size = map_size
        self.world.player_pos = start_pos
        self.world.player_index = self.client._player_index

    def handle_game_over(self, won, replay_url):
        if won:
            header = 'Game Won'
        else:
            header = 'Game Lost'
        print(header)
        print('='*len(header))
        print('Replay: %s\n' % replay_url)
        self.game_over = True

    def handle_chat(self, username, message):
        print('%s: %s' % (username, message))

    def block_forever(self):
        while not self.game_over:
            self.client.wait(seconds=2)


def main():
    if (len(sys.argv)) > 1:
        # Generate a random id
        user_id = ''.join([random.choice(ascii_letters) for i in range(16)])
        username = '[Bot] extra'
        custom_game_name = "delta"
        run_forever = False
        while True:
            bot = Bot(user_id, username, custom_game_name)
            bot.block_forever()
            if not run_forever:
                break

    else:
        custom_game_name = "delta"
        run_forever = False
        while True:
            config = commentjson.loads(open(CONFIG_FILENAME).read())    
            bot = Bot(config['user_id'], config['username'], custom_game_name)
            bot.block_forever()
            if not run_forever:
                break


if __name__ == '__main__':
    main()
