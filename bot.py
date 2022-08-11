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

        # Move randomly
        delta_moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]    
        moves = [(self.world.player_pos[0] + move[0], self.world.player_pos[1] + move[1]) for move in delta_moves]
        move = random.choice(moves)
        self.client.attack(self.world.player_pos, move)

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
