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
config.read('config.ini')

# Parse Command Line Options
usage = "usage: %prog option [user1] [[user2] ...]"
parser = OptionParser(usage=usage, version="%prog 0.1")
parser.add_option("-a", "--add",    dest="add",    action="store_true", help="Add a new users and rebuild.")
parser.add_option("-d", "--delete", dest="delete", action="store_true", help="Delete a users and rebuild.")
parser.add_option("-u", "--update", dest="update", action="store_true", help="Update the database from Twitter and rebuild.")
parser.add_option("-b", "--build",  dest="build",  action="store_true", help="Only build the HTML pages.")
parser.add_option("-t", "--tweet",  dest="tweet",  action="store_true", help="Tweet to notify added or removed users.")
parser.add_option("-s", "--silent", dest="silent", action="store_true", help="Don't produce any output.")
parser.add_option("", "--debug",    dest="debug",  action="store_true", help="Print debugging output.")
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
        if(opt.tweet):
            text = 'Neues Update von http://sexypirates.org Die 42 ist @%s #sexypirates' % highscore[41]['screen_name']
            api.PostUpdates(text)
            if(not opt.silent):
                print 'Tweeted "' + text + '".'
    elif(opt.build):
        build_pages()
#    elif(opt.test):
#        add_followers_count('t_grote')
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
    print_highscore(get_highscore_follower(),       print_follower_score,       '/index.html', print_users=True)
    print_highscore(get_highscore_age(),            print_age_score,            '/sort/age.html', ' - Alter')
    print_highscore(get_highscore_tweets(),         print_tweets_score,         '/sort/tweets.html', ' - Tweets')
    print_highscore(get_highscore_tweets_per_day(), print_tweets_per_day_score, '/sort/tweets-per-day.html', ' - Tweets am Tag')


def get_highscore_follower():
    try:
        cursor.execute("SELECT `users`.`id`, `screen_name`, `count`, `name`, `description`, `location`,\
                `profile_image_url`, `url`, `statuses_count`, `created_at`, `users`.`fetch_time`\
                FROM `followers`, `users`\
                WHERE `followers`.`id` = `users`.`id` AND `key_id` IN (SELECT MAX(`key_id`) FROM `followers` GROUP BY `id`)\
                ORDER BY `count` DESC")
        rows = cursor.fetchall()
        return rows
    except MySQLdb.IntegrityError, msg:
        print msg

def print_follower_score(f, user):
    f.write('<td class="score">' + str(user['count']) + '</td>')


def get_highscore_age():
    try:
        cursor.execute("SELECT `id`, `screen_name`, `name`, `description`, `location`,\
                `profile_image_url`, `url`, `statuses_count`, `created_at`, `fetch_time`\
                FROM `users`\
                ORDER BY `created_at` ASC")
        rows = cursor.fetchall()
        return rows
    except MySQLdb.IntegrityError, msg:
        print msg

def print_age_score(f, user):
    f.write('<td class="score">' + str(user['created_at'].date().strftime('%d.%m.%Y')) + '</td>')


def get_highscore_tweets():
    try:
        cursor.execute("SELECT `id`, `screen_name`, `name`, `description`, `location`,\
                `profile_image_url`, `url`, `statuses_count`, `created_at`, `fetch_time`\
                FROM `users`\
                ORDER BY `statuses_count` DESC")
        rows = cursor.fetchall()
        return rows
    except MySQLdb.IntegrityError, msg:
        print msg

def print_tweets_score(f, user):
    f.write('<td class="score">' + str(user['statuses_count']) + '</td>')


def get_highscore_tweets_per_day():
    try:
        cursor.execute("SELECT `id`, `screen_name`, `name`, `description`, `location`,\
                `profile_image_url`, `url`, `statuses_count`, `created_at`, `fetch_time`,\
                `statuses_count` / TIMESTAMPDIFF(DAY, `created_at`, NOW()) AS `tweets_per_day`\
                FROM `users`\
                ORDER BY `tweets_per_day` DESC")
        rows = cursor.fetchall()
        return rows
    except MySQLdb.IntegrityError, msg:
        print msg

def print_tweets_per_day_score(f, user):
    f.write('<td class="score">%.2f</td>' % user['tweets_per_day'])


