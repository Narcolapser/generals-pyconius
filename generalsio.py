import json
import math
import random
from string import ascii_letters
from socketIO_client import SocketIO, BaseNamespace


class Tile(object): # enum
    EMPTY = -1
    MOUNTAIN = -2
    UNKNOWN = -3
    UNKNOWN_OBSTACLE = -4


class GameClientListener(object):
    def handle_game_update(self, half_turns, tiles, armies, cities, enemy_position, 
                           enemy_total_army, enemy_total_land):
        pass

    def handle_game_start(self, map_size, start_pos, enemy_username):
        pass

    def handle_game_over(self, won, replay_url):
        pass

    def handle_chat(self, username, message):
        pass


class GameClient(object):
    """
    A small SDK for the http://generals.io bot API.
    """
    SERVER_URL = 'https://bot.generals.io'
    REPLAY_URL_TEMPLATE = 'http://bot.generals.io/replays/%s'

    def __init__(self, user_id, username):
        self._sock = SocketIO(GameClient.SERVER_URL, Namespace=BaseNamespace)

        self._sock.on('connect', self._on_connect)
        self._sock.on('reconnect', self._on_reconnect)
        self._sock.on('disconnect', self._on_disconnect)
        self._sock.on('error_set_username', self._on_error_set_username)

        self._sock.on('game_won', self._on_game_won)
        self._sock.on('game_lost', self._on_game_lost)
        self._sock.on('game_start', self._on_game_start)
        self._sock.on('game_update', self._on_game_update)
        self._sock.on('chat_message', self._on_chat_message)

        if not username.startswith('[Bot] '):
            raise ValueError('username must start with "[Bot] "')
        self._sock.emit('set_username', user_id, username)
        self._user_id = user_id

        self._is_first_update = True
        self._game_ended = False
        self._in_queue = False
        self._in_game = False
        self._chat_room = None
        self._map_size = (None, None)
        self._map_num_elements = None
        self._player_index = None
        self._map = []
        self._cities = []
        self._enemy_player_index = None
        self._enemy_username = None
        self._enemy_total_army = 1
        self._enemy_total_land = 1
        self._replay_url = None

        self._game_started = False
        self._custom_game_id = None

        self._half_turns = 0
        self._sent_attack_orders = 0

        self._listeners = []

    def __del__(self):
        if hasattr(self, 'in_game') and self._in_game:
            self._leave_game()
        else:
            self._sock.emit('cancel', '1v1')
            self._in_queue = False

    def join_1v1_queue(self):
        if self._game_ended:
            raise ValueError('Game already completed. Please create a new GameClient to requeue.')
        self._sock.emit('join_1v1', self._user_id)
        self._in_queue = True

    def join_custom(self, custom_game_id):
        if self._game_ended:
            raise ValueError('Game already completed. Please create a new GameClient to requeue.')
        self._sock.emit('join_private', custom_game_id, self._user_id)
        force_start = True
        self._sock.emit('set_force_start', custom_game_id, force_start)
        self._in_queue = True
        self._custom_game_id = custom_game_id
        print('Joined custom queue')

    def chat(self, message):
        self._sock.emit('chat_message', self._chat_room, message)

    def attack(self, start, end, half_move=False):
        start_index = self._coord_to_index((int(start[0]), int(start[1])))
        end_index = self._coord_to_index((int(end[0]), int(end[1])))
        self._sock.emit('attack', start_index, end_index, half_move)
        self._sent_attack_orders += 1

    def clear_moves(self):
        self._sock.emit('clear_moves')

    def add_listener(self, listener):
        self._listeners.append(listener)

    def wait(self, seconds=None):
        self._sock.wait(seconds)
        if not self._game_started and self._custom_game_id:
            self._sock.emit('set_force_start', self._custom_game_id, True)

    def _leave_game(self):
        self._sock.emit('leave_game')
        self._game_ended = True
        self._in_game = False

    def _index_to_coord(self, index):
        return (
            math.floor(index / self._map_size[0]),
            index % self._map_size[0]
        )

    def _coord_to_index(self, coord):
        return coord[0] * self._map_size[0] + coord[1]

    def _on_game_won(self, data, _):
        for listener in self._listeners:
            listener.handle_game_over(won=True, replay_url=self._replay_url)
        self._leave_game()

    def _on_game_lost(self, data, _):
        for listener in self._listeners:
            listener.handle_game_over(won=False, replay_url=self._replay_url)
        self._leave_game()

    def _on_game_start(self, data, _):
        self._in_queue = False
        self._in_game = True

        self._player_index = data['playerIndex']
        self._replay_url = GameClient.REPLAY_URL_TEMPLATE % data['replay_id']
        self._enemy_player_index = int(not self._player_index)
        self._enemy_username = data['usernames'][self._enemy_player_index]

    def _on_game_update(self, data, _):
        self._half_turns = data['turn'] 
        self._map = _patch(self._map, data['map_diff'])
        self._cities = _patch(self._cities, data['cities_diff'])

        if self._is_first_update:
            self._map_size = (self._map[0], self._map[1])
            self._map_num_elements = self._map_size[0] * self._map_size[1]
            start_location = self._index_to_coord(data['generals'][self._player_index])
            for listener in self._listeners:
                listener.handle_game_start(self._map_size, start_location, self._enemy_username)
            self._is_first_update = False

        tiles = _list_to_mat(self._map[2 + self._map_num_elements:2 + self._map_num_elements**2], self._map_size)
        armies = _list_to_mat(self._map[2:2 + self._map_num_elements], self._map_size)
        enemy_position = data['generals'][self._enemy_player_index]
        enemy_total_army = data['scores'][self._enemy_player_index]['total']
        enemy_total_land = data['scores'][self._enemy_player_index]['tiles']

        for listener in self._listeners:
            listener.handle_game_update(
                half_turns=self._half_turns,
                tiles=tiles,
                armies=armies,
                cities=self._cities,
                enemy_position=enemy_position,
                enemy_total_army=enemy_total_army,
                enemy_total_land=enemy_total_land
            )

    def _on_chat_message(self, chat_queue, data):
        if 'username' in data:
            username = data['username']
        else:
            username = '[System]'
        for listener in self._listeners:
           listener.handle_chat(username, data['text'])

    def _on_connect(self):
        print('[Connected]')

    def _on_reconnect(self):
        print('[Reconnected]')

    def _on_disconnect(self):
        print('[Disconnected]')

    def _on_error_set_username(self, error_message):
        if error_message:
            print('Error setting username:', error_message)
        else:
            print('Username successfully set!')


