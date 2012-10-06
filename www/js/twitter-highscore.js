/*    Twitter Highscore
 *    Copyright (C) 2012  Torsten Grote
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

var highlighter
var palette = new Rickshaw.Color.Palette();
palette.scheme = [ '#FF8800', '#6193AE', '#FF0000', '#00FF00', 'FF00FF', '#0006BF', '#C00000', '#C05800', '#FFFF00', '#00FFFF' ];

function add_twitter_user(user) {
    $.ajax({
        url: '/user/' + user.toLowerCase() + '.json',
        dataType: 'json',
        async: true,
        success: function(data) { add_twitter_line(user, data); },
        error: function(xhr, status, error) { alert("We don't have any data for " + user + "."); }
    });
}

function add_twitter_line(user, data) {
    // Fix rickshaw bug by making both series the same length
    while(series[0].data.length > data.length) {
//        data.push(data[data.length-1]);
        series[0].data.shift();
    }
    while(window.series[0].data.length < data.length) {
//        series[0].data.push(series[0].data[series[0].data.length-1]);
        data.shift();
    }

    new_series = {
        data: data,
        color: palette.color(),
        name: user
    };
    series.push(new_series);
    graph.update();

    // Hide hover detail due to rickshaw bug
    $('.detail').hide();

    // Add legend
    if(graph.series.length < 3) {
        legend = new Rickshaw.Graph.Legend( {
            graph: graph,
            element: document.getElementById('legend')
        } );
    } else {
        legend.addLine(new_series);
    }

    // link to profile page from legend
    $('#legend span[class="label"]').replaceWith(function() {
        var url = $.trim($(this).text());
        return '<a href="/' + url + '" class="label" target="_blank">' + url + '</a>';
    } );
}

// execute this when page is fully loaded
$(function() {
    $('input[name="add_line_button"]').click(function() {
        add_twitter_user($('input[name="twitter_user"]').val())
    } );

    // Click button when enter is pressed
    $('input[name="twitter_user"]').keyup(function(event){
        if(event.keyCode == 13) add_twitter_user($('input[name="twitter_user"]').val());
    } );

    // Enable Auto-complete
    $.getJSON('/user_list.json', function(data) {
        $('input[name="twitter_user"]').autocomplete({
            lookup: data
        } );
    } );

    var hash = window.location.hash;
    if(hash != '') {
        var users = hash.split('#');
        users.shift();

        $.each(users, function(index, user) {
            add_twitter_user(user);
        } );
    }
} );
