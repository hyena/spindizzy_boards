"""
Module to read the contents of a message board
from a remote MUCK server.
"""
# TODO(hyena): Make this whole logic a background task in a larger program.
from collections import deque
import json
import logging

import ssltelnet
import toml


logging.basicConfig(level=logging.DEBUG)  # Be verbose for now.


# A bit inelegant. Read the config file first thing and put it in a global.
with open("config.toml") as config_file:
    conf = toml.loads(config_file.read())


def get_posts_for_board(telnet, board_command='+read'):
    """
    Attempts to download the contents of a bulletin board.

    Requires that ``conf['muck']['get_posts_command']`` points to a valid
    action that launches `muf/get_posts.muf`.
    """
    posts = {}
    lines = deque([])
    def check_line(line, prefix):
        "Helper method that ensures that a line starts with a particular prefix."
        assert line.startswith(prefix)
        return line.split(prefix)[1]

    telnet.read_very_eager()  # Clear out as much out of the pipe as possible.
    telnet.write("{get_posts} {board}\n"
            .format(get_posts=conf['muck']['get_posts_command'], board=board_command)
            .encode(encoding='ascii'))
    telnet.read_until(b"--- START\r\n")

    # Process line by line:
    while True:
        line = telnet.read_until(b"\r\n").decode()
        if line.startswith("--- ERROR: "):
            raise Exception("Couldn't retrieve boards posts: " + line[len("--- ERROR: "):])
        elif line == "--- END\r\n":
            break
        # Our MUF is coded to start all output with a '|' character.
        elif line.startswith("|"):
            # Strip out the leading "|" and the trailing "\r\n"
            lines.append(line[1:-2])
        else:
            raise Exception("Unexpected line in board output: " + line )

    while lines:
        line = lines.popleft()
        owner = check_line(line, prefix="owner: ")
        line = lines.popleft()
        time = int(check_line(line, prefix="time: "))
        line = lines.popleft()
        title = check_line(line, prefix="title: ")
        line = lines.popleft()
        length = int(check_line(line, prefix="length: "))
        lines.popleft()  # Drop the "content:" line

        content = ""
        for count in range(length):
            content += lines.popleft() + "\n"
        assert time not in posts
        posts[time] = {'owner': owner,
                       'time': time,
                       'title': title,
                       'content': content}

    return posts


def lookup_name(telnet, dbref):
    """
    Look up the name of a dbref.

    Requires that ``conf['muck']['get_name_command']`` points to an action configured as
    `@succ <action>=--- NAME: {name:{&arg}}`
    """
    telnet.read_very_eager()  # Clear out as much out of the pipe as possible.
    telnet.write("{get_name} {dbref}\n"
            .format(get_name=conf['muck']['get_name_command'], dbref=dbref)
            .encode(encoding='ascii'))
    telnet.read_until(b"--- NAME: ")
    name = telnet.read_until(b"\r\n")
    return name[:-2].decode()


# Connect to the MUCK
s = ssltelnet.SslTelnet(force_ssl=conf['server']['ssl'],
                        host=conf['server']['host'],
                        port=conf['server']['port'])
s.write("connect {character} {password}\n"
        .format(character=conf['muck']['character'], password=conf['muck']['password'])
        .encode(encoding='ascii'))  # Oh for the day when UTF-8 is a reality.
logging.info("Connected to {server} and logged in as {character}."
             .format(server=conf['server']['host'], character=conf['muck']['character']))

# Download all the posts for all the boards.
boards = {}
for board_command in conf['muck']['boards']:
    logging.info("Retrieving posts for {board}".format(board=board_command))
    boards[board_command] = get_posts_for_board(telnet=s, board_command=board_command)

# We now have all the posts - but the names are dbrefs. Find all the names to look up and fix them.
logging.info("Looking up names.")
owner_dbrefs = set({})
names = {}
for board in boards.values():
    for post in board.values():
        owner_dbrefs.add(post['owner'])
for dbref in owner_dbrefs:
    names[dbref] = lookup_name(telnet=s, dbref=dbref)
# Replace owner dbrefs with names
for board in boards.values():
    for post in board.values():
        post['owner'] = names[post['owner']]


# Done. Output some pretty content.
logging.info("Done. Outputting json.")
print(json.dumps(boards, indent=4))
