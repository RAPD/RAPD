"""
Methods for creatig precession photos from integrated data set
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2012-2023, Cornell University
All rights reserved.

RAPD is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
__created__ = "2012-01-25"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

# Standard imports
from multiprocessing import Process, Queue
import os
import shutil
import time

# RAPD imports
from . import parse as Parse
from utils.communicate import rapd_send
from utils.modules import load_module
import utils.xutils as Utils
import utils.types as rapd_types

class LabelitPP(Process):
    def __init__(self, input, output=None, logger: rapd_types.bool_logger = None) -> None:
        logger.info("LabelitPP.__init__")
        self.st = time.time()
        self.input = input
        self.output = output
        self.logger = logger
        self.working_dir = self.input[0].get("dir", os.getcwd())
        self.agent_directories = self.input[0].get("agent_directories")
        self.gui = self.input[0].get("gui", True)
        self.test = self.input[0].get("test", False)
        self.clean = self.input[0].get("clean", True)
        self.controller_address = self.input[0].get("control", False)
        self.verbose = self.input[0].get("verbose", False)

        #Number of Labelit iterations to run. (Default is 4) added 2 more to test new Labelit options
        self.iterations = 6
        #Set times for processes. "False" to disable.
        self.stats_timer = 180
        self.labelit_timer = 120
        self.labelitpp_timer = False
        self.labelit_input = False
        self.labelit_log = {}
        self.labelit_log["0"] = []
        self.labelit_results = {}
        self.labelitpp_results = False
        self.labelit_jobs = {}
        self.labelit_summary = False
        self.labelit_failed = False
        self.failed = False
        self.pp_jobs = {}
        self.pids = {}
        #Labelit settings
        self.index_number = False
        self.spacegroup = "None"
        self.min_spots = False
        self.ignore_user_cell = False
        self.ignore_user_sg = False
        self.blank_image = False
        self.pseudotrans = False
        self.min_good_spots = False
        self.twotheta = False
        self.multiproc = True
        # For rerunning Labelit when it does not index correctly with a pair.
        self.cycle = 0
        if "run" in self.input[0]:
            #Variables I call in more than one place
            self.total = self.input[0].get("run").get("total")
            #For determining detector type. Should move to rapd_site probably.
            if self.input[0].get("run").get("fullname")[-3:] == "cbf":
                if float(self.input[0].get("run").get("x_beam")) > 200.0:
                    self.vendortype = "Pilatus-6M"
                else:
                    self.vendortype = "ADSC-HF4M"
            else:
                self.vendortype = "ADSC"
        else:
            self.failed = True
        #******BEAMLINE SPECIFIC*****
        #self.cluster_use = Utils.checkCluster()
        # self.cluster_use = BLspec.checkCluster()
        #******BEAMLINE SPECIFIC*****
        if self.test:
            self.clean = False

        Process.__init__(self, name="LabelitPP")
        self.start()

    def run(self) -> None:
        """
        Convoluted path of modules to run.
        """
        if self.verbose:
            self.logger.debug("LabelitPP::run")

        self.preprocess()
        if self.failed == False:
            #Run Labelit
            self.preprocess_labelit()
            self.process_labelit()
            #Sorts labelit results by highest symmetry.
            self.labelit_sort()
            if self.labelit_failed == False:
                #Run labelit_precession_photo for the 3 planes
                self.process_labelit_precession()
                self.run_queue()
        else:
            Utils.failedHTML(self, "jon_summary_pp")

        # Finish everything up
        self.postprocess()

    def preprocess(self) -> None:
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for Stat pipeline
        """
        if self.verbose:
            self.logger.debug("LabelitPP::preprocess")
        Utils.folders(self)
        #print out recognition of the program being used
        self.print_info()

    def preprocess_labelit(self) -> None:
        """
        Setup input dict for RunLabelit.
        """
        if self.verbose:
            self.logger.debug("LabelitPP::preprocess_labelit")

        import glob

        try:
            x_beam = float(self.input[0].get("run").get("x_beam"))
            y_beam = float(self.input[0].get("run").get("y_beam"))
            osc = float(self.input[0].get("run").get("osc_range"))
            first = self.input[0].get("run").get("fullname")
            self.labelit_dir = os.path.join(self.working_dir, "Labelit")
            self.images = []
            if self.test == False:
                #Check if dir already exists from previous run and delete if it does
                if os.path.exists(self.labelit_dir):
                    os.system("rm -rf %s"%self.labelit_dir)

            second = False
            self.images.append("AUTOINDEX")
            #Pass the Labelit working_dir.
            self.images.append({"work": self.labelit_dir})
            header = {}
            header["fullname"] = first
            header["twotheta"] = str(self.input[0].get("run").get("two_theta"))
            header["distance"] = str(self.input[0].get("run").get("distance"))
            header["binning"] = self.input[0].get("run").get("binning")
            if self.gui:
                header["acc_time"] = "0"
            self.images.append(header)
            #Sort out which images to autoindex
            s = first.rfind("_")+1
            f = first.rfind(".")
            num1 = first[s:f]
            range1 = self.total*osc
            #Figure out last frame number to use here and later
            ls = glob.glob("%s*%s" % (first[:s], first[f:]))
            ls.sort()
            last = int(num1)+self.total
            ls1 = "%s%s%s" % (first[:s], str(last).zfill(f-s), first[f:])
            if os.path.exists(ls1):
                self.last = last
            else:
                self.last = int(ls[-1][s:f])
            if range1 > 90:
                second = first[:s]+str(int(90/osc)-1+int(num1)).zfill(f-s)+first[f:]
            elif range1 < 5:
                pass
            else:
                second = first[:s]+str(self.last).zfill(f-s)+first[f:]
            if second:
                if os.path.exists(second):
                    header2 = header.copy()
                    header2.update({"fullname": second})
                    self.images.append(header2)
            self.images.append({"x_beam": x_beam, "y_beam": y_beam})
            self.images.append(("127.0.0.1", 50001))

        except:
            self.logger.exception("**ERROR in LabelitPP.preprocess_labelit**")

    def process_labelit(self, inp=False) -> None:
        """
        Initiate Labelit runs.
        """
        if self.verbose:
            self.logger.debug("LabelitPP::process_labelit")

        try:
            queue = Queue()
            params = {}
            params["test"] = self.test
            params["cluster"] = False # self.cluster_use # TODO
            params["verbose"] = self.verbose
            args1 = {}
            if inp:
                args1["input"] = inp
            else:
                args1["input"] = self.images
            args1["output"] = queue
            args1["params"] = params
            args1["logger"] = self.logger

            # Import the RunLabelit class
            agent = load_module(seek_module="rapd_agent_index+strategy",
                                directories=self.agent_directories,
                                logger=self.logger)

            Process(target=agent.RunLabelit, kwargs=args1).start()
            self.labelit_results = queue.get()
            self.labelit_log = queue.get()

        except:
            self.logger.exception("**Error in LabelitPP.process_labelit**")

    def process_labelit_precession(self) -> None:
        """
        Run labelit.precession_photo on dataset.
        """
        if self.verbose:
            self.logger.debug("LabelitPP::process_labelit_precession")

        try:
            bn = self.labelit_results.get("labelit_stats").get("best").get("sol")
            first = self.input[0].get("run").get("fullname")
            num1 = int(first[first.rfind("_")+1:first.rfind(".")])

            l = ["H,K,0", "H,0,L", "0,K,L"]
            for i in range(len(l)):
                command = 'labelit.precession_photo bravais_choice=%s image_range=%s,%s ' \
                          'plot_section="%s" pdf_output.file=pp%s.pdf' % (bn, num1, self.last, l[i], i)
                #command += " resolution_outer=3.0 layer_width=0.1"
                if self.verbose:
                    self.logger.debug(command)
                queue = Queue()
                if self.test:
                    job = Process(target=Utils.processLocal, args=("ls", self.logger, queue))
                elif False: # TODO self.cluster_use:
                    pass
                    # job = multiprocessing.Process(target=Utils.processCluster,args=(self,(command,"pp%s.log"%i),"all.q",queue))
                    # job = Process(target=Utils.processCluster,args=(self,(command,"pp%s.log"%i,"all.q"),queue))
                    # job = Process(target=BLspec.processCluster, args=(self, (command, "pp%s.log" % i, "all.q"), queue))
                else:
                    job = Process(target=Utils.processLocal, args=((command, "pp%s.log" % i), self.logger, queue))
                job.start()
                self.pp_jobs[job] = "pp%s" % i
                self.pids["pp%s"%i] = queue.get()

        except:
            self.logger.exception("**Error in LabelitPP.process_labelit_precession**")

    def postprocess_labelit_precession(self, iteration) -> None:
        """
        convert pdf's and copy to working dir.
        """
        if self.verbose:
            self.logger.debug("LabelitPP::postprocessPP")

        try:
            pdf = "%s.pdf" % iteration
            jpg = pdf.replace("pdf", "jpg")
            if os.path.exists(pdf):
                Utils.convertImage(self, pdf, jpg)
                if os.path.exists(os.path.join(self.working_dir, jpg)):
                    os.system("rm -rf %s" % os.path.join(self.working_dir, jpg))
                shutil.copy(jpg, self.working_dir)
            # Look for errors if pdf not generated
            else:
                if os.path.exists("%s.log" % iteration):
                    data = Parse.ParseOutputLabelitPP(self, open("%s.log" % iteration, "r").readlines())
                    if data != None:
                        self.total = data
                        return "kill"

        except:
            self.logger.exception("**ERROR in LabelitPP.postprocessPP**")

    def postprocess(self) -> None:
        """
        Pass info back to the core.
        """
        if self.verbose:
            self.logger.debug("LabelitPP::postprocess")

        failed = False
        output_files = False
        jpg = {}

        # Change to working dir.
        os.chdir(self.working_dir)

        # Save the path for the jpg files
        l = ["0KL", "H0L", "HK0"]
        for i in range(len(l)):
            try:
                if os.path.exists("pp%s.jpg"%i):
                    jpg["%s jpg" % l[i]] = os.path.join(self.working_dir, "pp%s.jpg"%i)
                else:
                    jpg["%s jpg" % l[i]] = None
                    self.clean = False
            except:
                self.logger.exception("**Could not save LabelitPP results**")
                failed = True
        self.labelitpp_results = {"LabelitPP results": jpg}

        # Create and save path of html summary file
        self.html_summary_pp()

        try:
            output = {}
            if self.gui:
                html = "jon_summary_pp.php"
            else:
                html = "jon_summary_pp.html"
            if os.path.exists(html):
                output["LabelitPP summary html"] = os.path.join(self.working_dir, html)
            else:
                output["LabelitPP summary html"] = "None"
            output_files = {"Output files": output}
        except:
            self.logger.exception("**Could not save LabelitPP html path**")
            failed = True

        status = {}
        if failed:
            status["status"] = "FAILED"
        else:
            status["status"] = "SUCCESS"

        #Send back results
        try:
            results = {}
            results.update(status)
            if self.labelitpp_results:
                results.update(self.labelitpp_results)
            if output_files:
                results.update(output_files)
            if self.output != None:
                self.output.put(results)
            else:
                if self.gui:
                    self.input.append(results)
                    #   self.sendBack2(self.input)
                    rapd_send(self.controller_address, self.input)
        except:
            self.logger.exception("**Could not send results to pipe.**")

        try:
            #Cleanup my mess.
            if self.clean:
                if self.verbose:
                    self.logger.debug("Cleaning up files and folders")
                if os.path.exists(self.labelit_dir):
                    os.system("rm -rf %s"%self.labelit_dir)
                    # os.system("rm -rf Labelit*")
        except:
            self.logger.exception("**Could not cleanup**")

        # Say job is complete.
        t = round(time.time()-self.st)
        self.logger.debug("-------------------------------------")
        self.logger.debug("RAPD labelit.precession_photo complete.")
        self.logger.debug("Total elapsed time: %s seconds" % t)
        self.logger.debug("-------------------------------------")
        if self.output == None:
            print("\n-------------------------------------")
            print("RAPD labelit.precession_photo complete.")
            print("Total elapsed time: %s seconds" % t)
            print("-------------------------------------")

    def run_queue(self, run_before=False) -> None:
        """
        Run queue for Labelit.
        """
        if self.verbose:
            self.logger.debug("LabelitPP::run_queue")
        try:
            timed_out = False
            timer = 0
            rerun = False
            jobs = list(self.pp_jobs.keys())
            if jobs != ["None"]:
                counter = len(jobs)
                while counter != 0:
                    for job in jobs:
                        if job.is_alive() == False:
                            jobs.remove(job)
                            del self.pids[self.pp_jobs[job]]
                            job = self.postprocess_labelit_precession(self.pp_jobs[job])
                            if job == "kill":
                                timed_out = True
                                rerun = True
                                counter = 0
                                break
                            else:
                                counter -= 1
                    time.sleep(0.2)
                    timer += 0.2
                    if self.output == None:
                        if self.verbose:
                            if round(timer%1, 1) in (0.0, 1.0):
                                print("Waiting for Labelit.precession_photo to finish %s seconds"%timer)
                    if self.labelitpp_timer:
                        if timer >= self.labelitpp_timer:
                            timed_out = True
                            # Check folders to see why it timed out.
                            self.clean = False
                            break
                if timed_out:
                    if self.verbose:
                        self.logger.debug("Labelitpp timed out.")
                        print("Labelitpp timed out.")
                    for pid in list(self.pids.values()):
                        # TODO
                        if False: # self.cluster_use:
                            pass
                            # Utils.killChildrenCluster(self,pid)
                            # BLspec.killChildrenCluster(self, pid)
                        else:
                            Utils.killChildren(self, pid)
            if rerun:
                if run_before == False:
                    self.pp_jobs = {}
                    self.pids = {}
                    self.process_labelit_precession()
                    self.run_queue(True)

            if self.verbose:
                self.logger.debug("LabelitPP finished.")

        except:
            self.logger.exception("**Error in LabelitPP.run_queue**")

    def labelit_sort(self) -> None:
        """
        Sort out which iteration of Labelit has the highest symmetry and choose that solution. If
        Labelit does not find a solution, finish up the pipeline.
        """
        if self.verbose:
            self.logger.debug("LabelitPP::labelit_sort")

        import numpy
        rms_list1 = []
        metric_list1 = []
        sol_dict = {}
        sg_list1 = []
        sg_dict = {}
        sym = "0"
        try:
            for run in list(self.labelit_results.keys()):
                if type(self.labelit_results[run].get("labelit_results")) == dict:
                    # Check for pseudotranslation
                    if self.labelit_results[run].get("labelit_results").get("pseudotrans") == True:
                        self.pseudotrans = True
                    Utils.getLabelitStats(self, inp=run, simple=False)
                    rms_list1.append(float(self.labelit_results[run].get("labelit_stats").get("best").get("mos_rms")))
                    metric_list1.append(float(self.labelit_results[run].get("labelit_stats").get("best").get("metric")))
                    sg = Utils.convertSG(self, self.labelit_results[run].get("labelit_stats").get("best").get("SG"))
                    sg_dict[run] = sg
                    sg_list1.append(float(sg))
                else:
                    # If Labelit failed, set dummy params
                    sg_dict[run] = "0"
                    sg_list1.append(0)
                    rms_list1.append(100)
                    metric_list1.append(100)
            for x in range(len(sg_list1)):
                if sg_list1[x] == numpy.amax(sg_list1):
                    # If its P1 look at the Mosflm RMS, else look at the Labelit metric.
                    if str(sg_list1[x]) == "1.0":
                        sol_dict[rms_list1[x]] = list(self.labelit_results.keys())[x]
                    else:
                        sol_dict[metric_list1[x]] = list(self.labelit_results.keys())[x]
            l = list(sol_dict.keys())
            l.sort()
            #Best Labelit_results key
            highest = sol_dict[l[0]]
            #symmetry of best solution
            sym = sg_dict[highest]

            #If there is a solution...
            if sym != "0":
                self.labelit_results = self.labelit_results[highest]
                os.chdir(os.path.join(self.labelit_dir, highest))
                self.logger.debug("The sorted labelit solution was #%s" % highest)
            else:
                failed = False
                #If pairs failed, then retry autoindexing on single frames.
                if len(self.images) == 6:
                    if self.cycle in (0, 1):
                        junk = list(self.images)
                        del junk[3-self.cycle]
                        self.cycle += 1
                        self.process_labelit(junk)
                        self.labelit_sort()
                    else:
                        failed = True
                else:
                    failed = True
                # If there is no solution from Labelit...
                if failed:
                    self.logger.debug("No solution was found when sorting Labelit results.")
                    self.labelit_failed = True
                    self.labelit_results = {"labelit_results":"FAILED"}

        except:
            self.logger.exception("**ERROR in LabelitPP.labelit_sort**")

    def print_info(self) -> None:
        """
        Print information regarding programs utilized by RAPD
        """
        if self.verbose:
            self.logger.debug("LabelitPP::print_info")
        try:
            print("=======================")
            print("RAPD developed using Labelit")
            print("Reference:  J. Appl. Cryst. 37, 399-409 (2004)")
            print("Website:    http://adder.lbl.gov/labelit/ \n")
            print("RAPD developed using Mosflm")
            print("Reference: Leslie, A.G.W., (1992), Joint CCP4 + ESF-EAMCB Newsletter on Protein Crystallography, No. 26")
            print("Website:   http://www.mrc-lmb.cam.ac.uk/harry/mosflm/")
            print("=======================")
            self.logger.debug("=======================")
            self.logger.debug("RAPD developed using Labelit")
            self.logger.debug("Reference:  J. Appl. Cryst. 37, 399-409 (2004)")
            self.logger.debug("Website:    http://adder.lbl.gov/labelit/ \n")
            self.logger.debug("RAPD developed using Mosflm")
            self.logger.debug("Reference: Leslie, A.G.W., (1992), Joint CCP4 + ESF-EAMCB Newsletter on Protein Crystallography, No. 26")
            self.logger.debug("Website:   http://www.mrc-lmb.cam.ac.uk/harry/mosflm/")
            self.logger.debug("=======================")

        except:
            self.logger.exception("**Error in LabelitPP.print_info**")

    def html_summary_pp(self) -> None:
        """
        Create HTML/php files for Labelit.precession_photo output results.
        """
        if self.verbose:
            self.logger.debug("LabelitPP::html_summary_pp")

        try:
            l = ["0KL", "H0L", "HK0"]
            if self.gui:
                sl = "jon_summary_pp.php"
            else:
                sl = "jon_summary_pp.html"
            jon_summary = open(sl, "w")
            jon_summary.write(Utils.getHTMLHeader(self))
            jon_summary.write("%4s$(function() {\n%6s$('.tabs').tabs();\n%4s});\n" % (3*("", )))
            jon_summary.write("%4s</script>\n%2s</head>\n%2s<body>\n%4s<table>\n%6s<tr>\n" % (5*("", )))
            jon_summary.write('%8s<td width="100%%">\n%10s<div class="tabs">\n%12s<ul>\n' % (3*("", )))
            for i in range(len(l)):
                jon_summary.write('%14s<li><a href="#tabs-54%s">%s</a></li>\n' % ("", i, l[i]))
            jon_summary.write("%12s</ul>\n" % "")
            for i in range(len(l)):
                jon_summary.write('%12s<div id="tabs-54%s">\n' % ("", i))
                if self.labelitpp_results.get("LabelitPP results").get("%s jpg" % l[i]) == None:
                    jon_summary.write("%14s<p>The precession photo for this plane did not work.</p>\n" % "")
                else:
                    if self.gui:
                        jon_summary.write("%14s<div id='pp%s_jpg' style='text-align:center'></div>\n" % ("", i))
                    else:
                        jon_summary.write('%14s<IMG SRC="%s">\n' % ("", self.labelitpp_results.get("LabelitPP results").get("%s jpg" % l[i])))
                jon_summary.write("%12s</div>\n" % "")
            jon_summary.write("%10s</div>\n%8s</td>\n%6s</tr>\n%4s</table>\n%2s</body>\n</html>\n" % (5*("", )))
            jon_summary.close()

        except:
            self.logger.exception("**ERROR in LabelitPP.html_summary_pp**")

