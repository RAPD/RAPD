# Get the default preferences setup
DEFAULT_PREFERENCES = {'multiprocessing': False, # Should be False for non-qsub
                       'ram_integrate': False,
                       "flip_beam" : True, # Needed for XDS
                       "analysis": False, #Run analysis on processed data
                       "clean_up": True, # clean up
                       "json": True, # send output as json back to DB
                       "show_plots": False, # plots for command line
                       "progress": False, # progress bar for command line
                       "spacegroup_decider": 'auto', # choices=["auto", "pointless", "xds"],
                       "cluster_use": True,
                       #"rounds_polishing": 1, # not used yet...
                       }
