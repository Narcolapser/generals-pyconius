import random
import sys
import json

from generalsio import BaseBot, print_map, Tile

def get_surrounding(tile, tiles):
    delta_moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    response = []
    for move in delta_moves:
        position = (tile[0] + move[0], tile[1] + move[1])

        # Exclude positions off the map.
        if position[0] > len(tiles):
                    continue
        if position[1] > len(tiles[0]):
            continue
        if position[0] < 0:
            continue
        if position[1] < 0:
            continue

        # Exclude positions in the mountains
        try:
            if tiles[position[0]][position[1]] == Tile.MOUNTAIN:
                continue    
        except:
            continue

        response.append(position)
    return response

class Node():
    def __init__(self, position, parent, children, tiles, checked, player_index):
        self.position = position
        self.parent = parent
        self.tiles = tiles
        self.checked = checked
        self.player_index = player_index
        self.children = []
        #print(f'Setting up {position} child of {parent} with children {children}')

        for child in children:
            # Skip children that have alread been claimed.
            if child in self.checked:
                continue

            # Don't check children that are not owned by us.
            #print(f'Child {child} has value {tiles[child[0]][child[1]]}')
            if tiles[child[0]][child[1]] != player_index:
                self.children.append(child)
            else:
                # Check the remaining children
                self.checked.add(child)
                surrounding = get_surrounding(child,tiles)
                self.children.append(Node(child,position,surrounding,tiles,checked,player_index))
    
    def pretty_print(self, depth=0):
        tab = '\t'
        print(f'{tab * depth}Node {self.position} of {self.parent} with children:')
        for child in self.children:
            if(isinstance(child,Node)):
                child.pretty_print(depth+1)
            else:
                print(f'{tab*(depth+1)}Node {child} is unowned.')

    def get_leaves(self, depth=0):
        leaves = []
        for child in self.children:
            if isinstance(child,Node):
                leaves += child.get_leaves(depth+1)
            else:
                leaves.append((depth,child))

        return leaves
    
    def distance(self, target):
        if target == self.position:
            return [(0,self.position)]
        child_distances = []
        for child in self.children:
            if not isinstance(child,Node):
                if child == target:
                    child_distances.append((1,child))
            else:
                child_options = child.distance(target)
                if len(child_options) > 0:
                    child_distances.append((child_options[0][0]+1,child.position))
        if len(child_distances) > 0:
            child_distances.sort(key=lambda x:x[0])
        return child_distances


CONFIG_FILENAME = 'config.json'
class Bot(BaseBot):
    def handle_game_update(self, half_turns, tiles, armies, cities, enemy_position, 
                           enemy_total_army, enemy_total_land):
        self.world.update(tiles, armies, cities, enemy_position, enemy_total_army, enemy_total_land)
        pos = self.world.player_pos
        #print(f'Player owns {pos} which has a value {tiles[pos[0]][pos[1]]} and player index of {self.world.player_index}')
        

        # Construct a map from root to closest tiles not owned by us.
        checked = {self.world.player_pos}
        surrounding = get_surrounding(self.world.player_pos,tiles)
        root = Node(self.world.player_pos, None, surrounding, tiles, checked, self.world.player_index)
        #root.pretty_print()

        leaves = root.get_leaves()
        print(leaves)
        leaves.sort(key=lambda x: x[0])
        print(leaves)
        target = leaves.pop(0)[1] # Closes tile that isn't ours identified.
        print(f'attacking {target}')

        # Next find our largest army
        largest = self.world.player_pos
        print(f'player owns: {self.world.player_owned}')
        for tile in self.world.player_owned:
            if armies[largest[0]][largest[1]] <= armies[tile[0]][tile[1]]:
                largest = tile
        
        # Lastly figure out the best way from the largest army to the target
        route_checked = {largest}
        surrounding = get_surrounding(largest, tiles)
        largest_root = Node(largest, None, surrounding, tiles, route_checked, self.world.player_index)
        direction_options = largest_root.distance(target)
        print(f'Possible directions: {direction_options}')

        print(f'Target is {target} largest army is at {largest}')
        if len(direction_options) > 0:
            fastest = direction_options[0][1]
            print(f'Target is {target} largest army is at {largest} moving to {fastest}')
            self.client.attack(largest, fastest)
        else:
            print('skipping due to lack of options')

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
