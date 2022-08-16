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
        if position[0] >= len(tiles):
                    continue
        if position[1] >= len(tiles[0]):
            continue
        if position[0] < 0:
            continue
        if position[1] < 0:
            continue

        # Exclude positions in the mountains
        if tiles[position[0]][position[1]] == Tile.MOUNTAIN:
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

    def step_towards(self, position, target):
        # Check that the position and the target are in the tree:
        if position not in self or target not in self:
            return False
        
        # Establish if one or the other of the children is self.
        if position == self.position:
            position_child = self
        else:
            position_child = None
        
        if target == self.position:
            target_child = self
        else:
            target_child = None

        print(f'self: {self.position} positon: {position} target: {target}')
        print(f'position in tree: {position in self} target in tree: {target in self}')
        print(f'position child: {position_child} target child: {target_child}')
        for child in self.children:
            if isinstance(child,Node):
                if position in child:
                    position_child = child
                if target in child:
                    target_child = child
            else:
                if position == child:
                    position_child = child
                if target == child:
                    target_child = child
            
            print(f'position in child {position in child or position == child} target in child {target in child or target == child}')

        # If both position and target are down the same branch, dig deeper.
        if position_child == target_child:
            return position_child.step_towards(position, target)
        
        # If they are down different branches we are in the lowest common parent. Here there are now 3 cases to
        # consider. First that we are the position and the target is down a branch. In this case we need to return
        # the position of the target child. Second that we are the target and third that both target and position are
        # down branches. In both of those cases we need the parent directly above the current position
        if position == self.position:
            if isinstance(target_child,Node):
                return target_child.position
            else:
                return target_child

        return self.parent_of(position)

        
    def parent_of(self, position):
        ''' Gets the parent of a provided node. Thus allowing you to travel up the tree.'''
        if position not in self:
            return False
        
        if position == self.position:
            return self.parent
        
        for child in self.children:
            if isinstance(child,Node):
                check = child.parent_of(position)
                if check:
                    return check
            else:
                if child == position:
                    return self.position
        return False


    def __contains__(self, position):
        print(f'checking contains. Self {self.position} position {position}')
        if self.position == position:
            return True
        
        tracker = False
        for child in self.children:
            if isinstance(child,Node):
                tracker |= position in child
            else:
                print(f'checking for child. child {child} position {position}')
                tracker |= position == child
        print(f'Found position in this branch {tracker}')
        return tracker
        


CONFIG_FILENAME = 'config.json'
class Bot(BaseBot):
    def handle_game_update(self, half_turns, tiles, armies, cities, enemy_position, 
                           enemy_total_army, enemy_total_land):
        try:
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
            
            fastest = root.step_towards(largest, target)

            print(f'Target is {target} largest army is at {largest}')
            if fastest:
                self.client.attack(largest, fastest)
            else:
                print('skipping due to lack of options')
        except Exception as e:
            print('Had a woopsy! Going to lap around and hope next turn something changes:')
            print(e)


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
        bot = Bot('iuhbghes', '[Bot] EdgeHawk', custom_game_name)
        bot.block_forever()
        if not run_forever:
            break


if __name__ == '__main__':
    main()
