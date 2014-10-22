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

#create a hash of private fields
%privateFields = ();
$privateFields{"uname"} = 1;
$privateFields{"password"} = 1;
$privateFields{"email"} = 1;
$privateFields{"found"} = 1;
$privateFields{"courses"} = 1;
$privateFields{"name"} = 1;
$privateFields{"profileImage"} = 1;
# my %udata = generateProfileData("AwesomeSurfer30");

# foreach $field (keys %udata)
# {

# 	print "$field:\n $udata{$field}"
# }

# generateProfileData("poop");
generateUserHtml("AwesomeSurfer30");
sub generateUserHtml
{
	my ($uname) = @_;
	my @currData = ();
	my %udata = ();

	print header, start_html('LOVE2041 MOTHERFUCKERS');
	warningsToBrowser(1);

	%udata = generateProfileData($uname);
	if (! $udata{"found"})
	{
		print "fuck\n";
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
			my $fieldToPrint = $field;
			$fieldToPrint =~ s/\_/ /g;
			print h2 "$fieldToPrint";
			@currData = split ('\n',$udata{$field});
			foreach my $entry (@currData)
			{
				print p "$entry";
			}
		}
		#print p "$udata{$field}";
	}
	print end_html;

	

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
			$userData{$currField} = $userData{$currField}.$line."\n"
		}

	}

	$userData{"profileImage"} = $ucgiFolder."profile.jpg";

	

	close (pFile);

	return %userData;

}