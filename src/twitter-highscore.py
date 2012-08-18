#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from optparse import OptionParser
import ConfigParser
import MySQLdb
import twitter
import time, datetime
import json

config = ConfigParser.ConfigParser()
config.read('/home/tovok7/sexypirates/config.ini')

# Parse Command Line Options
usage = "usage: %prog option [user1] [[user2] ...]"
parser = OptionParser(usage=usage, version="%prog 0.1")
parser.add_option("-a", "--add",    dest="add",    action="store_true", help="Add a new users and rebuild.")
parser.add_option("-d", "--delete", dest="delete", action="store_true", help="Delete a users and rebuild.")
parser.add_option("-u", "--update", dest="update", action="store_true", help="Update the database from Twitter and rebuild.")
parser.add_option("-b", "--build",  dest="build",  action="store_true", help="Only build the HTML pages.")
parser.add_option("-t", "--tweet",  dest="tweet",  action="store_true", help="Tweet to notify added or removed users.")
parser.add_option("", "--debug",  dest="debug",  action="store_true", help="Print debugging output.")
#parser.add_option("-x", "--test",  dest="test",  action="store_true", help="Test.")
(opt, args) = parser.parse_args()

# Set-up database connection
db = MySQLdb.connect(
    host = config.get('MySQL', 'host'),
    user = config.get('MySQL', 'user'),
    passwd = config.get('MySQL', 'pass'),
    db = config.get('MySQL', 'db'),
    use_unicode = True,
    charset = 'utf8'
)

# Set-up Twitter API
api = twitter.Api(
    consumer_key        = config.get('Twitter', 'consumer_key'),
    consumer_secret     = config.get('Twitter', 'consumer_secret'),
    access_token_key    = config.get('Twitter', 'access_token_key'),
    access_token_secret = config.get('Twitter', 'access_token_secret')
)

cursor = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

def main():
    if(opt.update):
        update_users()
        build_pages()
    elif(opt.build):
        build_pages()
#    elif(opt.test):
#        print get_twitter_reset_time()
    elif(len(args) < 1):
        print "No arguments specified!\n"
        parser.print_help()
        sys.exit(1)
    else:
        if(opt.add):
            text = ''
            for user in args:
                add_user(user)
                text += '@' + user + ' '
            print text + 'ihr seid jetzt auch #sexypirates auf http://sexypirates.org/'
            build_pages()
        elif(opt.delete):
            for user in args:
                del_user(user)
            build_pages()
        else:
           print "No command line option specified.\n"
           parser.print_help()
           sys.exit(1)

    db.close()


def build_pages():
    highscore = get_highscore()
    print_highscore(highscore)


def get_highscore():
    try:
        cursor.execute("SELECT `users`.`id`, `screen_name`, `count`, `name`, `description`, `location`, `profile_image_url`, `url`, `users`.`fetch_time`\
                FROM `followers`, `users`\
                WHERE `followers`.`id` = `users`.`id` AND `key_id` IN (SELECT MAX(`key_id`) FROM `followers` GROUP BY `id`)\
                ORDER BY `count` DESC")
        rows = cursor.fetchall()
        return rows
    except MySQLdb.IntegrityError, msg:
        print msg


def print_highscore(highscore):
    f = open(config.get('Twitter Highscore', 'document_root')+'/index.html', "w")
    
    print_header(f, 'SexyPirates.org')

    f.write('<table align="center">')

    position = 1

    for user in highscore:
        f.write('<tr>')
        f.write('<td class="pos">' + str(position) + '</td>')
        f.write('<td><a href="/' + user['screen_name'] + '"><img src="' + user['profile_image_url'] + '"/></a></td>')
        f.write('<td>' + user['name'].encode('ascii', 'xmlcharrefreplace') + ' (<a href="https://twitter.com/'+user['screen_name']+'">@' + user['screen_name'] + '</a>)</td>')
        f.write('<td class="fol">' + str(user['count']) + '</td>')
        f.write('</tr>')
        print_user_page(user, position)
        position += 1

    f.write("</table>")
    f.write('<div class="footer">Du bist Piratin, fehlst aber auf dieser Liste? Sag <a href="http://twitter.com/t_grote">@t_grote</a> Bescheid!</div>')
    f.write('</body>')
    f.write('</html>')

    f.close()
    
    if(opt.tweet):
        text = 'Neues Update von http://sexypirates.org Die 42 ist @%s #sexypirates' % highscore[41]['screen_name']
        api.PostUpdates(text)
        print 'Tweeted "' + text + '".'

    print "The web sites have been rebuilt!"


