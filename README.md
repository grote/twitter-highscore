Twitter Highscore
=================

This script allows you to generate a highscore of Twitter users as static HTML
files. It provides sorting by number of followers, account age, number of tweets
and tweets per day. For every user a dedicated profile page is created that
optionally shows a graph displaying the evolution of follower numbers over time.


Requirements
------------

* Python >=2.6
* Python modules:
  * [MySQLdb](http://mysql-python.sourceforge.net/)
  * [twitter](https://code.google.com/p/python-twitter/)
  * [requests](http://www.python-requests.org)
* MySQL Database


Installation
------------

1. Download [Twitter Highscore](https://github.com/Tovok7/twitter-highscore/zipball/master)
2. Create a MySQL database and apply `doc/database.sql` to it
3. Copy `doc/config.ini.sample` to `src/config.ini`
4. Edit `src/config.ini` following the inline comments
5. Run `src/twitter-highscore.py --help` to get started


License
-------

![GNU AGPLv3 Image](https://www.gnu.org/graphics/agplv3-88x31.png)

This program is free software: You can use, study share and improve it at your
will. Specifically you can redistribute and/or modify it under the terms of the
[GNU Affero General Public License](https://www.gnu.org/licenses/agpl.html) as
published by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

