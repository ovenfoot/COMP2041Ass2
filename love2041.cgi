#!/usr/bin/perl -w
# Simple CGI script written by andrewt@cse.unsw.edu.au
# to demonstrate a possible CGI security hole

use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);




sub generateHtml
{
	print header, start_html('LOVE2041 MOTHERFUCKERS');
	warningsToBrowser(1);

}

sub generateData
{
	
}