def print_user_page(user, score):
    try:
        cursor.execute("SELECT `count`, `fetch_time` FROM `followers` WHERE `id` = %(id)s", user)
        rows = cursor.fetchall()
    except MySQLdb.IntegrityError, msg:
        print msg   

    series = []
    for row in rows:
        series.append( {'x': time.mktime(row['fetch_time'].timetuple()), 'y': row['count']} )
    
    f = open(config.get('Twitter Highscore', 'document_root')+'/user/'+user['screen_name']+'.html', "w")

    print_header(f, 'SexyPirates.org - ' + user['screen_name'])

    f.write('<div class="box">')
    f.write('<img src="' + user['profile_image_url'].replace('_normal.', '.') + '"/>')
    f.write('<div class="user">')
    f.write('<div class="big">' + user['name'].encode('ascii', 'xmlcharrefreplace') + ' (<a href="https://twitter.com/' + user['screen_name'] + '">' + user['screen_name'] + '</a>)</div>')
    f.write('<div>ist auf Platz <b class="big">' + str(score) + '</b> mit <b class="big">' + str(user['count']) + '</b> Followern.</div>')
    f.write('<div class="bio">' + user['description'].encode('ascii', 'xmlcharrefreplace') + '</div>')
    f.write('<div>' + user['location'].encode('ascii', 'xmlcharrefreplace') + '</div>')
    if(user['url']):
        f.write('<div><a href="' + user['url'] + '">' + user['url'] + '</a></div>')
    f.write('</div><br/>')
#    f.write('<div id="chart_container"><div id="y_axis"></div><div id="chart"></div></div>');
    f.write('</div><br/>')
    f.write('<div class="footer">')
    f.write('Du m&ouml;chtest nicht hier stehen? Sag <a href="http://twitter.com/t_grote">@t_grote</a> Bescheid!<br/>')
    f.write('Letztes Update am ' + str(user['fetch_time']) + '.')
    f.write('</div>')

    if(False):
        f.write('<script>')
        f.write('data = ' + json.dumps(series) +';')

        f.write('''var graph = new Rickshaw.Graph( {
        element: document.querySelector("#chart"),
        width: 540,
        height: 240,
        renderer: 'line',
        series: [ {
                data: data, 
                color: 'steelblue',
                name: 'Follower'
        } ]
} );

var x_axis = new Rickshaw.Graph.Axis.Time( { graph: graph } );

var y_axis = new Rickshaw.Graph.Axis.Y( {
        graph: graph,
        orientation: 'left',
        tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
        pixelsPerTick: 20,
        element: document.getElementById('y_axis'),
} );

graph.render();

var hoverDetail = new Rickshaw.Graph.HoverDetail( {
    graph: graph,
    formatter: function(series, x, y) {
        var date = '<span class="date">' + new Date(x * 1000 - new Date().getTimezoneOffset() * 60000).toUTCString() + '</span>';
        var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
        var content = swatch + series.name + ": " + parseInt(y) + '<br/>' + date;
        return content;
    }
} );

</script>''')

    f.write('</body>')
    f.write('</html>')

    f.close()


def print_header(f, title):
    f.write('<html>');
    f.write('<head>');
    f.write('<title>' + title + '</title>');
    f.write('<link rel="stylesheet" href="/style.css">');

    if(False):
        f.write('<link rel="stylesheet" href="/css/rickshaw.min.css">')
        f.write('<script src="/js/d3.min.js"></script>')
        f.write('<script src="/js/d3.layout.min.js"></script>')
        f.write('<script src="/js/rickshaw.js"></script>')
        f.write('<style>')
        f.write('#chart_container { background-color: #FFFFFF; position: relative; font-family: Arial, Helvetica, sans-serif; clear: both; display: inline-block; margin-top: 2em;}')
        f.write('#chart { position: relative; left: 40px; }')
        f.write('#y_axis { position: absolute; width: 40px;}')# top: 0; bottom: 0; }')
        f.write('.rickshaw_graph .detail .x_label { display: none }')
        f.write('.rickshaw_graph .detail .item { line-height: 1.4; padding: 0.5em }')
        f.write('.detail_swatch { float: right; display: inline-block; width: 10px; height: 10px; margin: 0 4px 0 0 }')
        f.write('.rickshaw_graph .detail .date { color: #a0a0a0 }')
        f.write('</style>')

    f.write('</head>');
    f.write('<body>');
    f.write('<div class="header">');
    f.write('<span id="headline"><a href="/">Who Are The Sexiest Pirates?</a></span>')
    f.write('<br/><span id="slogan">Themen statt K&ouml;pfe!</span>')
    f.write('</div>');