def _list_to_mat(ilist, size):
    return [
        [ilist[x*size[0] + y] for y in range(size[0])]
        for x in range(size[1])
    ]


def _patch(old, diff):
    """Returns a new list created by modfying the old list using change information encoded in the
    generals.io list diff encoding.
    """
    new = []
    cursor = 0

    while cursor < len(diff):
        num_elems_matching = diff[cursor]
        if num_elems_matching != 0:
            new.extend(old[len(new):len(new)+num_elems_matching])
        cursor += 1
        if cursor >= len(diff):
            break
        num_elems_changed = diff[cursor]
        if num_elems_changed != 0:
            cursor += 1
            new.extend(diff[cursor:cursor+num_elems_changed])
        cursor += num_elems_changed
    return new


def pretty_print(json_like):
    print(json.dumps(json_like, sort_keys=True, indent=4, separators=(',', ': ')))

map_map = {-1:' ',-2:'M',-3:'.',-4:'m'}

def print_map(map):
    for i, row in enumerate(map):
        for char in row:
            if char < 0:
                print(map_map[char],end='')
            else:
                print(char,end='')
        print()
    print()
        

class Tile(object): # enum
    EMPTY = -1
    MOUNTAIN = -2
    UNKNOWN = -3
    UNKNOWN_OBSTACLE = -4

class WorldUnderstanding(object):
    def __init__(self):
        self.map_size = (None, None)
        self.enemy_pos = None
        self.player_pos = None

        self.cities = None
        self.mountains = set()

        self.last_seen_scores = None
        self.expected_scores = None

    def update(self, tiles, armies, cities, enemy_position, enemy_total_army, enemy_total_land):
        for x in range(self.map_size[0]):
            for y in range(self.map_size[1]):
                    if tiles[x][y] == Tile.MOUNTAIN:
                        self.mountains.add((x, y))


class Bot(GameClientListener):
    def __init__(self, user_id, username, custom_game_name):
        print('building bot')
        self.client = GameClient(user_id, username)
        self.world = WorldUnderstanding()
        self.client.add_listener(self)
        self.game_over = False
        print('instatiated')
        if custom_game_name:
            self.client.join_custom(custom_game_name)
        else:
            self.client.join_1v1_queue()

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
        move = random.choice(move_options)
        self.client.attack(self.world.player_pos, move)

    def handle_game_start(self, map_size, start_pos, enemy_username):
        print('Starting game')
        self.world.map_size = map_size
        self.world.player_pos = start_pos

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

if __name__ == '__main__':
    userid = ''.join([random.choice(ascii_letters) for i in range(16)])
    username = '[Bot] ' + ''.join([random.choice(ascii_letters) for i in range(4)])
    custom_game_name = "narconium"
    run_forever = False
    while True:
        bot = Bot(userid, username, custom_game_name)
        bot.block_forever()
        if not run_forever:
            break