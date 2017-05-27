
"""A 'placeholder' module for testing other parts of the program without an actual MUCK
connection setup to read posts."""

from typing import List
from datetime import datetime
import logging

# This allows us to test the webapp without setting up a 'live' muck
# account and running the MUF every time.

class MuckDownloader(object):
    """A fake class to pretend we downloaded board contents from a MUCK
    such as SpinDizzy."""
    def __init__(self, host: str, port: int, ssl: bool, character: str, password: str,
                 get_posts_command: str, get_name_command: str, boards: List[str]):
        pass

    def get_posts(self):
        # (maybe) TODO: Make something a little more clever -- create a bunch of
        # posts with random content and dates ranging from yesterday to tomorrow
        # at a fixed interval, and serve all posts where post.date <= now...
        logging.debug("(fake) MuckDownloader.get_posts() at {}"
                          .format(datetime.now().strftime("%D %T")))
        return {
            '+read': {
                1495648230: {
                    'owner': '#1234',
                    'owner_name': 'Bob',
                    'time': 1495648230,
                    'title': 'Principles of Thermo-Dynamic Transpilation',
                    'content': """The software engineering method to superblocks is defined not only by the study of Moore's Law, but also by the private need for the World Wide Web. In this paper, we disconfirm the evaluation of the Ethernet. In this work we disconfirm that though the seminal self-learning algorithm for the investigation of public-private key pairs by Wang et al. is Turing complete, A* search and telephony can agree to overcome this quagmire.

The implications of efficient algorithms have been far-reaching and pervasive. The notion that end-users agree with the study of congestion control is never well-received. The notion that scholars synchronize with introspective methodologies is mostly adamantly opposed. On the other hand, DHCP alone cannot fulfill the need for Boolean logic. Our intent here is to set the record straight.

Motivated by these observations, the lookaside buffer and reliable communication have been extensively refined by computational biologists. The basic tenet of this solution is the analysis of model checking. In addition, it should be noted that Bull evaluates Bayesian theory. Although conventional wisdom states that this grand challenge is mostly solved by the evaluation of superblocks, we believe that a different method is necessary [16]. Unfortunately, this solution is usually well-received.

Bull, our new application for perfect epistemologies, is the solution to all of these problems. Further, our approach is derived from the exploration of RPCs. It should be noted that Bull observes amphibious theory. For example, many applications store suffix trees. We emphasize that Bull is copied from the principles of machine learning. Obviously, we describe new empathic algorithms (Bull), arguing that red-black trees and A* search can cooperate to achieve this intent."""},

                1495648618: {
                    'owner': '#5678',
                    'owner_name': 'Alice',
                    'time': 1495648618,
                    'title': 'In Defense of Circular Definitions For Compilers',
                    'content': """A robust method to overcome this issue is the understanding of gigabit switches. Existing empathic and optimal solutions use lambda calculus to emulate DHCP. although conventional wisdom states that this issue is largely answered by the investigation of suffix trees, we believe that a different solution is necessary. Two properties make this approach optimal: our application explores red-black trees, and also our application prevents thin clients, without locating information retrieval systems. Thus, we see no reason not to use large-scale information to emulate ubiquitous symmetries. Even though this might seem counterintuitive, it is derived from known results.

We proceed as follows. Primarily, we motivate the need for the transistor. We place our work in context with the existing work in this area. To address this issue, we construct a methodology for IPv7 (Bull), proving that gigabit switches and the transistor are largely incompatible [10]. Similarly, we place our work in context with the previous work in this area. Finally, we conclude."""}
            }
        }
