#!/usr/bin/env python

import glob
import os
import shutil
import subprocess
import re

def findDeps(filename):
	"""
	Find developmental files and return them
	"""
	#print "findDeps on %s" % filename
	d_files = []
	#set up regular expressions
	js_pat = re.compile("[\'\"]{1}([\.\/\w]*?d_.+?\.js)[\'\"]{1}")
	php_pat = re.compile("[\'\"]{1}([\.\/\w]*?d_.+?\.php)[\'\"]{1}")
	css_pat = re.compile("[\'\"]{1}([\.\/\w]*?d_.+?\.css)[\'\"]{1}")
	in_lines = open(filename,"r").readlines()
	for line in in_lines:
		#look for developmental file references
		for pat in (js_pat,php_pat,css_pat):
			result = pat.search(line)
			if result:
				#print result.group(1),line.rstrip()
				dep = result.group(1)
				if dep.startswith("./"):
					dep = dep[2:]
				d_files.append(dep)
	return(d_files)
	
def newBakFile(filename):
	"""
	Look in old/ and determine the name for the backup file
	"""
	#print "newBakFile %s" % filename
	#look for the highest incremented .bak file
	bak_pat = re.compile(".*\.bak(\d*)")
	my_bak_files = glob.glob("./old/"+filename+".bak*")
	#print my_bak_files
	high = 0
	for bak_file in my_bak_files:
		bak_result = bak_pat.search(bak_file)
		if bak_result:
			try:
				inc = int(bak_result.group(1))
				if  inc > high:
					high = inc
			except:
				pass
	#print high
	new_bak_inc = high + 1
	new_bak_file = "./old/"+os.path.basename(filename)+".bak"+str(new_bak_inc)
	return(new_bak_file)

if __name__ == "__main__":

	print 'deploy.py'
	print '========='
	print '''
	Replaces files N with their d_N counterparts, keeps
	the older verion in the old subdirectory, and changes
	the new standard files to not use d_N calls\n'''

	# Vars for keeping track of what we have acted upon
	looked_at = []
	rolled_out = []
	

	# Head files determine what is rolled out
	head_files = ("d_trip_data_main.php",)
	# Build file list
	dependency_dict = {}
	dependencies = []
	checked_for_dependencies = []
	for head_file in head_files:
		print "Interrogating %s" % head_file
		dependencies.append(head_file)
		checked_for_dependencies.append(head_file)
		my_dependencies = findDeps(head_file)
		dependency_dict[head_file] = my_dependencies
		for dep in my_dependencies:
			if dep not in dependencies:
				dependencies.append(dep)
	print dependencies
	print checked_for_dependencies
	#Now check these files
	for file in dependencies:
		#print "Iterating %d" % len(dependencies)
		print "Interrogating %s" % file
		checked_for_dependencies.append(file)
		my_dependencies = findDeps(file)
		dependency_dict[file] = my_dependencies
		for dep in my_dependencies:
			if dep.startswith("./"):
				dep = dep[2:]
			if dep not in dependencies:
				dependencies.append(dep)
				print "Adding %s" %dep
		
	# Print out deps
	print
	print "Compiled list of dev files"
	print "=========================="
	for i,dep in enumerate(dependencies):
		print i,dep
				
	# Make a new .bakN for each released file in old/
	for dev in dependencies:
		released_file = dev.replace("d_","",1)
		for file in (dev,released_file):
			if os.path.exists(file):
				#print "%s exists" % file
				base_rel_file = os.path.basename(file)
				new_bak_file = newBakFile(file)
				#print new_bak_file
				print "shutil.copy "+file+" "+new_bak_file
				shutil.copy(file,new_bak_file)
				
			# Copy the dev into the released file
			#print "shutil.copy "+dev+" "+released_file
			shutil.copy(dev,released_file)
			
	# Edit the release file to change references from dev files to released files
	for dev_file in dependencies:
		if len(dependency_dict[dev_file]) > 0:
			#print dev_file,dependency_dict[dev_file]
			edit_file = dev_file.replace("d_","",1)
			print "Editing %s" % edit_file
			file_lines = open(dev_file,"r").readlines()
			out_file = open(edit_file,"w")
			for line in file_lines:
				if "d_" in line:
					my_write = False
					for dep_file in dependency_dict[dev_file]:
						if dep_file in line:
							print line.rstrip()
							print line.replace(dep_file,dep_file.replace("d_","",1))
							out_file.write(line.replace(dep_file,dep_file.replace("d_","",1)))
							break
					else:
						print "No dep file",line
						out_file.write(line)
					
				else:
					out_file.write(line)
					
			out_file.close()


