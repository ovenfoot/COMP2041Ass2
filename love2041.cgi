#!/usr/bin/perl -w
# Simple CGI script written by andrewt@cse.unsw.edu.au
# to demonstrate a possible CGI security hole
use Cwd;
use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
#use Email::MIME;
#use Email::Sender::Simple qw(sendmail);
use File::Copy;
use Time::Local;


#TODO2: Multiple image upload

#######################################################################
#		GLOBAL VAR INITIALISATION
#######################################################################
$cgiFolder = "/~tngu211/students/";
$dataFolder = getcwd."/students/";
$defaultProfileFilename = "profile.txt";
$defaultPreferenceFilename = "preferences.txt";
$currProfile = "";
$homeUrl = "/~tngu211/love2041.cgi";
#$userListURL = "/~tngu211/love2041.cgi?|allusers";
#$authenticated = 0;
$timeToLive = 600; #seconds
%globalSessionData = ();
$profPerPage = 3;
$WORST_SCORE = 10000;
%matchScores = ();


#create a hash of private fields
#these wont show on public profile pages
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
$privateFields{"personal_text"} = 1;
$privateFields{"extraImge"} = 1;
#hash of predefined 'preference variables'
#any info fields outside of this list will be matched according
#to occurance between the two users.
%specialMatchingFields = ();
$specialMatchingFields{"gender"} = 1;
$specialMatchingFields{"weight"} = 1;
$specialMatchingFields{"height"} = 1;
$specialMatchingFields{"birthdate"} = 1;
$specialMatchingFields{"hair_colour"} = 1;
$specialMatchingFields{"otherPhotos"} = 1;
$maxWeight = 5;



#######################################################################
#		MAIN EXECUTION STATE MACHINE
#######################################################################

#statemachine based on session
#check session checks REMOTE_ADDR.acc file on server directory
#if session is not currently authenticated, redirect user to login screen
#if session is authenticated, then allow for more complex use of site


