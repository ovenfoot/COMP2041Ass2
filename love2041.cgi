#!/usr/bin/perl -w
# Simple CGI script written by andrewt@cse.unsw.edu.au
# to demonstrate a possible CGI security hole
use Cwd;
use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);


$dataFolder = getcwd."/students/";
$defaultProfileFilename = "profile.txt";

my %udata = generateProfileData("AwesomeSurfer30");

foreach $field (keys %udata)
{
	print "$field:\n $udata{$field}"
}

generateProfileData("poop");
sub generateHtml
{
	print header, start_html('LOVE2041 MOTHERFUCKERS');
	warningsToBrowser(1);

}

#Grab profile data for given username.
#takes 1 argument, username desired
#returns hash of user profile data
sub generateProfileData
{
	my ($uname) = @_;
	my $ufolder = $dataFolder.$uname."/";
	my $profileFile = $ufolder.$defaultProfileFilename;
	my @tabspaces = ();
	my %userData = ();
	my $currField = "";
	my $tabstring= ();

	$userData{"uname"} = $uname;
	
	if (!(-R $profileFile))
	{
		print "user $uname not  found!\n";
		return (-1);
	}
	print "Getting $uname from  $ufolder\n";

	open (pFile, "< $profileFile");

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
			#tabpsaces greater than 1 indicates a data field
			$userData{$currField} = $userData{$currField}.$line."\n"
		}
	}

	

	close (pFile);

	return %userData;

}