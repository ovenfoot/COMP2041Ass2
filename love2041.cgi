#!/usr/bin/perl -w
# Simple CGI script written by andrewt@cse.unsw.edu.au
# to demonstrate a possible CGI security hole
use Cwd;
use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use File::Copy;

$cgiFolder = "http://cgi.cse.unsw.edu.au/~tngu211/students/";
$dataFolder = getcwd."/students/";
$defaultProfileFilename = "profile.txt";
$currProfile = "";
$homeUrl = "http://cgi.cse.unsw.edu.au/~tngu211/love2041.cgi";
$userListURL = "http://cgi.cse.unsw.edu.au/~tngu211/love2041.cgi?|allusers";
$authenticated = 0;
$timeToLive = 600; #seconds
%globalSessionData = ();


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

#checkSession();
if (checkSession() != 0)
{
	if(defined(param ("uname")) && defined(param("pass")) )
	{
		#debugPrint("yass");
		$globalSessionData{"authenticated"} = authenticate();
		if($globalSessionData{"authenticated"} ==0)
		{
			updateSession();
			#debugPrint($globalSessionData{"authenticated"});
			#debugPrint("poop");
			generateUserListHtml();
		}
		else
		{
			generateHomePage();	
		}
	}
	else
	{
		
		generateHomePage();
	}
}
elsif ($ENV{'QUERY_STRING'} eq "" )
{
	generateUserListHtml();
}
elsif ($ENV{'QUERY_STRING'} =~ /^[\|].*/ )
{
	#fornow assume command character is '|'
	my $query = $ENV{'QUERY_STRING'};
	$query =~ s/\|//g;
	if($query eq "allusers")
	{
		generateUserListHtml();
	}
	elsif($query eq "logout")
	{
		logout();
	}
}
else
{
	$currProfile = $ENV{'QUERY_STRING'};
	generateUserHtml($currProfile);
}


#generateUserHtml($currProfile);

sub authenticate
{
	my $uname = param('uname');
	my $password = param('pass');
	my %udata = generateProfileData($uname);

	if (!$udata{"found"})
	{
		return (-1);
	}
	my $actpass = $udata{"password"};
	$actpass=~ s/\s*$//g;
	$actpass =~ s/^\s*//g;

	$password =~ s/\s*$//g;
	if ($actpass eq $password)
	{
		param("actPass", $password);
		param("upass", $udata{"password"});

		return 0;#
	}
	else
	{
		#return $password.$udata{"pa                                                  ssword"};
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
	#checkSession();

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
	}

	print a;
	print '<!-- Designed by DreamTemplate. Please leave link unmodified. -->
		<br><center><a href="http://www.dreamtemplate.com" title="Website Templates" target="_blank">Website templates</a></center>';
	print end_html;

	
}

sub logout
{
	
	my $ip = $ENV{"REMOTE_ADDR"};
	$ip =~ s/\./\_/g;
	my $sessionFile = "$ip.acc";

	unlink $sessionFile;

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
sub generateHomePage
{
	#print header;
	
	createNewSession();

	beginPage();

	print h1 "Welcome to LOVE2041, the most ghetto piece of shit dating website ever";

	print h1;
	printLink($homeUrl."?|allusers", "Browse All Users");
	print "</h1>";


	print start_form,
        'Enter login: ', p textfield('uname'), p "<br>\n",
        ' Enter password: ', p password_field('pass'),p "<br>\n",
        submit('Login'),
        end_form;
		

	endPage();
}
sub generateUserListHtml
{
	#print header;
	beginPage();

	my @users = getUserList();
	warningsToBrowser(1);

	print h1 "Browse Users";
	#print p $globalSessionData{"authenticated"};
	#printLink($homeUrl, "RESTART");

	#print p $ENV{'QUERY_STRING'};
	foreach my $user (@users)
	{

		my $userURL = $homeUrl."?$user";
		print p;
		printLink($userURL, $user);
		#print p $user;
	}

	endPage();
}

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

sub generateUserHtml
{
	my ($uname) = @_;
	my @currData = ();
	my %udata = ();
	my @otherPhotos = ();
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

	#print image
	$imagePath = $udata{"profileImage"};
	print "<img src=$imagePath><p>\n";	
	
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
		#print p "$udata{$field}";
	}



	print h2 "Other Photos";
	@otherPhotos = split(/\|/, $udata{"otherPhotos"});
	foreach my $photo (@otherPhotos)
	{	
		$imagePath = $udata{"path"}.$photo;
		print "<img src=$imagePath><p>\n";
	}
	print p;
	
	print h1;
	printLink($userListURL, "Back to User List");

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
	#print "Getting $uname from  $ufolder\n";

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

	opendir my $udir, $ufolder;
		@otherPhotos = grep{/photo\d*\.jpg/} readdir $udir;
	closedir $udir;
	
	$userData{"path"} = $ucgiFolder;
	$userData{"otherPhotos"} = join('|',@otherPhotos);
	return %userData;

}

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
	# print p "last access", $globalSessionData{"last_access"};
	# print p "time to die: $timeToDie";
	# print p "authenticaed = $authenticated";
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