if ($ENV{'QUERY_STRING'} eq "lostPass")
{
	#password recovery query
	generatePasswordRecoveryHTML();
}
elsif (checkSession() != 0)
{
	#session is not authenticated
	#prompt for login details and try to authenticate
	if(defined(param ("uname")) && defined(param("pass")) )
	{
		#if params defined, user has attempted to log in
		my $uname = param("uname");
		my $pass = param("pass");
		
		$globalSessionData{"authenticated"} = authenticate();
		#$auth = authenticate();
		#debugPrint("trying to login $uname $pass $auth");
		if($globalSessionData{"authenticated"} ==0)
		{
			#successful login. update session file
			$globalSessionData{"current_user"} = param("uname");
			updateSession();;
			#let them into the rest of the site
			generateNUserList($profPerPage, 0);
		}
		else
		{
			#debugPrint("nggers cant log");
			#unsuccessful. go back to login page
			generateLoginPage("failed_login");	
		}
	}
	elsif($ENV{'QUERY_STRING'} eq "|newUser")
	{
		#first, new profile generation
		#beginPage();
		#printAllParams();
		if(defined param('new_preferences'))
		{
			#create new prefernce file and show the user their page
			createNewPreferences(param('new_username'));
			generateUserHtml(param('new_username'));

		}
		elsif (defined param('new_profile'))
		{
			#create new profile file and get the uesr to enter prefernces
			createNewProfile(param('new_username'));
			generateNewUserPreferencesHTML();
		}
		else
		{
			generateNewUserProfileHTML();
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
elsif($ENV{'QUERY_STRING'} eq "myMatches")
{
	#user hsa requested for their matches to be shown
	my $currUser = $globalSessionData{"current_user"};
	generateNMatches($currUser, 5);
}
elsif($ENV{"QUERY_STRING"} =~ /\%7CuserQuery\=(.+)/)
{
	#search result requested. process search string and go
	#note that for some reason the bar character '|' comes up as '%7C' because html is retard
	$userSearchQuery = $1;
	generateSearchResultsHTML($userSearchQuery);

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
		generateLoginPage();
	}
	elsif($query eq "matchtest")
	{
		my $matchscore = matchUsers("AwesomeGenius60", "SadDude80");
		debugPrint("$matchscore between AwesomeGenius60 and SadDude80");
	}
	elsif($query =~ /userlist(\d+)/)
	{
		my $nthPage = $1;
		generateNUserList($profPerPage, $nthPage);
	}
	elsif($query eq "preferenceTest")
	{
		param('new_username', "ovenfoot");
		generateNewUserPreferencesHTML();
		
	}
	elsif($query eq "editProfile")
	{
		if (defined param('new_profile'))
		{
			createNewProfile(param('username'));
			#beginPage();
			#printAllParams();
			generateUserHtml(param('username'));
			
		}
		else
		{
			generateEditProfileHTML($globalSessionData{'current_user'});
		}
		#debugPrint("Whassup");
	}
	elsif($query eq "editPrefrences")
	{
		if (defined param('new_preferences'))
		{
			createNewPreferences(param('username'));
			generateUserHtml(param('username'));
		}
		else
		{
			generateEditPreferencesHTML($globalSessionData{'current_user'});
		}
	}
	elsif($query eq "newUser")
	{
		#navigating to newuser whilst logged in will logout hte current person
		$globalSessionData{'current_user'} = "";
		$globalSession{'authenticated'} = -1;
		updateSession();
		generateNewUserProfileHTML();

	}
	elsif($query =~ /message\=(.+)/)
	{
		#send a message to a user
		#if 'send_message' is defined it means there is data to send
		if (defined param('send_message'))
		{	
			sendMail (param('from_user'), param('to_user'), param('message_body'));
		}
		#otherwise generate a new message html
		else
		{
			generateSendMessageHTML($1);
		}
	}
	else
	{
		debugPrint("THIS IS THE MOST BORING 404 PAGE EVER");
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
#		HTML UTILITY FUNCTIONS
#		Shortcuts and utilties for doing web stuff
#######################################################################


#take in username and password to check against database
#return 0 for success, <0 for fail
sub authenticate
{
	my $uname = param('uname');
	my $password = param('pass');

	my %udata = generateUserData($uname);
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
	my ($flag) = @_;
	print header;
	print start_html(-title=>'love doge go');

	print param("unameSearch");

	print "<link rel='stylesheet' type='text/css' href='style.css'>\n";

	
	#print p $ENV{"REMOTE_ADDR"};
	print '<div id = "header">';
	
	if ($globalSessionData{"authenticated"} == 0 && !defined $flag)
	{
		
		print "<center>";
		print h1 "Welcome to the den of the love doge";
		print h2 "We hope you enjoy your stay";
		print "</center>";
		print "<table width = 750 padding-top = 20> <tr>\n";
		
		print "<td><center>";
		print a;
		printLink($homeUrl, "Go home");
		print "</center> </td> \n";
		
		#link to go to your profile
		print "<td>"; 
		printLink ($homeUrl."?".$globalSessionData{"current_user"}, "My Profile");
		print "</td>";

		
		#logout
		print "<td>";
		printLink($homeUrl."?|logout", "Log Out");
		print "</td>\n";
		
		print '<td align = "right">';
		printSearchForm();
		print "</td>\n";
		print "</tr></table>\n";
	}
	
	print "</div>";
	#print p $ENV{"SERVER_PORT"};

}

#prints all end html tags and generic hidden variables
sub endPage
{
	my ($errorFlag)= @_;
	print "<br>  </br>";


	print '<div id = "footer">';

	if (!defined $globalSessionData{"current_user"})
	{
		$globalSessionData{"authenticated"} = -1;
	}

	#if we're in an authenticated session then print logout details
	if ($globalSessionData{"authenticated"} == 0 && !defined $errorFlag)
	{
		
		
		#back to last browse button
		if (!defined $globalSessionData{"last_profile_browse"})
		{
			$globalSessionData{"last_profile_browse"} = 0;
		}
		$lastURL = $homeUrl."?|userlist".$globalSessionData{"last_profile_browse"};
		
		print "<center>\n";
		print "<table>\n";
		print "<tr><td>";
		print a;
		printLink($lastURL, "Back to User List");
		print "</td>";
		
		#redundant home button 
		print "<td><center>";
		print a;
		printLink($homeUrl, "Go home");
		print "</center> </td> \n";
		
		#logout
		print "<td>";
		printLink($homeUrl."?|logout", "Log Out");
		print "</td> </tr>\n";
		
		
		#link to go to your profile
		print "<tr><td> </td> <td> You are currently logged in as "; 
		printLink ($homeUrl."?".$globalSessionData{"current_user"}, $globalSessionData{"current_user"});
		print "</td>  <td> </td>  </tr>\n";

		print "</table>\n";
		print "</center>\n";
		updateSession();
	}

	print '<!-- Designed by DreamTemplate. Please leave link unmodified. -->
		<br><center><a href="http://www.dreamtemplate.com" 
			title="Website Templates" target="_blank">
			Website templates</a></center>';

	
	print '</div>';
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
}
##
#prints debug string to html
sub debugPrint
{
	my (@debugStrings) = @_;
	print header;
	print start_html(-title=>'LOVE2041 MOTHERS',
								-bgcolor=>'CCFF33');

	foreach $debugString (@debugStrings)
	{
		print p $debugString;
	}
	print end_html;

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

	#update last access and timeout values
	$globalSessionData{"last_access"} = localtime();
	$globalSessionData{"timeout"} = time()+$timeToLive;

	open (sFile, "> $sessionFile");
	foreach my $key (keys %globalSessionData)
	{
		if($key =~ /[\w\d]+/)
		{
			print sFile "$key,$globalSessionData{$key}\n";
		}
	}
	close sFile;
}

#load session data into memory
#if authenticated and checks out, return 0
#If no session data found, return error and force person to sign in
#also checks and deletes obsolete session files
sub checkSession
{

	my $ip = $ENV{"REMOTE_ADDR"};
	$ip =~ s/\./\_/g;
	my $sessionFile = "$ip.acc";
	my %otherSession = ();

	#first, scrub all previous sessions
	#search through all access files
	#delete anything with a timeout value less than current time
	opendir my $DIR, './';
	my @otherAccesses = grep{/.*.acc/} readdir $DIR;
	closedir $DIR;
	
	foreach my $access (@otherAccesses)
	{
		open (otherFile, "< $access");

		foreach my $line (<otherFile>)
		{
			chomp $line;
			@data = split(/\,/, $line);
			if (defined $data[0] && defined $data[1])
			{
				$otherSession{$data[0]} = $data[1];
			}
		}
		
		close (otherFile);

		if ($otherSession{"timeout"} < time())
		{
			unlink $access
		}
	}


	#now scan the session file relevant to this session
	if (!(-R $sessionFile))
	{
		#session does not exist
		return -1;
	}

	open (sFile, "< $sessionFile");

	foreach my $line (<sFile>)
	{
		chomp $line;
		@data = split(/\,/, $line);
		$globalSessionData{$data[0]} = $data[1];
	}

	close sFile;

	#check for timeout
	if ($globalSessionData{"timeout"} < time())
	{
		#timeout value exceeded
		return -1;
	}
	
	if (!defined $globalSessionData{"current_user"})
	{
		$globalSessionData{"authenticated"} = -1;
	}
	return $globalSessionData{"authenticated"};
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
	print "</a>";
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
		$scale = "100%";
	}

	print "<a ";
	print 'href="';
	print $addr;
	print '" ';
	print ">";
	print "<img src=$imagePath width = $scale height = $scale>\n";
	print "</a>\n";

}

#helper function to print the user search form 
sub printSearchForm
{

    print '<form action="',
    "$homeUrl",'?search' ,
    '">
    <label>Search for user <input name="|userQuery"></label>
    <input type="submit" value = "Search">
	</form>'	
}

#print new login form
sub printNewLogin
{
	my ($errorMessage) = @_;
	beginPage("nosearch");
	print h1 "Welcome, new person!";
	print h2 "Enter a username a password!";
	if(defined $errorMessage)
	{
		print "\n",'<p style = "color:#FF0000">',
		$errorMessage, 
		'</p>', "\n";
	}
	

	print start_form;
    print 'Enter login: ', p textfield('new_username'), p "<br>\n";
    print 'Password: ', p password_field('new_password'),p "<br>\n";
    print 'Email: ', p textfield('email'), p "<br>\n";
    print submit('submit');
    print end_form;
	
	print h2;
	printLink($homeUrl, "Back to login");
	print "</h2>";
    endPage("noauth");
}

#print all parameters on the page currently
sub printAllParams
{
	foreach my $key (param())
	{
		print p ("param key: $key \n");
		my $val = param($key);
		print p ("value: $val");
	}
}
#######################################################################
#		HTML SUBPAGE GENERATORS
#######################################################################

#page to allow users to send messages to each other via email
sub generateSendMessageHTML
{
	my($toUser) = @_;
	my $fromUser = $globalSessionData{'current_user'};
	
	beginPage();
	print h1 "Send a message to $toUser";
	
	print start_form;
	print td (textarea(-name=>'message_body', 
						-rows=>"10",
						-cols=>"50",
						-value=>"HOLY CRAP I'M SO IN LOVE WITH YOU"));
	
	
	param("from_user", $fromUser);
	param("to_user", $toUser);
	
	print hidden("from_user");
	print hidden("to_user");
	
	print p submit (-value=>"Send Message!", -name=>"send_message");
	
	print end_form;
	
	endPage();
}

#send mail. First argument is from, second argument is to, 3rd arg is message
sub sendMail
{
	my ($fromUser, $toUser, $message) = @_;
	my %udata = generateUserData($toUser, "profile");
	beginPage("nosearch");
	if (defined $udata{"email"})
	{
		#test
		my $to = $udata{"email"};
		my $from = 'tngu211@cse.unsw.edu.au';
		my $subject = "Love doge message delivery from $fromUser";
		my $message = "$fromUser wants to send a message to you:\n\n".$message.
				"\n\nMaybe you should send them a message back!";
		
		open(MAIL, "|/usr/sbin/sendmail -t");
		 
		# Email Header
		print MAIL "To: $to\n";
		print MAIL "From: $from\n";
		print MAIL "Subject: $subject\n\n";
		# Email Body
		print MAIL $message;
		
		print p "Message Sent!"
	}
	else
	{
		print p "$toUser doesn't have an email address, sorry :(";
	}
	
	print h2;
	printLink($homeUrl."?".$toUser, "Back to $toUser\'s profile");
	print "</h2>";
	endPage();

	
}

#password recovery page. Finds the password and sends it in plaintext via email
sub generatePasswordRecoveryHTML
{
		
	if(defined param('lostUname'))
	{
		my %udata = generateUserData(param('lostUname'), "profile");
		beginPage("nosearch");
		if (defined $udata{"email"})
		{
			#email parameters
			my $to = $udata{"email"};
			my $from = 'tngu211@cse.unsw.edu.au';
			my $subject = 'Love Doge Password Reset';
			my $message = "Password Reset requested. your password is ".$udata{"password"};
			 
			open(MAIL, "|/usr/sbin/sendmail -t");
			 
			#mail data to send
			print MAIL "To: $to\n";
			print MAIL "From: $from\n";
			print MAIL "Subject: $subject\n\n";
			print MAIL $message;

			close(MAIL);

			print h3 "Recovery Email Sent to $to\n";
			
			print h2;
			printLink($homeUrl, "Go back to login");
			print "</h2\n>";

		}
		else
		{
			print p "No username or email found!";
			print h2;
			printLink($homeUrl, "Go back to login");
			print "</h2\n>";

		}
		endPage();
	}
	else
	{
		beginPage('nosearch');
		print start_form;
		print h1 "Password Recovery";
		print p "Forgot your password? Doge worry. Type in your username and we'll send you your password in an email";
		print p "Login:", textfield('lostUname');
		#print h3 "Email:", textfield('lostEmail');
		
		print submit(-name=>'recover',
								-value=>'Recover me!');
								
		print end_form;
		
		print h2;
		printLink($homeUrl, "Go back to login");
		print "</h2\n>";

		
		endPage();
	}
}

#edit preferences
#takes in username as first argument
#same as create new preferences.txt
sub generateEditPreferencesHTML
{
	my ($username) = @_;
	my %u1Pref = generateUserData($username, 'preferences');
	my $age_min = "";
	my $age_max = "";
	my $height_max = "";
	my $height_min = "";
	my $weight_max = "";
	my $weight_min = "";
	
	my $hair_colours = join("\n", split (/\|/,$u1Pref{'hair_colours'}));	
	beginPage();
	
	#get ranges
	if ($u1Pref{"age"} =~ 
		/min\:\|\s*([\w\d\.]+)\|\s*max\:\s*\|\s*([\w\d\.]+)/)
	{
		$age_min = $1;
		$age_max = $2;
		
	}

	if ($u1Pref{"weight"} =~ 
		/min\:\|\s*([\d]+)kg\|\s*max\:\s*\|\s*([\d]+)kg/)
	{
		$weight_min = $1;
		$weight_max = $2;	
	}
	
	if ($u1Pref{"height"} =~ 
		/min\:\|\s*([\d\.]+)m\|\s*max\:\s*\|\s*([\d\.]+)m/)
	{
		$height_min = $1;
		$height_max = $2;	
	}


	print h1 "Who are your looking for?";
	
	#gigantic form...
	print start_form;
	
	print "<table>\n";

	print "<tr>";
	print td 'Age:';
	print td p "min", (textfield(-name=>'age_min',
						-value=>"$age_min")),
		p "max", textfield(-name=>'age_max',
						-value=>"$age_max");
	print "</tr>\n";
	
	print "<tr>";
	print td 'Height:';
	print td p "min", (textfield(-name=>'height_min',
						-value=>"$height_min")), "m",
		p "max", textfield(-name=>'height_max',
						-value=>"$height_max"), "m";
	print "</tr>\n";
	
	print "<tr>";
	print td 'Weight:';
	print td p "min", (textfield(-name=>'weight_min',
						-value=>"$weight_min")), "kg",
		p "max", textfield(-name=>'weight_max',
						-value=>"$weight_max"), "kg";
	print "</tr>\n";

	
	print "<tr>";
	print "<td valign = 'top'>", 'Hair Colours:';
	print "</td>";
	print td (textarea(-name=>'hair_colours', 
						-rows=>"10",
						-cols=>"25",
						-value=>$hair_colours));
	print "</tr>\n";
	
	print "<tr>";
	print td "Gender";
	print '<td> <select name = "gender">', "\n";
	print option("$u1Pref{'gender'}");
	print option ("");
	print option ("Male");
	print option ("Female");
	print option ("Other");
	print "</select> </td>";
	
	#pass through all the required variables
	param('username', $username);
	print hidden('username');
		
	print "<tr> <td></td> <td>";
	print center submit(-name=>'new_preferences',
						-value=>'Submit');
	print "</td> </tr>\n";
	print "</table>\n";

	print end_form;
	
	endPage();
	
}

#edit profile.
#takes in username as first argument
#essentially the same as create profile except that
#the fields come pre-filled
sub generateEditProfileHTML
{
	my ($username) = @_;
	my %udata = generateUserData($username);
	my $birthdayString = "";
	#parse the data and make sure that the | delimeter is replaced by \n
	foreach my $key (keys %udata)
	{
		$udata{$key} = join("\n", split (/\|/, $udata{$key}));
	}
	
	beginPage();
	print h1 "Hello, $username!";
	print h2 "Tell us a bit about yourself!";
	print h3 "(Feel free to leave out the more private details!)";

	print start_form;
	
	print p "Sum yourself up in a few words";
	print p (textarea(-name=>'personal_text', 
						-rows=>"10",
						-cols=>"50"
						-value=>$udata{'personal_text'}));
	
	
	print "<table style = table-layout:fixed>\n";	
	
	################ BASIC INFO ###################
	print "<tr> <td>", h2 "Basic Info", "</td></tr>";

	print "<tr>";
	print td 'Profle Picture:';
	print td filefield(-name => "profileImage");
	print "</tr>\n";

	print "<tr>";
	print td 'Name:';
	print td (textfield(-name=>'name',
			-value=>$udata{'name'}));
	print "</tr>\n";

	print "<tr>";
	print td 'Height:';
	print td ((textfield(-name=>'height', 
		-value=>$udata{'height'})), "m");
	print "</tr>\n";

	print "<tr>";
	print td 'Hair colour:';
	print td (textfield(-name=>'hair_colour',
		-value=>$udata{'hair_colour'}));
	print "</tr>\n";

	print "<tr>";
	print td 'Weight:';
	print td ((textfield(-name=>'weight',
		-value=>$udata{'weight'})), "kg");
	print "</tr>\n";

	print "<tr>";
	print td "Gender";
	print '<td> <select name = "gender", value = Male>', "\n";
	print option ("$udata{'gender'}");
	print option ("");
	print option ("male");
	print option ("female");
	print option ("other");
	print "</select> </td>";

	print "</tr>\n";

	
	#parse the birthday for default value to be set
	if ($udata{'birthdate'} =~ /(\d\d\d\d)\/(\d\d)\/(\d\d)/)
	{
		$birthdayString = $1."-".$2."-".$3;
	}
	elsif ($udata{'birthdate'} =~ /(\d\d)\/(\d\d)\/(\d\d\d\d)/)
	{
		$birthdayString = $3."-".$2."-".$1;
	}
	
	print "<tr>";
	print td 'Birthday:';
	print td "<input type=\"date\" name = \"birthdate\" value = \"$birthdayString\">";
	print "</tr>\n";
	
	print "<tr>";
	print td 'Extra Image:';
	print td filefield(-name => "extraImage");
	print "</tr>\n";
	

	########### STUDY DEETS ####################
	print "<tr> <td>", h2 "Study details", "</td></tr>";
	print "<tr>";
	print td 'Degree: ';
	print td (textfield(-name=>'degree',
		-value=>$udata{'degree'}));
	print "</tr>\n";

	print "<tr>";
	print "<td valign = 'top'>", 'Courses';
	print "</td>";
	print td (textarea(-name=>'courses', 
						-rows=>"10",
						-cols=>"25",
						-value=>$udata{'courses'}));
	print "</tr>\n";

	################INTERESTS AND HOBBIES #################

	print "<tr> <td>", h2 "Interests and hobbies", "</td></tr>";

	print "<tr>";
	print "<td valign = 'top'>", 'Favourite Hobbies:';
	print "</td>";
	print td (textarea(-name=>'favourite_hobbies', 
						-rows=>"10",
						-cols=>"25",
						-value=>$udata{'favourite_hobbies'}));
	print "</tr>\n";

	print "<tr>";
	print "<td valign = 'top'>", 'Favourite Books:';
	print "</td>";
	print td (textarea(-name=>'favourite_books', 
						-rows=>"10",
						-cols=>"25",
						-value=>$udata{'favourite_books'}));
	print "</tr>\n";


	print "<tr>";
	print "<td valign = 'top'>", 'Favourite TV Shows:';
	print "</td>";
	print td (textarea(-name=>'favourite_TV_shows', 
						-rows=>"10",
						-cols=>"25",
						-value=>$udata{'favourite_TV_shows'}));
	print "</tr>\n";


	print "<tr>";
	print "<td valign = 'top'>", 'Favourite Movies:';
	print "</td>";
	print td (textarea(-name=>'favourite_movies', 
						-rows=>"10",
						-cols=>"25",
						-value=>$udata{'favourite_movies'}));
	print "</tr>\n";

	print "<tr>";
	print "<td valign = 'top'>", 'Favourite Bands:';
	print "</td>";
	print td (textarea(-name=>'favourite_bands', 
						-rows=>"10",
						-cols=>"25",
						-value=>$udata{'favourite_bands'}));
	print "</tr>\n";

	
	param('username', $username);
	param('new_password', $udata{'password'});
	param('email', $email);
	print hidden('new_password');
	print hidden('email');
	print hidden('username');
	print hidden('email');
	#print hidden('new_profile');


	print "<tr> <td></td> <td>";
	print center submit(-name=>'new_profile',
						-value=>'Submit');
	print "</td> </tr>\n";
	print "</table>\n";

	print end_form;
	
}

#new user creation page
sub generateNewUserProfileHTML
{
	
	#debugPrint("Wassup negro?");
	my $username = "";
	my $password = "";
	my $email = "";
	my @allUsers = ();

	
	if (!defined param('new_username'))
	{
		#on first pass, new login page to specify uname, email and pass
		printNewLogin();
	}
	else
	{

		$username = param('new_username');
		$password = param('new_password');
		$email = param('email');

		#check if username exists
		if( grep ( /^$username$/, getUserList()))
		{

			printNewLogin("username already exists!");
			return;
		}

		#check that password field is non-empty
		if($password eq "")
		{
			printNewLogin("password can't be empty!");
			return;
		}

		#check for a valid email address
		if (!($email =~ /.+\@.+\..+/ ))
		{
			printNewLogin("Invalid Email!");
			return;
		}
		
		#check for no spaces in username
		if ($username =~ /\s+/)
		{
			printNewLogin("Usernames must be alphanumeric with no white spaces");
			return;
		}
		beginPage("nosearch");

		print h1 "Hello, $username!";
		print h2 "Tell us a bit about yourself!";
		print h3 "(Feel free to leave out the more private details!)";
		#print p param('height');

		print start_form;
		
		
		print p "Sum yourself up in a few words";
		print p (textarea(-name=>'personal_text', 
							-rows=>"10",
							-cols=>"50"));
		
		
		print "<table style = table-layout:fixed>\n";
		
		
		
		
		################ BASIC INFO ###################
		print "<tr> <td>", h2 "Basic Info", "</td></tr>";

		print "<tr>";
		print td 'Profle Picture:';
		print td filefield(-name => "profileImage");
		print "</tr>\n";

		print "<tr>";
		print td 'Name:';
		print td (textfield('name'));
		print "</tr>\n";

		print "<tr>";
		print td 'Height:';
		print td ((textfield('height')), "m");
		print "</tr>\n";

		print "<tr>";
		print td 'Hair colour:';
		print td (textfield('hair_color'));
		print "</tr>\n";

		print "<tr>";
		print td 'Weight:';
		print td ((textfield('weight')), "kg");
		print "</tr>\n";

		print "<tr>";
		print td "Gender";
		print '<td> <select name = "gender">', "\n";
		print option ("");
		print option ("Male");
		print option ("Female");
		print option ("Other");
		print "</select> </td>";

		print "</tr>\n";

		print "<tr>";
		print td 'Birthday:';
		print td '<input type="date" name = "birthdate">';
		print "</tr>\n";
		
		print "<tr>";
		print td 'Extra Image (you can upload more later):';
		print td filefield(-name => "extraImage");
		print "</tr>\n";


		########### STUDY DEETS ####################
		print "<tr> <td>", h2 "Study details", "</td></tr>";
		print "<tr>";
		print td 'Degree: ';
		print td (textfield('degree'));
		print "</tr>\n";

		print "<tr>";
		print "<td valign = 'top'>", 'Courses';
		print "</td>";
		print td (textarea(-name=>'courses', 
							-rows=>"10",
							-cols=>"25"));
		print "</tr>\n";

		################INTERESTS AND HOBBIES #################

		print "<tr> <td>", h2 "Interests and hobbies", "</td></tr>";

		print "<tr>";
		print "<td valign = 'top'>", 'Favourite Hobbies:';
		print "</td>";
		print td (textarea(-name=>'favourite_hobbies', 
							-rows=>"10",
							-cols=>"25"));
		print "</tr>\n";

		print "<tr>";
		print "<td valign = 'top'>", 'Favourite Books:';
		print "</td>";
		print td (textarea(-name=>'favourite_books', 
							-rows=>"10",
							-cols=>"25"));
		print "</tr>\n";


		print "<tr>";
		print "<td valign = 'top'>", 'Favourite TV Shows:';
		print "</td>";
		print td (textarea(-name=>'favourite_TV_shows', 
							-rows=>"10",
							-cols=>"25"));
		print "</tr>\n";


		print "<tr>";
		print "<td valign = 'top'>", 'Favourite Movies:';
		print "</td>";
		print td (textarea(-name=>'favourite_movies', 
							-rows=>"10",
							-cols=>"25"));
		print "</tr>\n";

		print "<tr>";
		print "<td valign = 'top'>", 'Favourite Bands:';
		print "</td>";
		print td (textarea(-name=>'favourite_bands', 
							-rows=>"10",
							-cols=>"25"));
		print "</tr>\n";

		
		param('new_username', $username);
		param('new_password', $password);
		param('email', $email);
		param('new_profile', 1);
		print hidden('new_password');
		print hidden('email');
		print hidden('new_username');
		print hidden('email');

		print "<tr> <td></td> <td>";
		print center submit(-name=>'new_profile',
							-value=>'Submit');
		print "</td> </tr>\n";
		print "</table>\n";

		print end_form;

		#state change flag 
		print hidden('new_profile');
		


		endPage();
	}
}

#new user preference creation page
#big form for users to specify their dating preferences
sub generateNewUserPreferencesHTML
{
	
	#debugPrint("Wassup negro?");
	my $username = "";
	my $password = "";
	my $email = "";
	my @allUsers = ();

	$username = param('new_username');
	
	beginPage("nosearch");

	print h1 "And now, who are your looking for?";
	
	#gigantic form...
	print start_form;
	
	print "<table>\n";

	print "<tr>";
	print td 'Age:';
	print td p "min", (textfield('age_min')),
		p "max", textfield('age_max');
	print "</tr>\n";
	
	print "<tr>";
	print td 'Height:';
	print td p "min", (textfield('height_min')), "m",
		p "max", textfield('height_max'), "m";
	print "</tr>\n";
	
	print "<tr>";
	print td 'Weight:';
	print td p "min", (textfield('weight_min')), "kg",
		p "max", textfield('weight_max'), "kg";
	print "</tr>\n";

	
	print "<tr>";
	print "<td valign = 'top'>", 'Hair Colours:';
	print "</td>";
	print td (textarea(-name=>'hair_colours', 
						-rows=>"10",
						-cols=>"25"));
	print "</tr>\n";
	
	print "<tr>";
	print td "Gender";
	print '<td> <select name = "gender">', "\n";
	print option ("");
	print option ("Male");
	print option ("Female");
	print option ("Other");
	print "</select> </td>";
	
	#pass through all the required variables
	print hidden('new_username');
		
	print "<tr> <td></td> <td>";
	print center submit(-name=>'new_preferences',
						-value=>'Submit');
	print "</td> </tr>\n";
	print "</table>\n";

	print end_form;
	
	endPage();
}



#login page. Generate everything necessary
sub generateLoginPage
{

	my ($errFlag) = @_;
	#create a new session page for login
	createNewSession();

	beginPage();
	print h1 "Hello. I am the love doge. Enter at your own risk";

	printImageLink($homeUrl, "/~tngu211/doge_sticker.jpg", "50%");
	#login form
	if (defined $errFlag)
	{
		print "\n",'<p style = "color:#FF0000"> Wrong password or username! </p>', "\n";
	}
	print start_form,
        'Enter login: ', p textfield(-name=>'uname'), p "<br>\n",
        ' Enter password: ', p password_field('pass'),p "<br>\n",
        submit('Login'),
        end_form;
		
	#account creation and lost password links
    print h2;
    printLink("$homeUrl?|newUser", "Don't have an account? Create one here!");
    print "</h2>\n";
	
	print h3;
	printLink("$homeUrl?lostPass", "Lost your password?");
	print "</h3>\n";
	
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

		my %udata = generateUserData($users[$index]);

		print '<td>';
		printImageLink($userURL, $udata{"profileImage"}, "175");
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

	print h2;
	printLink($homeUrl."?myMatches", "Find my matches!");
	print "</h2>";

	endPage();

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

	beginPage();
	warningsToBrowser(1);
	%udata = generateUserData($uname);
	if (! $udata{"found"})
	{
		print h1 "404. HOW DID YOU GET HERE?\n";
		
		endPage();
		return (-1);
	}


	print h1 "$uname";

	#if the user is the current user, let them edit profile
	if ($globalSessionData{'current_user'} eq $uname)
	{
		print h2;
		printLink($homeUrl."?|editProfile", "Edit Profile");
		print "</h2>";
		
		print h2;
		printLink($homeUrl."?|editPrefrences", "Edit Preferences");
		print "</h2>";
	}
	else
	{
		#message the user
		print h2;
		printLink($homeUrl."?|message=$uname", "Message This Person!");
		print "</h2>";
	}
	
	#print profile picture from path stored in hash
	if (defined $udata{"profileImage"})
	{	
		$imagePath = $udata{"profileImage"};
		print p "<img src=$imagePath width = 250><p>\n";	
	}
	
	#print personal text
	if(defined $udata{"personal_text"})
	{
		print p $udata{"personal_text"};
	}
	
	print '<table class = "fixed"> <col width = "300"> <col width = "300">';
	print '<td valign = top >';
	#go through each data field and print values
	#check if field is private
	print h1 "Personal Details";
	
	
	foreach my $field (sort keys %udata)
	{
		if(!exists ($privateFields{$field}))
		{
			#check if the field is not private, print it
			$fieldToPrint = prettyInput ($field);
			print h2 "$fieldToPrint";
			@currData = split ('\|',$udata{$field});
			foreach my $entry (@currData)
			{
				print ul "$entry";
			}
		}
	}

	
	#grab the preference data and repeat
	%udata = generateUserData($uname, "preferences");
	if ($udata{"found"})
	{
		print "</td>\n";
		print "<td valign = top>";
		print h1 "They are looking for ...";
		#go through each data field and print values
		#check if field is private
		foreach my $field (sort keys %udata)
		{
			
			if(!exists ($privateFields{$field}))
			{
				#check if the field is not private, print it
				$fieldToPrint = prettyInput ($field);
				print h3 "$fieldToPrint";
				#analyse for min/max values
				if ($udata{$field} =~ /min\:\|\s*([\w\d\.]+)\|\s*max\:\s*\|\s*([\w\d\.]+)/)#\s*([\w\d\.]+)/)
				{
					print p "$1 - $2";
				}
				else
				{
					@currData = split ('\|',$udata{$field});
					foreach my $entry (@currData)
					{
						print p "$entry";
					}
				}
			}

		}
		print "</td>\n";
	}
	print '</table>';
	#extract photo file names and embed them in the page
	if($udata{"otherPhotos"} ne "")
	{
		print '<div id = "images_hz">';
		print h2 "Other Photos";
	
		@otherPhotos = split(/\|/, $udata{"otherPhotos"});
		foreach my $photo (@otherPhotos)
		{	
			$imagePath = $udata{"path"}.$photo;
			print "<img src=$imagePath width = 250 alt = ", '""', " >\n";
		}
		print p;
		print '</div>';
	}
	endPage();

}

#generate page of search results
#first argument is search string
sub generateSearchResultsHTML
{
	my ($searchString) = @_;
	#search for users and return matched string list
	my @matchedUsers = searchForUsers($searchString);

	beginPage();
	print h1 "Search Results";

	#error out if nothing was found
	if ($#matchedUsers < 0)
	{
		print p "Sorry, could not find a match for  \"$searchString\"";
	}
	else
	{
		print p "You searched for \"$searchString\"";

		#print each of the results with the display pic as an unordered list
		foreach my $matchedUser (@matchedUsers)
		{
			my $userURL = $homeUrl."?$matchedUser";
			my %udata = generateUserData($matchedUser);
			#print ul;
			print ul;
			printImageLink($userURL, $udata{"profileImage"}, "150");
			print ul;
			printLink($userURL, $matchedUser);
			print "\n";
		}
	}	
	endPage();

}

# Generates a page displaying N matches 
# first argument is user name to match
# second argument is the number of matches
sub generateNMatches
{
	my ($userIn, $numMatches) = @_;
	my @allUsers = getUserList();
	my %localMatches = ();
	my @sortedMatches = ();

	chomp $userIn;

	beginPage();
	foreach my $user (@allUsers)
	{
		chomp $user;
		if(!($user eq $userIn) )
		{

			#print p "processing $user and $userIn";
			$matchScores{$userIn}{$user} = matchUsers($userIn,$user);
			$matchScores{$user}{$userIn} = $matchScores{$userIn}{$user};

		}
	}

	print h1 "Your best love matches!";

	%localMatches = %{$matchScores{$userIn}};
	print "<ol>\n";
	foreach my $user (sort { $matchScores{$userIn}{$a} <=> $matchScores{$userIn}{$b} } keys %{$matchScores{$userIn}})
	{
		push @sortedMatches, $user;
	}

	for (my $i=0; $i<$numMatches; $i++)
	{
		my $userURL = $homeUrl."?$sortedMatches[$i]";
		my %udata = generateUserData($sortedMatches[$i]);
		print "<li>";
		printImageLink($userURL, $udata{"profileImage"}, "100");
		print p;
		printLink($userURL, "$sortedMatches[$i]");
		
		print "</li>\n"
	}
	print "</ol>\n";
	endPage();
}

#######################################################################
#		USER DATABASE FUNCTIONS
#######################################################################

#scans the /students/ folder and extracts out all the users
sub getUserList
{
	opendir ((my $userdirs), $dataFolder);
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


#create user profile based on submitted parameters
sub createNewProfile
{
	my ($username) = @_;
	my $ufolder = $dataFolder.$username;
	my $uprofileFile = $ufolder."/".$defaultProfileFilename;
	mkdir $ufolder;

	
	#sanity check height and weight
	if(!(param ('height') =~ /[\d\.]+(m)*/))
	{
		param('height', "");
	}
	
	if(!(param ('weight') =~ /[\d\.]+(kg)*/))
	{
		param('weight', "");
	}
	chmod 0755, $ufolder;
	open NEWUSERPROFILE, "> $uprofileFile" or die ("NO USER");
	
	foreach my $field (param())
	{
		
		if(param($field) ne "" && $field ne "new_profile")
		{
			#field is nonempty.
			#store it in the standard format

			my $fieldToStore = $field;
			$fieldToStore =~ s/new\_//g;
			print NEWUSERPROFILE "$fieldToStore:\n";
			my @values = split(/\n/, param($field));
			foreach my $value (@values)
			{
				#check if field requires kg or m at the end
				if($field eq "height")
				{
					$value =~ s/m//g;

					$value .="m";
				}
				elsif ($field eq "weight")
				{
					$value =~ s/kg//g;
					$value =~ s/\D//g;
					$value .="kg";
				}
				elsif ($field eq "gender")
				{
					$value = lc$value;
				}
				elsif($field eq "birthdate")
				{
					$value =~ s/\-/\//g;
				}
				elsif ($field eq "profileImage")
				{

					#debugPrint("tried to upload an image $value");
					$filename = param ("profileImage");
					my $profileImageFile = $ufolder."/profile.jpg";
					my $profileImageHandle = upload("profileImage");
					open PROFILEIMAGE, "> $profileImageFile";
					#binmode PROFILEIMAGE;
					while($bytesread = read($filename, $buffer, 1024))
					{
						print PROFILEIMAGE $buffer;
						$bytesread = 0;
					}
					close PROFILEIMAGE;
				}
				elsif ($field eq "extraImage")
				{
					#debugPrint("uploading Another Image");
					$filename = param ("extraImage");
					#first count the number of photos, and append to the end;
					opendir ((my $udir), $ufolder);
					my @otherPhotos = grep{/photo\d*\.jpg/} readdir $udir;
					closedir $udir;
		
					#new filename is photo file + 1;
					my $otherImageFile = $ufolder."/photo".($#otherPhotos+1).".jpg";
					#debugPrint("trying to write to $otherImageFile");
					my $profileImageHandle = upload("otherImageFile");
					open OTHERIMAGE, "> $otherImageFile";
					#binmode PROFILEIMAGE;
					while($bytesread = read($filename, $buffer, 1024))
					{
						print OTHERIMAGE $buffer;
						$bytesread = 0;
					}
					close OTHERIMAGE;
				}
				print NEWUSERPROFILE "\t$value\n";
			}
		}
	}
	
	

	close NEWUSERPROFILE;
	chmod 0755, $uprofileFile;
}


#create a new preference file
sub createNewPreferences
{
	my ($username) = @_;
	my $ufolder = $dataFolder.$username;
	my $upreferenceFile = $ufolder."/".$defaultPreferenceFilename;
	my @lines = ();
	open NEWUSERPREFERENCES, "> $upreferenceFile" or die ("CANNOT OPEN USER PREFERENCE FILE");

	
	if (param ('hair_colours') ne "")
	{
		print NEWUSERPREFERENCES "hair_colours:\n";
		@lines = split(/\n/, param('hair_colours'));
		foreach my $line (@lines)
		{
			print NEWUSERPREFERENCES "\t$line\n";
		}
		
	}
	
	if (param('gender') ne "")
	{
		print NEWUSERPREFERENCES "gender:\n";
		print NEWUSERPREFERENCES "\t", param('gender'), "\n";
	}
	
	if (param('age_min') ne "" && param('age_max') ne "")
	{
		print NEWUSERPREFERENCES "age:\n";
		print NEWUSERPREFERENCES "\t","min:\n";
		print NEWUSERPREFERENCES "\t\t", param('age_min'), "\n";
		print NEWUSERPREFERENCES "\t","max:\n";
		print NEWUSERPREFERENCES "\t\t", param('age_max'), "\n"
	}
	
	if (param('weight_min') ne "" && param('weight_max') ne "")
	{
		print NEWUSERPREFERENCES "weight:\n";
		print NEWUSERPREFERENCES "\t","min:\n";
		print NEWUSERPREFERENCES "\t\t", param('weight_min'), "kg\n";
		print NEWUSERPREFERENCES "\t","max:\n";
		print NEWUSERPREFERENCES "\t\t", param('weight_max'), "kg\n"
	}
	if (param('height_min') ne "" && param('height_max') ne "")
	{
		print NEWUSERPREFERENCES "height:\n";
		print NEWUSERPREFERENCES "\t","min:\n";
		print NEWUSERPREFERENCES "\t\t", param('height_min'), "m\n";
		print NEWUSERPREFERENCES "\t","max:\n";
		print NEWUSERPREFERENCES "\t\t", param('height_max'), "m\n"
	}

	close NEWUSERPREFERENCES;
	chmod 0755, $upreferenceFile;

	$globalSessionData{"current_user"} = $username;
	$globalSessionData{"authenticated"} = 0;

	updateSession();

}


#Grab profile data for given username.
#takes 2 arguments, 
#1st argument username desired
#2nd argument is a string, "profile" or "preferences"
#blank 2nd argument assumes profile is wanted
#returns hash of user profile data
sub generateUserData
{
	my ($uname, $option) = @_;
	my $ufolder = $dataFolder.$uname."/";
	my $ucgiFolder = $cgiFolder.$uname."/";
	my @tabspaces = ();
	my %userData = ();
	my $currField = "";
	my $tabstring= ();
	my @otherPhotos = ();

	$userData{"uname"} = $uname;
	
	if(!defined($option) || $option eq "profile")
	{
		$ufile = $ufolder.$defaultProfileFilename;
	}
	elsif ($option eq "preferences")
	{
		$ufile = $ufolder.$defaultPreferenceFilename;
	}
	#debugPrint("trying to find $ufile");
	if (!(-R $ufile))
	{
		#debugPrint("not found");
		$userData{"found"} = 0;
		return %userData;
	}
	
	#go through each line of the file
	#use tab delimitation to figure out if something is a field or a value
	#use a pseudo state machine to decide when to pass in a field or a value 
	open (pFile, "< $ufile");
	$userData{"found"} = 1;
	foreach $line (<pFile>)
	{
		chomp $line;
		
		@tabspaces = $line =~ m/^\t+/g;
		
		$line =~ s/^\t+//g;
		if ($#tabspaces<0) 
		{
			#tabspaces less than one means a field has been added
			#first remove the trailing '|' character from the previous field
			if ($currField ne "")
			{
				$userData{$currField} =~ s/\|$//g;
			}
			$currField = $line;
			$currField =~ s/://g;
			$userData{$currField} = "";
		}
		elsif (!($currField eq ""))
		{
			#extra check to make sure that currfield is not empty
			#tabpsaces greater than 1 indicates a data field
			$userData{$currField} = ($userData{$currField}.$line.'|');
		}

	}


	$userData{"profileImage"} = $ucgiFolder."profile.jpg";
	close (pFile);


	#open the directory and see if there are any other photos to display
	#return the photos as a string joined by '|'
	opendir ((my $udir), $ufolder);
	@otherPhotos = grep{/photo\d*\.jpg/} readdir $udir;
	$userData{"otherPhotos"} = join('|',@otherPhotos);
	closedir $udir;
	
	$userData{"path"} = $ucgiFolder;

	return %userData;

}

#searches for users matching the input string
#input argument is search string and old score
#if no old score is supplied, then we assume we start from nothing and give it a maximum
#else we stack results form the previous calculation
#output argument is array of potentially matched users
sub searchForUsers
{
	my ($searchString, $oldScore) = @_;
	my @matchedUsers = ();
	opendir ((my $searchFolder), $dataFolder);
	@matchedUsers = grep{/\Q$searchString\E/i} readdir $searchFolder;
	closedir $searchFolder;
	return @matchedUsers;

}

#matches 2 specified users
#returns a weighted score of matching
#a lower score indicates a better match
#takes in 2 arguments = 2 usernames
#optional third argument is old score, used for recursion
#default score is worst score

#weights:
#age, gender = 2 (need to work out an age range)
#height, hair colour = 1.5;
sub matchUsers
{
	my ($user1, $user2, $oldScore) = @_;
	#debugPrint("matching user $user1 and $user2");
	my $score = $WORST_SCORE;
	my %u1Data = generateUserData($user1, "profile");
	my %u2Data = generateUserData($user2, "profile");
	my %u1Pref = generateUserData($user1, "preferences");
	my %u2Pref = generateUserData($user2, "preferences");
	my $u2ProfileFile = $dataFolder.$user2."/".$defaultProfileFilename;
	my $u2Age = 0;
	my @matchedHobbies = ();

	

	#see if old score has been passed
	if(defined $oldScore)
	{
		$score = $oldScore;
	}
	

	#calculate special cases for matching first
	
	#gender mismatch is a giant penalty. leave score untouched otherwise
	if (defined $u1Pref{"gender"} && defined $u2Data{"gender"})
	{
		
		if (lc$u1Pref{"gender"} ne lc$u2Data{"gender"})
		{
			$score = $score*100;
		}
	}


	#see if age is in age range
	if(defined $u1Pref{"age"} && defined $u2Data{"birthdate"})
	{
		if ($u1Pref{"age"} =~ 
			/min\:\|\s*([\w\d\.]+)\|\s*max\:\s*\|\s*([\w\d\.]+)/)
		{
			my $min = $1;
			my $max = $2;
			#calculate age
			#note that there are two cases of ages being stored in the database
			#first with year out front, second with year at the back
			if($u2Data{"birthdate"} =~ /(\d{4})\/(\d\d)\/(\d\d)/)
			{	
				$year = (localtime())[5] + 1900;
				$u2Age = $year - $1;
				#debugPrint("$user2: $u2Age");

				$score /=calculateWeight($min, $max, $u2Age);
				
			}
			elsif($u2Data{"birthdate"} =~ /(\d{2})\/(\d{2})\/(\d{4})/)
			{
				$year = (localtime())[5] + 1900;
				$u2Age = $year - $3;
				#debugPrint("badAge $user2: $u2Age");

				$score /=calculateWeight($min, $max, $u2Age);
				
			}
			else
			{
				#age unknown, penalty
				$score /=0.5
			}
			
		}
	}


	#see if weight is in weight range
	if(defined $u1Pref{"weight"} && defined $u2Data{"weight"})
	{
		if ($u1Pref{"weight"} =~ 
			/min\:\|\s*([\d]+)kg\|\s*max\:\s*\|\s*([\d]+)kg/)
		{
			my $min = $1;
			my $max = $2;
			#calculate weight
			
			if($u2Data{"weight"} =~ /\s*(\d+)kg/)
			{	
				my $u2Weight = $1;

				$score /=calculateWeight($min, $max, $u2Weight);
			}
		
			
		}
	}

	#see if height is in height range
	if(defined $u1Pref{"height"} && defined $u2Data{"height"})
	{
		if ($u1Pref{"height"} =~ 
			/min\:\|\s*([\d\.]+)m\|\s*max\:\s*\|\s*([\d\.]+)m/)
		{
			my $min = $1;
			my $max = $2;
			
			#calculate weight
			if($u2Data{"height"} =~ /\s*([\d+\.]+)m/)
			{	
				my $u2Height = $1;

				$score /=calculateWeight($min, $max, $u2Height);
			}

			
		}
	}

	#match hair colours
	#examine u2's hair colour
	#use regex to see if u2's hair colour is in u1's preference list
	if (defined $u2Data{"hair_colour"} && defined $u1Pref{"hair_colours"})
	{
		my $u2Hair = lc$u2Data{"hair_colour"};
		if(lc$u1Pref{"hair_colours"} =~ /$u2Hair/ )
		{
			$score /=2;
		}
		else
		{
			$score /=0.5
		}
	}

	#if oldscore is not defined, it means we've only matched one way.
	#recurse to match in the reverse direction
	

	#now compare common interests by grepping between profile files
	foreach my $field(%u1Data)
	{
		#check if field is a common interest
		if(!defined $specialMatchingFields{$field} 
			&& defined $u1Data{$field}
			&& defined $u2Data{$field})
		{
			my @u1hobbies = split (/\|/, $u1Data{$field});
			#@matchedHobbies, grep {/$hobby/} (<u2Profile>);
			foreach my $u1hobby (@u1hobbies)
			{
				push @matchedHobbies, grep{/$u1hobby/i} $u2Data{$field};
			}
			#debugPrint(@u1hobbies);
		}

	}

	#offset the score by one so that no matches ensures parity
	#offset $#matchedHobbies +1 to reflect count of arrays occurs properly
	#weight each matched hobby as 2

	$score /= (1 + ($#matchedHobbies + 1)*2);
	
	if (!(defined $oldScore))
	{
		$score = matchUsers($user2, $user1, $score);
	}

	return $score;

}


#calculates wieght of success based on (min,max) range and an input value
#higher result is better
#maximum result returned from beign in the range
#outside of the range incurs a penalty
#3 args: min, max and input value
sub calculateWeight
{
	my($min, $max, $input) = @_;
	my $weight = 0;
	my $mean = ($min + $max)/2;
	my $dist = 0;
	my $intervalLen = 0;

	if ($min < $input && $input < $max)
	{
		$weight = $maxWeight;
	}
	else
	{	
		$intervalLen = $max - $min;
		$dist = abs($mean - $input) - $intervalLen;

		$weight = $maxWeight - ($dist/$intervalLen)*10; 

		#floor the value at 0.01
		if($weight<0.01)
		{
			$weight = 0.01;
		}
	}

	return $weight;
}
