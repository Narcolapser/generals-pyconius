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
        #moves = [np.add(self.world.player_pos, delta_move) for delta_move in delta_moves]
        moves = [(self.world.player_pos[0] + move[0], self.world.player_pos[1] + move[1]) for move in delta_moves]
        def move_feasible(position):
            if tuple(position) in self.world.mountains:
                return False
            if not 0 <= position[0] < self.world.map_size[0]:
                return False
            if not 0 <= position[1] < self.world.map_size[1]:
                return False
            return True
        move_options = [move for move in moves if move_feasible(move)]
        #print(move_options)
        move = random.choice(move_options)
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
