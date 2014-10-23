#!/usr/bin/perl -w
# Simple CGI script written by andrewt@cse.unsw.edu.au
# to demonstrate a possible CGI security hole
use Cwd;
use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use File::Copy;


#######################################################################
#		GLOBAL VAR INITIALISATION
#######################################################################
$cgiFolder = "http://cgi.cse.unsw.edu.au/~tngu211/students/";
$dataFolder = getcwd."/students/";
$defaultProfileFilename = "profile.txt";
$currProfile = "";
$homeUrl = "http://cgi.cse.unsw.edu.au/~tngu211/love2041.cgi";
$userListURL = "http://cgi.cse.unsw.edu.au/~tngu211/love2041.cgi?|allusers";
$authenticated = 0;
$timeToLive = 600; #seconds
%globalSessionData = ();
$profPerPage = 3;

#create a hash of private fields
%privateFields = ();
$privateFields{"uname"} = 1;
$privateFields{"password"} = 1;
$privateFields{"email"} = 1;
$privateFields{"found"} = 1;
$privateFields{"courses"} = 1;
$privateFields{"name"} = 1;
$privateFields{"profileImage"} = 1;
$privateFields{"username"} = 1;
$privateFields{"otherPhotos"} = 1;
$privateFields{"path"} = 1;

#beginPage();


#######################################################################
#		MAIN EXECUTION STATE MACHINE
#######################################################################

#statemachine based on session
#check session checks REMOTE_ADDR.acc file on server directory
#if session is not currently authenticated, redirect user to login screen
#if session is authenticated, then allow for more complex use of site
if (checkSession() != 0)
{
	#session is not authenticated

	if(defined(param ("uname")) && defined(param("pass")) )
	{
		#if params defined, user has attempted to log in

		$globalSessionData{"authenticated"} = authenticate();
		if($globalSessionData{"authenticated"} ==0)
		{
			#successful login. update session file
			updateSession();;
			#let them into the rest of the site
			generateNUserList($profPerPage, 0);
		}
		else
		{
			#unsuccessful. go back to login page
			generateLoginPage();	
		}
	}
	else
	{
		#no login attempt, go to login page
		generateLoginPage();
	}
}
elsif ($ENV{'QUERY_STRING'} eq "" )
{
	#empty query string, show them the list of users
	generateNUserList($profPerPage, 0);
}
elsif ($ENV{'QUERY_STRING'} =~ /^[\|].*/ )
{
	#nonempty query with a command character '|'
	#process the command and dcide what to do

	my $query = $ENV{'QUERY_STRING'};
	$query =~ s/\|//g;


	#switch through the queries and decide what page to display
	if($query eq "allusers")
	{
		generateAllUserListHtml();
	}
	elsif($query eq "logout")
	{
		logout();
	}
	elsif($query =~ /$|userlist(\d+)/)
	{
		my $nthPage = $1;
		generateNUserList($profPerPage, $nthPage);
	}


}
else
{
	#nonempty query string indicates a user has been requested
	#generate user page file based on query string
	$currProfile = $ENV{'QUERY_STRING'};
	generateUserHtml($currProfile);
}





#######################################################################
#		HERE BEGIN YONDER FUNCTIONS
#######################################################################

#take in username and password to check against database
#return 0 for success, <0 for fail
sub authenticate
{
	my $uname = param('uname');
	my $password = param('pass');

	my %udata = generateProfileData($uname);
	if (!$udata{"found"})
	{
		#no user found, failed to authenticate
		return (-1);
	}

	my $actpass = $udata{"password"};
	$actpass=~ s/\s*$//g;
	$actpass =~ s/^\s*//g;

	$password =~ s/\s*$//g;
	if ($actpass eq $password)
	{
		#password matched
		param("actPass", $password);
		param("upass", $udata{"password"});
		return 0;#
	}
	else
	{
		#password unmatched
		return (-2);
	}
}



#prints all start html tags and generic page properties
sub beginPage
{
	print header;
	print start_html(-title=>'LOVE2041 MOTHERFUCKERS');

	print "<link rel='stylesheet' type='text/css' href='style.css'>\n";

	print p $ENV{"REMOTE_ADDR"};

}

#prints all end html tags and generic hidden variables
sub endPage
{

	if ($globalSessionData{"authenticated"} == 0)
	{
		print h2;
		print "<center>";
		printLink($homeUrl."?|logout", "Log Out");
		print "</center>";
		print "</h2>";
		updateSession();
	}

	print '<!-- Designed by DreamTemplate. Please leave link unmodified. -->
		<br><center><a href="http://www.dreamtemplate.com" title="Website Templates" target="_blank">Website templates</a></center>';
	print end_html;

}

#on logout, delete session data and print logout page
sub logout
{
	
	my $ip = $ENV{"REMOTE_ADDR"};
	$ip =~ s/\./\_/g;
	my $sessionFile = "$ip.acc";

	unlink $sessionFile;
	$globalSessionData{"authenticated"} = -1;
	beginPage();
		print h2 "logged out";
	print p;
	printLink($homeUrl, "Go home");
	endPage();


}

