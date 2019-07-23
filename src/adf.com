cad hklin1 /gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.mtz hklin2 /gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz hklout adf_input.mtz<<eof3
labin file 1 E1=FC  E2=PHIC E3=FOM
labin file 2 all
end
eof3
fft hklin adf_input.mtz mapout map.tmp<<eof4
scale F1 1.0
labin DANO=DANO SIG1=SIGDANO PHI=PHIC W=FOM
end
eof4
mapmask mapin map.tmp xyzin /gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.pdb mapout /gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1_adf.map<<eof5
border 5
end
eof5
peakmax mapin /gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1_adf.map xyzout /gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1_adf_peak.pdb<<eof6
numpeaks 50
end
eof6