if __name__ == "__main__":
    # Input
    import logging, logging.handlers

    """
    {'fullname':'/gpfs6/users/mizzou/tanner_E_443/images/Tanner/runs/AfUDPGlcD6/AfUDPGlcD6_1_001.img',
     'total':90,
     'osc_range':'1.0',
     'x_beam':'153.75',
     'y_beam':'158.93',
     #'x_beam':'0',
     #'y_beam':'0',
     'binning':'2x2',
     'two_theta':0.0,
     'distance':'309.3',
    },
    """
    inp = [{'run':{'fullname':'/gpfs1/users/necat/Jon/images/Gaudet_4zi9/P118-WW-A9RUN_1_001.img',
                   'total':180,
                   'osc_range':'1.0',
                   'x_beam':'156.3',
                   'y_beam':'165.2',
                   #'x_beam':'0',
                   #'y_beam':'0',
                   'binning':'2x2',
                   'two_theta':0.0,
                   'distance':'250.0',
                  },

            'dir' :  '/gpfs6/users/necat/Jon/RAPD_test/Output',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/PK_lu_peak.sca',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/insulin.sca',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/Y567A_ATrich_dTTP_free.mtz',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/UGM_PTS.sca',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/1UXM_A4V_twin.mtz',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/r3_tricky_ANOM.sca',
            'data': '/gpfs6/run2013_3/24ID-E/mizzou/tanner_E_443/process/rapd/integrate/AfUDPGlcD6_1/AfUDPGlcD6_1_1/AfUDPGlcD6_1_1_free.mtz',
            #'timer': 15,
            'clean': False,
            'test': False,
            'verbose':True,
            'gui'  : False,
            'control': ('164.54.212.165', 50001),
            'passback': True,
            'process_id': 11111,
           }]
    #start logging
    LOG_FILENAME = os.path.join(inp[0].get('dir'), 'rapd.log')
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    LabelitPP(inp, output=None, logger=logger)
