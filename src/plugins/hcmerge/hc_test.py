'''
Created June 12, 2015
By Kay Perry, Frank Murphy

Distributed under the terms of the GNU General Public License.

This file is part of RAPD

RAPD is a free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 3 of the license,
or (at your option) any later version.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

hc_test.py is for testing HCMerge.
	Checks for: matplotlib, hcluster, cctbx, AIMLESS, POINTLESS
	Tests hcluster to make sure matplotlib works with it.

'''

import re 
import subprocess
import time
import unittest

#The following check for functioning of pipeline specific python requirements
class TestHcluster(unittest.TestCase):
    """Test to ensure that hcluster module is available and runs"""

    compatible_versions = ('0.2.0',)

    def test_availability(self):
        """Test for required hcluster module"""
        try:
            import hcluster
            result = True
        except:
            result = False
            print "hcluster module not available."
        self.assertTrue(result)

    def test_plot(self):
    	"""Test for ability of matplotlib to plot when called from within hcluster"""
    	from hcluster import linkage, dendrogram
    	Y = [0.035799737505230245, 0.1811812512148112, 0.18161858552553956, 0.04994734393972866,
    		0.06927030254919231, 0.5252030028971776, 0.25599557979833076, 0.17263640709974182,
			0.21648328487945045, 0.23166379346914234, 0.10977388952328548, 0.09478470286615925,
			0.04132745408345362, 0.7485043497658326, 0.23710239238698283, 0.18559942955019038,
			0.18528123099951554, 0.10557917871965272, 0.18896587244751162, 0.22979622414785061,
			0.4812500870612588, 0.1595844742784095, 0.08232086667793992, 0.07645504116931245,
			0.14760429506721406, 0.11615455329624691, 0.18506169911660608, 0.15208127394209903,
			0.13493267261670583, 0.1683158653022112, 0.05783488469585951, 0.20997258124495488,
			0.15552875660003107, 0.19184061684283715, 0.27662093729644177, 0.22603945264163194,
			0.19784169961244613, 0.14950555280594968, 0.17855956953284702, 0.18664743498752967,
			0.21652972682435756, 0.3441090944871187, 0.22148144735712694, 0.1329329863326959,
			0.14856710057703015] # The list of distances, our equivalent of pdist
        Z = linkage(Y, method="complete") # The linkage defaults to single and euclidean
        try:
		    import matplotlib.pylab
		    dendrogram(Z, no_plot=False)
		    matplotlib.pylab.xlabel('All Datasets')
		    matplotlib.pylab.ylabel('1 - Correlation Coefficient')
		    f = matplotlib.pylab.gcf()
		    f.set_size_inches([8,8])
		    f.subplots_adjust(bottom=0.4)
		    matplotlib.pylab.savefig('test-dendrogram.png', dpi=300)
		    print "test-dendrogram.png generated.  Inspect to ensure that hcluster and matplotlib are functioning."
        except:
		    d = dendrogram(Z, no_plot=True)
		    print "Matplotlib.pylab not present. Dendrogram information:" + str(d)

class TestCCTBX(unittest.TestCase):
    """Test for availability of cctbx modules"""
    
    def test_availability(self):
        """Test for required cctbx module"""
        try:
			from iotbx import reflection_file_reader
			from cctbx import miller
			from cctbx.array_family import flex
			from cctbx.sgtbx import space_group_symbols
			result = True
        except:
            result = False
            output = subprocess.Popen(['which cctbx.python'],
                                  	stdout = subprocess.PIPE,
                                  	stderr = subprocess.PIPE,
                                  	shell = True)
            (stdout, stderr) = output.communicate()
            if stderr:
        		print "cctbx module is not available."
            else:
            	print "Full version of cctbx containing iotbx required."
            	print "Your cctbx is " + stdout
        self.assertTrue(result)

class TestMatplotlib(unittest.TestCase):
    """Test for availability of the matplotlib module and that it is an
    approved version"""

    compatible_versions = ('1.1.0','1.1.1','1.2.1','1.3.1',)

    def test_availability(self):
        """Test for availability of the matplotlib module and can be set correctly"""
        try:
            import matplotlib
			# Force matplotlib to not use any Xwindows backend.  Must be called before any other matplotlib/pylab import.
            matplotlib.use('Agg')
            result = True
        except:
            result = False
            print "Matplotlib not available.  Dendrogram plotting will fail."
        self.assertTrue(result)

    def test_version(self):
        """Test to make sure matplotlib is an acceptable version"""
        import matplotlib
        version = matplotlib.__version__
        self.assertIn(version, self.compatible_versions)

class TestAimless(unittest.TestCase):

    compatible_versions = ('0.1.27','0.1.29','0.5.17',)
    notcompatible_versions = (,)

    def test_availability(self):
        result = False
        output = subprocess.Popen(['aimless test'],
                                  stdout = subprocess.PIPE,
                                  stderr = subprocess.PIPE,
                                  shell = True)
        (stdout, stderr) = output.communicate()
        while (output.poll() == None):
            time.sleep(0.1)
        if 'AIMLESS' in stdout:
            result = True
        else:
        	result = False
        	print "AIMLESS program missing in path."
        self.assertTrue(result)

    def test_version(self):
        output = subprocess.Popen(['aimless test'],
                                  stdout = subprocess.PIPE,
                                  stderr = subprocess.PIPE,
                                  shell = True)
        (stdout, stderr) = output.communicate()
        while (output.poll() == None):
            time.sleep(0.1)
        m = re.search('version ([\d\.]+)', stdout)
        version = m.group(1)
        self.assertIn(version, self.compatible_versions)
        self.assertNotIn(version, self.notcompatible_versions)

class TestPointless(unittest.TestCase):
    compatible_versions = ('1.7.6','1.10.13',)
    notcompatible_versions = ('1.9.33',)

    def test_availability(self):
        result = False
        output = subprocess.Popen(['pointless test'],
                                  stdout = subprocess.PIPE,
                                  stderr = subprocess.PIPE,
                                  shell = True)
        (stdout, stderr) = output.communicate()
        while (output.poll() == None):
            time.sleep(0.1)
        if 'POINTLESS' in stdout:
            result = True
        else:
        	result = False
        	print "POINTLESS program missing in path."
        self.assertTrue(result)

    def test_version(self):
        output = subprocess.Popen(['pointless test'],
                                  stdout = subprocess.PIPE,
                                  stderr = subprocess.PIPE,
                                  shell = True)
        (stdout, stderr) = output.communicate()
        while (output.poll() == None):
            time.sleep(0.1)
        m = re.search('version ([\d\.]+)', stdout)
        version = m.group(1)
        self.assertIn(version, self.compatible_versions)
        self.assertNotIn(version, self.notcompatible_versions)
        
cctbxsuite = unittest.TestLoader().loadTestsFromTestCase(TestCCTBX)
matplotlibsuite = unittest.TestLoader().loadTestsFromTestCase(TestMatplotlib)
hclustersuite = unittest.TestLoader().loadTestsFromTestCase(TestHcluster)
aimlesssuite = unittest.TestLoader().loadTestsFromTestCase(TestAimless)
pointlesssuite = unittest.TestLoader().loadTestsFromTestCase(TestPointless)
alltests = unittest.TestSuite([cctbxsuite,matplotlibsuite,aimlesssuite,pointlesssuite,hclustersuite])
unittest.TextTestRunner(verbosity=2).run(alltests)


        