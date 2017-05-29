from datetime import datetime
import logging
import threading
import time
from typing import Dict

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound
import pytz
import toml

from muck_downloader import FakeMuckDownloader, MuckDownloader


_TIME_FORMAT = "%Y-%m-%d %I:%M %p"


class SpinDizzyBoards(object):
    """
    A class that is responsible for most of the functionality
    of the app.

    It includes all the view callables for the web app.

    It also includes a background process that is responsible
    for keeping content up to date.
     - Checks for new posts at a specified interval.
     - Updates the state for the web-app.
     - [Unimplemented] Sends out alerts to Twitter and Mastodon.
    """
    def __init__(self, config: Dict):
        """
        Args:
            config (dict): A parsed config.toml object.
        """
        if config['fake_muck']:
            self.downloader = FakeMuckDownloader(**config['muck'])
        else:
            self.downloader = MuckDownloader(**config['muck'])
        self.boards = [x[0] for x in config['muck']['boards']]
        self.board_names = {x[0]: x[1] for x in config['muck']['boards']}
        self.current_content = {}  # Will be filled in by a background thread.
        self.url_base = config['web']['url_base']
        self.tz = pytz.timezone(config['timezone'])

        # Start up our background task.
        self.interval = config['interval']
        self.download_thread = threading.Thread(target=self.background_download)
        self.download_thread.daemon = True
        self.download_thread.start()

    def post2template(self, x):
        """
        This function does a little processing to turn the raw data
        associated with a post into the form a template expects.

        Right now the only real reason to do this is to provide a
        human-readable date generated by strftime(), but in the future
        we could also do some formatting (e.g., just enough to allow
        *italic* and **bold** text) and any other similar things
        here, if desired.
        """
        return { 'id': x['time'],
                 'humantime': datetime.fromtimestamp(x['time'], self.tz).strftime(_TIME_FORMAT),
                 'author_name': x['owner_name'],
                 'title': x['title'],
                 'content': x['content']
               }

    def command_for_post(self, board: str, post_id: int):
        """ Generate the muck side command to read a given postid, given present board contents."""
        # This assumes that the posts are sorted by time.
        index = sorted(self.current_content[board].keys()).index(post_id) + 1
        return "{} {}".format(board, index)

    def url_for_post(self, board: str, post_id: int):
        url_base = self.url_base[:-1] if self.url_base.endswith('/') else self.url_base
        return "{}/{}/{}".format(url_base, board, post_id)

    def background_download(self):
        """Background task to download board content."""
        # TODO(hyena): This isn't especially fault tolerant right now.
        # If it dies in a recoverable fashion, we should log the error and retry.
        # Conversely if it dies to a logical or fatal error, we should kill the
        # the webserver too. Unfortunately right now if anything goes wrong, this
        # thread dies quietly.
        while True:
            next_runtime = time.time() + self.interval
            old_content = self.current_content
            # Expose the downloaded content without waiting for sending announcements.
            # The GIL makes this safe.
            self.current_content = self.downloader.get_posts()
            if old_content:  # Only send out alerts if we previously had content.
                for board in self.current_content:
                    for post_id in self.current_content[board]:
                        if post_id not in old_content[board]:
                            logging.debug("New post {post_id} in {board}"
                                          .format(post_id=post_id, board=board))
                            print("{name} posted {subject}. {command} or {url} to read."
                                  .format(name=self.current_content[board][post_id]['owner_name'],
                                          subject=self.current_content[board][post_id]['owner_name']['title'],
                                          command=self.command_for_post(board, post_id),
                                          url=self.url_for_post(board, post_id)))
                        elif ((old_content[board][post_id]['title']
                               != self.current_content[board][post_id]['title'])
                              or (old_content[board][post_id]['content']
                                  != self.current_content[board][post_id]['content'])):
                            logging.debug("Editted post {post_id} in {board}"
                                          .format(post_id=post_id, board=board))
            # New content gotten, alerts made. Rest if we can....
            sleep_length = next_runtime - time.time()
            if sleep_length > 0:
                time.sleep(sleep_length)

    ### View Callables.
    def list_boards(self, request):
        """View callable that shows a list of available boards."""
        loaded_boards = self.current_content.keys()
        boards = [x for x in self.boards if x in loaded_boards]
        return {'boards': boards,
                'board_names': self.board_names,
                }

    def list_posts(self, request):
        """View callable that shows all the posts on a particular board."""
        # Grab this at the start because it might get updated in a background thread.
        content = self.current_content
        board = request.matchdict['board_command'].lower()
        if board not in content:
            raise HTTPNotFound("No such board found.")
        return {'posts': [self.post2template(x)
                          for x in sorted(content[board].values(), key=lambda p: p['time'])],
                'board': board,
                'board_name': self.board_names[board],
               }

    def view_post(self, request):
        """View callable that shows the contents of a post."""
        # Grab this at the start because it might be updated by the background thread.
        content = self.current_content
        board = request.matchdict['board_command'].lower()
        postid = int(request.matchdict['post_id'])
        if board not in content or postid not in content[board]:
            raise HTTPNotFound("Post not found")
        return {'post': self.post2template(content[board][postid]),
                'board': board,
                'board_name': self.board_names[board],
               }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    with open("config.toml") as config_file:
        conf_toml = toml.loads(config_file.read())
    worker = SpinDizzyBoards(conf_toml)

    # Set up webapp routes.
    # Note that this could also be accomplished with pyramid's traversal functionality.
    # However, I think that for this usage case that adds more complexity than it's worth.
    config = Configurator()
    config.include("pyramid_jinja2")

    config.add_route('board_list', '/')
    config.add_view(worker.list_boards, route_name='board_list', renderer="templates/boardlist.jinja2")

    config.add_route('posts_list', '/{board_command}')
    config.add_view(worker.list_posts, route_name='posts_list', renderer="templates/postlist.jinja2")

    config.add_route('view_post', '/{board_command}/{post_id:\d+}')
    config.add_view(worker.view_post, route_name='view_post', renderer="templates/post.jinja2")

    # TODO(hyena): Set up a *real* wsgi environment.
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', conf_toml['web']['port'], app)
    server.serve_forever()
