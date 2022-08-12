import random
import sys
import json

from generalsio import BaseBot, print_map, Tile

CONFIG_FILENAME = 'config.json'
class Bot(BaseBot):
    def handle_game_update(self, half_turns, tiles, armies, cities, enemy_position, 
                           enemy_total_army, enemy_total_land):
        self.world.update(tiles, armies, cities, enemy_position, enemy_total_army, enemy_total_land)
        # Move randomly
        delta_moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        all_moves = []
        capture_moves = []
        for tile in self.world.player_owned:
            for delta in delta_moves:
                target = (tile[0] + delta[0], tile[1] + delta[1])
                # Avoid invalid moves off the edge of the map
                if target[0] > len(tiles):
                    continue
                if target[1] > len(tiles[0]):
                    continue
                if target[0] < 0:
                    continue
                if target[1] < 0:
                    continue

                # Don't attempt to spread into mountians.
                if tiles[target[0]][target[1]] == Tile.MOUNTAIN:
                    continue
                
                # Don't attempt to move tiles with one troop on them.
                if armies[tile[0]][tile[1]] < 2:
                    continue

                if target not in tiles:
                    capture_moves.append((tile,target))

                all_moves.append((tile,target))

        moves = all_moves
        if len(capture_moves) == 0:
            print('no capture moves available. spreading')
        else:
            moves = capture_moves

        if len(moves) == 0:
            print('skipping, no valid moves')
        else:
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
        bot = Bot('alskdjlfe', '[Bot] CESpread', custom_game_name)
        bot.block_forever()
        if not run_forever:
            break


if __name__ == '__main__':
    main()