#prints debug string to html
sub debugPrint
{
	my ($debugString) = @_;
	print header;
	print start_html(-title=>'LOVE2041 MOTHERFUCKERS',
								-bgcolor=>'CCFF33');


	print p $debugString;
	print end_html;

}

#login page. Generate everything necessary
sub generateLoginPage
{

	#create a new session page for login
	createNewSession();

	beginPage();
	print h1 "Welcome to LOVE2041, the most ghetto piece of shit dating website ever";

	#login form
	print start_form,
        'Enter login: ', p textfield('uname'), p "<br>\n",
        ' Enter password: ', p password_field('pass'),p "<br>\n",
        submit('Login'),
        end_form;
		

	endPage();
}

#generates list of all users currently in the pseudo-database
#first argument is the 'failed login attempt' flag
sub generateAllUserListHtml
{
	#print header;
	beginPage();

	my @users = getUserList();
	warningsToBrowser(1);

	print h1 "Browse Users";

	#for eahc user print a link with a query string to get user data
	foreach my $user (@users)
	{

		my $userURL = $homeUrl."?$user";
		print p;
		printLink($userURL, $user);
		#print p $user;
	}

	endPage();
}

#generates a list of n mini profiles to view
#first argument is number of prifles per page
#second argument is page requested to be viewed
#eg (10,2) will so profiles 21-30;
sub generateNUserList
{

	my @input = @_;
	my $profilesPerPage = $input[0];
	my $page = $input[1];
	my $index = 0;
	my @users = getUserList();


	$totalPages = $#users/$profilesPerPage + 1;

	my $nthUser = $page*$profilesPerPage + 1;

	#if page is greater than total pages then mod the number
	$page = $page % $totalPages;

	beginPage();
	print h1 "Browse Users";

	#print out 3 users as a table
	print center;
	print '<table>';
	print '<tr>';
	#pick the next n users from the userlist and print pictures and username
	for (my $i = 0; $i <$profilesPerPage; $i++)
	{
		$index = ($i + $nthUser) % $#users;
		my $userURL = $homeUrl."?$users[$index]";

		my %udata = generateProfileData($users[$index]);

		print '<td>';
		printImageLink($userURL, $udata{"profileImage"}, 70);
		printLink($userURL, $users[$index]);
		print '</td>';
		print "\n";
		

	}
	print '</tr>';
	
	print '<tr>';

	#calculate next and previous page links
	#if we hit the end, don't print the next/prev link
	my $nextPage = ($page+1);
	my $prevPage = ($page-1);
	print td;
	if($prevPage >= 0)
	{
		printLink($homeUrl."?|userlist$prevPage", "Prev Page");
	}
	for (my $i=1; $i<$profilesPerPage; $i++)
	{
		print td;
		if ($i == int($profilesPerPage/2))
		{
			printLink($homeUrl."?|allusers", "List all profiles");
		}
	}
	if ($nextPage < $totalPages)
	{
		printLink($homeUrl."?|userlist$nextPage", "Next Page");
	}
	print '</tr>';

	print '</table>';
	
	#update session data about the last page person was browsing
	$globalSessionData{"last_profile_browse"} = $page;
	endPage();

}

#scans the /students/ folder and extracts out all the users
sub getUserList
{
	opendir my $userdirs, $dataFolder;
	my @allUsers = readdir $userdirs;
	my @returnUsers = ();
	closedir $userdirs;
	foreach my $user (@allUsers)
	{
		if (($user =~ /\w+.*/ ))
		{
			push @returnUsers, $user;
		}
	}
	return @returnUsers;
}

#generates all the data for one particular user
#first argument is the desired username
sub generateUserHtml
{
	my ($uname) = @_;
	my @currData = ();
	my %udata = ();
	my @otherPhotos = ();
	my $lastURL = ();
	#print header;

	beginPage();

	warningsToBrowser(1);

	%udata = generateProfileData($uname);
	if (! $udata{"found"})
	{
		print "fuck cannot find $uname\n";
		return (-1);
	}


	print h1 "$uname";

	#print profile picture from path stored in hash
	$imagePath = $udata{"profileImage"};
	print "<img src=$imagePath><p>\n";	
	
	#go through each data field and print values
	#check if field is private
	foreach my $field (keys %udata)
	{
		
		if(!exists ($privateFields{$field}))
		{
			#check if the field is not private, print it
			$fieldToPrint = prettyInput ($field);
			print h2 "$fieldToPrint";
			@currData = split ('\n',$udata{$field});
			foreach my $entry (@currData)
			{
				print p "$entry";
			}
		}
	}

	#extract photo file names and embed them in the page
	print h2 "Other Photos";
	@otherPhotos = split(/\|/, $udata{"otherPhotos"});
	foreach my $photo (@otherPhotos)
	{	
		$imagePath = $udata{"path"}.$photo;
		print "<img src=$imagePath><p>\n";
	}
	print p;
	

	#end of page, go home links

	#last page browsed stored in session
	$lastURL = $homeUrl."?|userlist".$globalSessionData{"last_profile_browse"};
	print h1;
	printLink($lastURL, "Back to User List");

	print p;
	printLink($homeUrl, "Go home");

	endPage();

}


