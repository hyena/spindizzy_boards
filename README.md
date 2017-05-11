SpinDizzy Remote Board Reader
=============================

This is an app designed to remotely read the contents of a bulletin board on (SpinDizzy MUCK)[https://muck.spindizzy.org] and expose it as json. It requires a bit of set-up MUCK side to get it working and a login there, which should ideally be a dedicated bot used `@set` 'H(aven)'.

Although this project was made specifically for SpinDizzy, with some modification it should work for other FuzzBall MUCK that have CorkBoard.muf installed. Notably, you'll need to change a dbref in `get_posts.muf`.

If you're having trouble, bother Regan on SpinDizzy.


MUCK components set-up
----------------------
These instructions assume you have a SpinDizzy character with a `M1` bit, preferably one designed to operate as a bot. Using your own account should be fine for testing, though.
  1. Copy the contents of (get_posts.muf)[muf/get_posts.muf] and make a program out of it (if you don't know much about MUF or using the editor http://www.universitymuck.org/book/export/html/14 may be a good starting place).
  I named mine `read-posts.muf` but you can name your program whatever you wish.
  2. Create an action somewhere your bot can access it and link it to the program you made. I named mine `process_posts` and attached it to the room my bot lives in:
  ```
  @action process_posts=here
  @link process_posts=read-posts.muf
  ```
  3. Test your command. e.g. `process_posts +read`. If everything is set up correctly, you'll see the contents of the bulletin board fly by.

FuzzBall's security is somewhat Kafkaesque: With `M1` permissions in MUF, we can look up the dbref of a global name like `+read`, but we can't remotely look up the name of dbref we pull off the board like `|owner: #2057`. However, using MPI we can't look up the dbref of a global that's not in the same room as us--but we _can_ look up the name of any dbref. So to get people-friendly character names instead of dbrefs, we're going to need a bit of mpi that can look-up dbrefs.

  4. Make an action where your character/bot can access it, link it to `$nothing` and give it a success value of `--- NAME: {name:{&arg}}`. e.g.:
  ```
  @action getname=here
  @link getname=$nothing
  @succ getname=--- NAME: {name:{&arg}}
  ```
  It's important that the `@succ` value is set up exactly as the above for the program to work.
  5. Try an owner value from the board listings you outputted earlier. e.g. `getname #2056`. You should see something like `--- NAME: Morticon`.


Python set-up
-------------
Once you've set up the above and confirmed the MUCK side of the world is working, it's time to setup and the Python app. I recommend that you use a virtual environment for this set-up (e.g. `python3 -m venv ve`), but it's not necessary.

This code has been tested with Python 3.5, but should probably work in 2.7 and 3.6.
  1. Activate your virtual environment if any.
  2. `pip install -r requirements.txt`
  3. `cp config.toml.sample config.toml`
  4. Open `config.toml` with your favorite editor and fill in the values appropriately for how you've set up your muck environment.
  5. Test it: `python download_posts.py` You should see some progress messages on stderr and then the boards' content dumped to stdout as json.


TODO
----
This is a cute little demo. The next step is probably to make it a periodic task that feeds or populates some web-app.


Acknowledgements
----------------
Thanks to @kelketek of Winter's Oasis for the CorkBoard.muf implementation, whose API makes this easy.
