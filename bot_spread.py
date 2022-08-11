import random
import sys
import json

from generalsio import BaseBot, print_map

CONFIG_FILENAME = 'config.json'
class Bot(BaseBot):
    def handle_game_update(self, half_turns, tiles, armies, cities, enemy_position, 
                           enemy_total_army, enemy_total_land):
        self.world.update(tiles, armies, cities, enemy_position, enemy_total_army, enemy_total_land)
        print_map(tiles)
        print(self.world.player_owned)
        # Move randomly
        delta_moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        moves = []
        for tile in self.world.player_owned:
            for delta in delta_moves:
                position = (tile[0] + delta[0], tile[1] + delta[1])
                moves.append((tile,position))

        move = random.choice(moves)
        self.client.attack(move[0], move[1])

def main():
    if len(sys.argv) > 1:
        custom_game_name = sys.argv[1]
        run_forever = False
        print('Joining custom game %s' % custom_game_name)
    else:
        custom_game_name = "delta"
        run_forever = False
        print('Joining delta')

    while True:
        config = json.loads(open(CONFIG_FILENAME).read())    
        bot = Bot(config['user_id'], config['username'], custom_game_name)
        bot.block_forever()
        if not run_forever:
            break


if __name__ == '__main__':
    main()
