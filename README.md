PLEASE NOTICE
=============

Do not use this. This was put together in a hurry and is no where near a stable
condition.


About
=====

Family Feud (german: Familien Duell)
http://en.wikipedia.org/wiki/Family_Feud
http://de.wikipedia.org/wiki/Familien-Duell

Dependencies
============

python2.7 (since pygame only works with python2)
pygame


Howto
=====

[g1](https://github.com/fiji-flo/duell/blob/master/g1) provides an example
configuration of a game. A game consists of 4 normal rounds plus the final.

To launch the game go to the repository root directory and launch:

> $ python2.7 sd.py

You can pass an argument to change the title display on the game screen:

> $ python2.7 sd.py "my fancy title"

After launching the game you have to connect to the simple web interface
running on port 8001.

On the same machine simply use:

> http://localhost:8001

If you want to access the machine remotely use the ip address of the host.

> http://<HOST_IP>:8001


Web Interface
-------------

### Fist step:

Click on *Initialize Game Screen*. The game field should appear.

### Load a Game

To load a game, put the game description file into the repository root
directory. Next go to the web interface and enter the exact filename into
the input field right in front of the *Load Game* button. Press the button to
set up the new game.

### Start a Round

To start a round click on one of the four *Round X* buttons. Enter the team
names into the corresponding input fields and press the according *set* buttons.

### How to Play a Round

Please take the time to watch an episode (of the german version) of family feud.
The controls are very basic. Click on the according answer button and the answer
will appear. After a short dealy the corresponding points will appear.

If someone gives a wrong answer during the inital fight that decides which team
will play the round press the *Wrong(non counting)* button to get the wrong
answer buzzer sound.

After the round is over. Please assign the points to the winner team by pressing
the *<team name>* button.

The two fields below the team buttons can be used to adjust (set) the points.

### Final

In the final round you have to search a corresponding answer in the drop down
boxes. If there was no fitting answer use the wrong button.

Use the *hide* button to hide the answers and points of the first player.

File Encoding
=============

PyGame and encoding is a mess. Please make sure the game configuration files are
plain utf-8 files.