def update_users():
    limit = api.GetRateLimitStatus()['remaining_hits']

    if(limit <= 1):
        secs = get_twitter_reset_time()
        if(opt.debug):
            print "Waiting for %d seconds..." % secs
        time.sleep(secs)
        if(opt.debug):
            print "Continuing..."
        # get new limit
        limit = api.GetRateLimitStatus()['remaining_hits']

    try:
        # select all entries older than %d days and use 10 minutes flexibility
        cursor.execute("SELECT `id` FROM `users`\
                WHERE TIMESTAMPADD(DAY, -%d, TIMESTAMPADD(MINUTE, 10, NOW())) >= `fetch_time`\
                LIMIT %d" % (int(config.get('Twitter Highscore', 'fetch_interval')), limit) )
        rows = cursor.fetchall()
    except MySQLdb.IntegrityError, msg:
        print msg

    for user in rows:
        add_followers_count(user['id'])

    # run again if there might be more
    if(len(rows) >= limit):
        update_users()


def add_followers_count(user_id):
    user = api.GetUser(user_id)
    try:
        cursor.execute("""INSERT INTO `followers` (`id`, `count`, `fetch_time`)\
                VALUES (%(_id)s, %(_followers_count)s, NOW())""", user.__dict__)

        cursor.execute("UPDATE `users` SET `screen_name`=%(_screen_name)s, `name`=%(_name)s, `location`=%(_location)s,\
                `description`=%(_description)s, `profile_image_url`=%(_profile_image_url)s, `url`=%(_url)s,\
                `fetch_time`=NOW() WHERE `id` = %(_id)s", user.__dict__)

        print "Entry for " + user.screen_name + " added with " + str(user.followers_count) + " followers."
    except MySQLdb.IntegrityError, msg:
        print msg


def add_user(user_id):
    user = api.GetUser(user_id)

    try:
        cursor.execute("""INSERT INTO `users` (`id`, `screen_name`, `name`, `location`, `description`, `profile_image_url`, `url`, `fetch_time`)\
                VALUES (%(_id)s, %(_screen_name)s, %(_name)s, %(_location)s, %(_description)s, %(_profile_image_url)s, %(_url)s, NOW())""", user.__dict__)
        
        cursor.execute("""INSERT INTO `followers` (`id`, `count`, `fetch_time`)\
                VALUES (%(_id)s, %(_followers_count)s, NOW())""", user.__dict__)

        print 'New entry for ' + user.screen_name + ' added.'
        
        if(opt.tweet):
            text = '@' + user.screen_name + ' Du bist jetzt auch einer von den #sexypirates http://sexypirates.org'
            api.PostUpdates(text)
            print 'Tweeted "' + text + '".'
    except MySQLdb.IntegrityError, msg:
        if(msg[0] == 1062):
            print 'This user was already added.'
        else:
            print msg


def del_user(user_id):
    user = api.GetUser(user_id)

    try:
        cursor.execute("DELETE FROM `users` WHERE `id` = %(_id)s", user.__dict__)
        cursor.execute("DELETE FROM `followers` WHERE `id` = %(_id)s", user.__dict__)

        print user.screen_name + ' was removed.'
        
        if(opt.tweet):
            text = '@' + user.screen_name + ' Du bist jetzt aus http://sexypirates.org raus. #sexypirates'
            api.PostUpdates(text)
            print 'Tweeted "' + text + '".'
    except MySQLdb.IntegrityError, msg:
        print msg
    
    # remove user profile page
    file = config.get('Twitter Highscore', 'document_root') + '/user/' + user.screen_name + '.html'
    if(os.path.isfile(file)):
        os.remove(file)


def get_twitter_reset_time():
    # get time of rate limit reset from API
    reset_time = api.GetRateLimitStatus()['reset_time']
    # convert to datetime object
    limit = datetime.datetime.strptime(reset_time, '%a %b %d %H:%M:%S +0000 %Y')
    # calculate difference between reset time and now
    delta = limit - datetime.datetime.utcnow()
    # timedelta in seconds
    delta = delta.seconds
    
    # return result with small time buffer
    return delta + 10


if __name__ == '__main__':
    main()
