"""
Module to read the contents of a message board
from a remote MUCK server.
"""
# TODO(hyena): Make this whole logic a background task in a larger program.
from collections import deque
from typing import Dict, List
import json
import logging

import ssltelnet
import toml


class MuckDownloader(object):
    """A class that facilitates downloading board contents from a MUCK such as SpinDizzy."""
    def __init__(self, host: str, port: int, ssl: bool, character: str, password: str,
                 get_posts_command: str, get_name_command: str, boards: List[str]):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.character = character
        self.password = password
        self.get_posts_command = get_posts_command
        self.get_name_command = get_name_command
        self.boards = boards

    def _get_posts_for_board(self, telnet, board_command='+read'):
        """
        Attempts to download the contents of a bulletin board.

        Requires that ``get_posts_command`` points to a valid
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
                .format(get_posts=self.get_posts_command, board=board_command)
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

    def _lookup_name(self, telnet, dbref):
        """
        Look up the name of a dbref.

        Requires that ``get_name_command`` points to an action configured as
        `@succ <action>=--- NAME: {name:{&arg}}`
        """
        telnet.read_very_eager()  # Clear out as much out of the pipe as possible.
        telnet.write("{get_name} {dbref}\n"
                .format(get_name=self.get_name_command, dbref=dbref)
                .encode(encoding='ascii'))
        telnet.read_until(b"--- NAME: ")
        name = telnet.read_until(b"\r\n")
        return name[:-2].decode()

    def get_posts(self):
        """Downloads the contents of all the configured boards, returning them as a dict."""
        # Connect to the MUCK
        s = ssltelnet.SslTelnet(force_ssl=self.ssl,
                                host=self.host,
                                port=self.port)
        s.write("connect {character} {password}\n"
                .format(character=self.character, password=self.password)
                .encode(encoding='ascii'))  # Oh for the day when UTF-8 is a reality.
        logging.debug("Connected to {server} and logged in as {character}."
                      .format(server=self.host, character=self.character))

        # Download all the posts for all the boards.
        boards = {}
        for board_command in self.boards:
            logging.debug("Retrieving posts for {board}".format(board=board_command))
            boards[board_command] = self._get_posts_for_board(telnet=s, board_command=board_command)

        # We now have all the posts - but the names are dbrefs. Find all the names to look up and fix them.
        logging.debug("Looking up names.")
        owner_dbrefs = set({})
        names = {}
        for board in boards.values():
            for post in board.values():
                owner_dbrefs.add(post['owner'])
        for dbref in owner_dbrefs:
            names[dbref] = self._lookup_name(telnet=s, dbref=dbref)
        # Include owner names
        for board in boards.values():
            for post in board.values():
                post['owner_name'] = names[post['owner']]
        logging.debug("Done formatting boards.")

        # Disconnect politely.
        s.write("QUIT\n".encode(encoding='ascii'))
        s.close()
        return boards


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    with open("config.toml") as config_file:
        conf = toml.loads(config_file.read())
    downloader = MuckDownloader(**(conf['muck']))
    print(json.dumps(downloader.get_posts(), indent=4))