#Grab profile data for given username.
#takes 1 argument, username desired
#returns hash of user profile data
sub generateProfileData
{
	my ($uname) = @_;
	my $ufolder = $dataFolder.$uname."/";
	my $ucgiFolder = $cgiFolder.$uname."/";
	my $profileFile = $ufolder.$defaultProfileFilename;
	my @tabspaces = ();
	my %userData = ();
	my $currField = "";
	my $tabstring= ();
	my @otherPhotos = ();

	$userData{"uname"} = $uname;
	
	if (!(-R $profileFile))
	{
		#print "user $uname not  found!\n";
		$userData{"found"} = 0;
		return %userData;
	}
	
	#go through each line of the file
	#use tab delimitation to figure out if something is a field or a value
	#use a pseudo state machine to decide when to pass in a field or a value 
	open (pFile, "< $profileFile");
	$userData{"found"} = 1;
	foreach $line (<pFile>)
	{
		chomp $line;
		
		@tabspaces = $line =~ m/^\t+/g;
		
		if ($#tabspaces<0) 
		{
			#tabspaces less than one means a field has been added
			$currField = $line;
			$currField =~ s/://g;
			$userData{$currField} = "";
		}
		elsif (!($currField eq ""))
		{
			#extra check to make sure that currfield is not empty
			#tabpsaces greater than 1 indicates a data field
			$userData{$currField} = prettyInput($userData{$currField}.$line."\n");
		}

	}


	$userData{"profileImage"} = $ucgiFolder."profile.jpg";
	close (pFile);

	#open the directory and see if there are any other photos to display
	#return the photos as a string joined by '|'
	opendir my $udir, $ufolder;
	@otherPhotos = grep{/photo\d*\.jpg/} readdir $udir;
	$userData{"otherPhotos"} = join('|',@otherPhotos);
	closedir $udir;
	
	$userData{"path"} = $ucgiFolder;

	return %userData;

}


#create a new session file
#session files used for authentication
#initialise globalSession data to default values and write to session file
sub createNewSession
{
	my $ip = $ENV{"REMOTE_ADDR"};
	$ip =~ s/\./\_/g;
	my $sessionFile = "$ip.acc";
	%globalSessionData = ();

	$globalSessionData{"REMOTE_ADDR"} = $ip;
	$globalSessionData{"last_access"} = gmtime();
	$globalSessionData{"timeout"}		= time()+$timeToLive;
	$globalSessionData{"authenticated"} = -1;


	updateSession();
}

#dump all current session data to the file and save for further use
sub updateSession
{
	my $ip = $ENV{"REMOTE_ADDR"};
	$ip =~ s/\./\_/g;
	my $sessionFile = "$ip.acc";

	$globalSessionData{"last_access"} = localtime();
	$globalSessionData{"timeout"}		= time()+$timeToLive;


	open (sFile, "> $sessionFile");

	foreach my $key (keys %globalSessionData)
	{
		print sFile "$key,$globalSessionData{$key}\n";
	}

	close sFile;

	return $globalSessionData{"authenticated"};
}

#load session data into memory
#if authenticated and checks out, return 0
#If no session data found, return error and force person to sign in
sub checkSession
{
	my $ip = $ENV{"REMOTE_ADDR"};
	$ip =~ s/\./\_/g;
	my $sessionFile = "$ip.acc";

	open (sFile, "< $sessionFile");

	foreach my $line (<sFile>)
	{
		@data = split(/\,/, $line);
		$globalSessionData{$data[0]} = $data[1];
	}

	close sFile;

	
	if (!(-R $sessionFile))
	{
		return -1;
	}
	my $timeToDie = $globalSessionData{"timeout"} - time();
	my $authenticated = $globalSessionData{"authenticated"};
	
	return $authenticated;
}



#captilises first letter of each word in a string
#removes underscores where not necessary
sub prettyInput
{
	my ($input) = @_;
	my @words = split ('\_', $input);
	my $output = "";

	foreach my $word (@words)
	{
		$word = ucfirst ($word);
	}

	$output = join(' ', @words);
	return $output;

}

#helper function to print hyperlinks
#first argument is the desired address
#second argument is the desied display text
sub printLink
{
	my @inputs = @_;
	my $addr = $inputs[0];
	my $text = "";
	if(defined $inputs[1])
	{
		$text = $inputs[1];
	}
	else
	{
		$text = $addr;
	}

	print "<a ";
	print 'href="';
	print $addr;
	print '" ';
	print ">";
	print $text;
	print "</a>\n";
}

#helper argument to print image link
#first argument is desired address
#second argument is picture to be displayed
#third optional argument is scaling percentage
sub printImageLink
{
	my @inputs = @_;
	my $addr = $inputs[0];
	my $imagePath = $inputs[1];

	if (defined $inputs[2])
	{
		$scale = $inputs[2];
	}
	else
	{
		$scale = 100;
	}

	print "<a ";
	print 'href="';
	print $addr;
	print '" ';
	print ">";
	print "<img src=$imagePath width = $scale\% height = $scale\% = s><p>\n";
	print "</a>\n";

}