def print_highscore(highscore, print_score, path, title='', print_users=False):
    f = open(config.get('Twitter Highscore', 'document_root') + path, "w")
    
    print_header(f, 'SexyPirates.org' + title)

    # Print Menu
    f.write('<div class="footer">')
    f.write('Was ist sexy? ')
    if(print_score == print_follower_score):
        f.write('Gefolgschaft, ')
    else:
        f.write('<a href="/">Gefolgschaft</a>, ')
    if(print_score == print_age_score):
        f.write('Alter, ')
    else:
        f.write('<a href="/sort/age">Alter</a>, ')
    if(print_score == print_tweets_score):
        f.write('viele Tweets oder ')
    else:
        f.write('<a href="/sort/tweets">viele Tweets</a> oder ')
    if(print_score == print_tweets_per_day_score):
        f.write('viele Tweets pro Tag?')
    else:
        f.write('<a href="/sort/tweets-per-day">viele Tweets pro Tag</a>?')
    f.write('</div>')

    f.write('<table align="center">')

    position = 1

    for user in highscore:
        f.write('<tr>')
        f.write('<td class="pos">' + str(position) + '</td>')
        f.write('<td><a href="/' + user['screen_name'] + '"><img src="' + user['profile_image_url'] + '"/></a></td>')
        f.write('<td>' + user['name'].encode('ascii', 'xmlcharrefreplace') + ' (<a href="https://twitter.com/'+user['screen_name']+'">@' + user['screen_name'] + '</a>)</td>')
        print_score(f, user)
        f.write('</tr>')
        if(print_users):
            print_user_page(user, position)
        position += 1

    f.write("</table>")
    f.write('<div class="footer">Du bist Piratin, fehlst aber auf dieser Liste? Sag <a href="http://twitter.com/t_grote">@t_grote</a> Bescheid!</div>')

    print_footer(f)

    f.close()

    if(not opt.silent):
        print "The web sites have been rebuilt!"


