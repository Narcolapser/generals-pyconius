# generalsio
generals.io (turn based strategy game) game bot

To start a basic bot for you to test against you can execute the generalsio.py file as well. This will create a simple bot that will just move around it's origin. This provides enough activity to prevent the bot from getting kicked for inactivity but not so much that it will matter much to what ever testing you might be doing. Execute one of the following

``` 
python generalsio.py
python3 generalsio.py
```

## Creating your first bot

This repository comes with a basic example: bot.py. Copy this file to get started quickly in making a new bot. The `handle_game_update` method is the primary one you will want to be concerned with. It is run every turn and the line at the end of it `self.client.attack(self.world.player_pos, move)` is what you use to declare where you want to attack/move units. The order is tile you are attacking from to tile you are sending troops. To run it execute one of the following:

```
python bot.py
python3 bot.py
```

Executing it without any arguments will drop it into the "delta" game room. Include an argument to get to a different room:

```
python bot.py test_room
```