def print_user_page(user, score):
    if(config.getboolean('Twitter Highscore', 'draw_charts')):
        try:
            cursor.execute("SELECT `count`, `fetch_time` FROM `followers` WHERE `id` = %(id)s", user)
            rows = cursor.fetchall()
        except MySQLdb.IntegrityError, msg:
            print msg

        series = []
        for row in rows:
            series.append( {'x': time.mktime(row['fetch_time'].timetuple()), 'y': row['count']} )
    
    # calculate tweets per day
    avg = float(user['statuses_count']) / (datetime.datetime.utcnow() - user['created_at']).days
    avg = '%.2f' % avg
    avg = avg.replace('.', ',')

    f = open(config.get('Twitter Highscore', 'document_root')+'/user/'+user['screen_name']+'.html', "w")

    print_header(f, 'SexyPirates.org - ' + user['screen_name'])

    f.write('<div class="box">')
    f.write('<img src="' + user['profile_image_url'].replace('_normal.', '.') + '"/>')
    f.write('<div class="user">')
    f.write('<div class="big">' + user['name'].encode('ascii', 'xmlcharrefreplace') + ' (<a href="https://twitter.com/' + user['screen_name'] + '">@' + user['screen_name'] + '</a>)</div>')
    f.write('<div>')
    f.write('ist auf Platz <b class="big">' + str(score) + '</b> mit <b class="big">' + str(user['count']) + '</b> Followern,')
    f.write('<p>seit dem <b>' + user['created_at'].date().strftime('%d.%m.%Y') + '</b> auf Twitter ')
    f.write('und schreibt durchschnittlich <b>' + avg + '</b> Tweets am Tag.</p>')
    f.write('</div>')
    f.write('<div class="bio">' + user['description'].encode('ascii', 'xmlcharrefreplace') + '</div>')
    f.write('<div>' + user['location'].encode('ascii', 'xmlcharrefreplace') + '</div>')
    if(user['url']):
        f.write('<div><a href="' + user['url'] + '">' + user['url'] + '</a></div>')
    f.write('</div><br/>')
    if(config.getboolean('Twitter Highscore', 'draw_charts') and len(series) > 1):
        f.write('<div id="chart_container"><div id="y_axis"></div><div id="chart"></div></div>');
    f.write('</div><br/>')
    f.write('<div class="footer">')
    f.write('Du m&ouml;chtest nicht hier stehen? Sag <a href="http://twitter.com/t_grote">@t_grote</a> Bescheid!<br/>')
    f.write('Letztes Update am ' + str(user['fetch_time']) + '.')
    f.write('</div>')

    if(config.getboolean('Twitter Highscore', 'draw_charts') and len(series) > 1):
        f.write('<script>')
        f.write('data = ' + json.dumps(series) +';')

        f.write('''var graph = new Rickshaw.Graph( {
        element: document.querySelector("#chart"),
        width: 600,
        height: 300,
        renderer: 'line',
        min: 'auto',
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

    print_footer(f)
    f.close()


def print_header(f, title):
    f.write('<html>');
    f.write('<head>');
    f.write('<title>' + title + '</title>');
    f.write('<link rel="stylesheet" href="/css/style.css">');

    if(config.getboolean('Twitter Highscore', 'draw_charts')):
        f.write('<link rel="stylesheet" href="/css/rickshaw.min.css">')
        f.write('<script src="/js/d3.min.js"></script>')
        f.write('<script src="/js/d3.layout.min.js"></script>')
        f.write('<script src="/js/rickshaw.js"></script>')

    f.write('</head>');
    f.write('<body>');
    f.write('<div class="header">');
    f.write('<span id="headline"><a href="/">Who Are The Sexiest Pirates?</a></span>')
    f.write('<br/><span id="slogan">Themen statt K&ouml;pfe!</span>')
    f.write('</div>');


def print_footer(f):
    if(config.getboolean('Piwik', 'tracking')):
        f.write('<script src="' + config.get('Piwik', 'base_url') +'piwik.js" type="text/javascript"></script>')
        f.write('<script type="text/javascript">')
        f.write('var pkBaseURL = "' + config.get('Piwik', 'base_url') + '";')
        f.write('var piwikTracker = Piwik.getTracker(pkBaseURL + "piwik.php", ' + config.get('Piwik', 'idsite') + ');')
        f.write('piwikTracker.trackPageView();')
        f.write('piwikTracker.enableLinkTracking();')
        f.write('</script>')
        f.write('<noscript><p>')
        f.write('<img src="' + config.get('Piwik', 'base_url') + 'piwik.php?idsite=' + config.get('Piwik', 'idsite') + '" style="border:0" alt="" />')
        f.write('</p></noscript>')

    f.write('</body>')
    f.write('</html>')


def update_users():
    limit = 100
    rate_limit = api.GetRateLimitStatus()['remaining_hits']

    if(limit > rate_limit and rate_limit > 1):
        limit = rate_limit
    elif(rate_limit <= 1):
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
                WHERE TIMESTAMPADD(HOUR, -%d, TIMESTAMPADD(MINUTE, 10, NOW())) >= `fetch_time`\
                LIMIT %d" % (config.getint('Twitter Highscore', 'fetch_interval'), limit) )
        rows = cursor.fetchall()
    except MySQLdb.IntegrityError, msg:
        print msg

    # assemble list of twitter IDs
    ids = []
    for row in rows:
        ids.append(row['id'])

    try:
        users = api.UsersLookup(ids)

        print "Got %d users from twitter" % len(users)
        for user in users:
            add_followers_count(user)

        # run again if there might be more
        if(len(rows) >= limit):
            print "run update_users() again"
            update_users()
    except AttributeError, msg:
        print "Error: Twitter API response returned no users. Maybe one was deleted or deactivated."


def add_followers_count(user):
    # these are errors you might want to look at so don't respect --silent
    if(user.screen_name == None):
        print "User with id '%s' seems to be deactivated or deleted. Skipping..." % user_id
        # TODO handle that somehow!
        return
    if(user.followers_count == 0):
        print "Query for user '%s' with id '%s' has returned 0 followers. Not adding..." % (user.screen_name, user.id)
        return

    try:
        cursor.execute("""INSERT INTO `followers` (`id`, `count`, `fetch_time`)\
                VALUES (%(_id)s, %(_followers_count)s, NOW())""", user.__dict__)

        cursor.execute("UPDATE `users` SET `screen_name`=%(_screen_name)s, `name`=%(_name)s, `location`=%(_location)s,\
                `description`=%(_description)s, `profile_image_url`=%(_profile_image_url)s, `url`=%(_url)s,\
                `statuses_count`=%(_statuses_count)s, `fetch_time`=NOW() WHERE `id` = %(_id)s", user.__dict__)

        if(not opt.silent):
            print "Entry for " + user.screen_name + " added with " + str(user.followers_count) + " followers."
    except MySQLdb.IntegrityError, msg:
        print msg


def add_user(user_id):
    user = api.GetUser(user_id)

    # transform created_at datetime into proper format
    user.created_at = datetime.datetime.strptime(user.created_at, '%a %b %d %H:%M:%S +0000 %Y').isoformat(' ')

    try:
        cursor.execute("""INSERT INTO `users` (`id`, `screen_name`, `name`, `location`,\
                `description`, `profile_image_url`, `url`, `statuses_count`, `created_at`, `fetch_time`)\
                VALUES (%(_id)s, %(_screen_name)s, %(_name)s, %(_location)s,\
                %(_description)s, %(_profile_image_url)s, %(_url)s, %(_statuses_count)s, %(_created_at)s, NOW())""", user.__dict__)
        
        cursor.execute("""INSERT INTO `followers` (`id`, `count`, `fetch_time`)\
                VALUES (%(_id)s, %(_followers_count)s, NOW())""", user.__dict__)

        if(not opt.silent):
            print 'New entry for ' + user.screen_name + ' added.'
        
        if(opt.tweet):
            text = '@' + user.screen_name + ' Du bist jetzt auch einer von den #sexypirates http://sexypirates.org'
            api.PostUpdates(text)
            if(not opt.silent):
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

        if(not opt.silent):
            print user.screen_name + ' was removed.'
        
        if(opt.tweet):
            text = '@' + user.screen_name + ' Du bist jetzt aus http://sexypirates.org raus. #sexypirates'
            api.PostUpdates(text)
            if(not opt.silent):
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
