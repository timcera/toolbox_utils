"""
catalog
----------------------------------

Tests for `hspf_reader plotgen` module.
"""

import sys
from unittest import TestCase

from pandas.testing import assert_frame_equal

from toolbox_utils import tsutils

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import pandas as pd

from toolbox_utils import tsutils


def capture(func, *args, **kwds):
    sys.stdout = StringIO()  # capture output
    out = func(*args, **kwds)
    out = sys.stdout.getvalue()  # release output
    try:
        out = bytes(out, "utf-8")
    except:
        pass
    return out


class TestDescribe(TestCase):
    def setUp(self):
        extract = b"""Datetime,GROUNDWATER,INTERFLOW,SURFACE,TOTAL OUTFLOW
1976-01-01 12:00:00,11.4047,0,0.0174039,11.4221
1976-01-02 00:00:00,11.2878,0,0,11.2878
1976-01-02 12:00:00,11.1592,0,0,11.1592
1976-01-03 00:00:00,11.0433,0,0,11.0433
1976-01-03 12:00:00,10.9179,0,0,10.9179
1976-01-04 00:00:00,10.8046,0,0,10.8046
1976-01-04 12:00:00,10.6823,0,0,10.6823
1976-01-05 00:00:00,10.5716,0,0,10.5716
1976-01-05 12:00:00,10.4523,0,0,10.4523
1976-01-06 00:00:00,10.3441,0,0,10.3441
1976-01-06 12:00:00,10.2278,0,0,10.2278
1976-01-07 00:00:00,10.1219,0,0,10.1219
1976-01-07 12:00:00,10.0085,0,0,10.0085
1976-01-08 00:00:00,9.905,0,0,9.905
1976-01-08 12:00:00,9.79434,0,0,9.79434
1976-01-09 00:00:00,9.69315,0,0,9.69315
1976-01-09 12:00:00,9.58518,0,0,9.58518
1976-01-10 00:00:00,9.48622,0,0,9.48622
1976-01-10 12:00:00,9.38086,0,0,9.38086
1976-01-11 00:00:00,9.28409,0,0,9.28409
1976-01-11 12:00:00,9.18126,0,0,9.18126
1976-01-12 00:00:00,9.18061,0,0.0122835,9.1929
1976-01-12 12:00:00,9.11522,0,0,9.11522
1976-01-13 00:00:00,9.32981,0,0.15018,9.47999
1976-01-13 12:00:00,9.34197,0,0.203775,9.54575
1976-01-14 00:00:00,10.4385,0,0.380274,10.8187
1976-01-14 12:00:00,10.4229,0,0.0531978,10.4761
1976-01-15 00:00:00,11.7787,0.033321,0.756801,12.5688
1976-01-15 12:00:00,11.8928,0.0338938,0,11.9267
1976-01-16 00:00:00,12.6546,0.0303155,0.779703,13.4646
1976-01-16 12:00:00,12.7404,0.027115,0,12.7676
1976-01-17 00:00:00,12.6078,0.0242524,0,12.632
1976-01-17 12:00:00,12.4635,0.021692,0,12.4852
1976-01-18 00:00:00,12.3338,0.0194019,0,12.3532
1976-01-18 12:00:00,12.1932,0.0173536,0,12.2105
1976-01-19 00:00:00,12.2357,0.0188251,0.0364363,12.291
1976-01-19 12:00:00,12.1335,0.0174167,0,12.1509
1976-01-20 00:00:00,12.0074,0.015578,0,12.023
1976-01-20 12:00:00,11.8708,0.0139334,0,11.8847
1976-01-21 00:00:00,11.9734,0.0124624,0.14222,12.1281
1976-01-21 12:00:00,11.9008,0.0111467,0,11.912
1976-01-22 00:00:00,11.7773,0.00996992,0,11.7873
1976-01-22 12:00:00,11.6616,0.00978101,0.215345,11.8867
1976-01-23 00:00:00,13.4909,0.0447231,0.806954,14.3425
1976-01-23 12:00:00,13.5842,0.0428549,0.565389,14.1924
1976-01-24 00:00:00,16.4947,0.0598848,1.90708,18.4617
1976-01-24 12:00:00,16.7213,0.0552669,0,16.7765
1976-01-25 00:00:00,17.4213,0.0494322,0.573529,18.0442
1976-01-25 12:00:00,17.3532,0.0442135,0,17.3974
1976-01-26 00:00:00,17.2462,0.0395458,0.0247581,17.3105
1976-01-26 12:00:00,17.0859,0.0353708,0.635329,17.7566
1976-01-27 00:00:00,19.1108,0.0354611,1.11172,20.258
1976-01-27 12:00:00,19.1109,0.0330182,0.153316,19.2973
1976-01-28 00:00:00,20.5164,0.104081,0.589802,21.2103
1976-01-28 12:00:00,20.5275,0.101794,0.0987141,20.728
1976-01-29 00:00:00,24.1308,0.415222,3.43669,27.9827
1976-01-29 12:00:00,24.7569,0.40735,1.26266,26.4269
1976-01-30 00:00:00,29.7139,0.696856,2.07643,32.4872
1976-01-30 12:00:00,29.8609,0.584016,0,30.4449
1976-01-31 00:00:00,29.535,0.469073,0,30.0041
1976-01-31 12:00:00,29.1438,0.378275,0,29.5221
1976-02-01 00:00:00,28.8265,0.306367,0,29.1329
1976-02-01 12:00:00,28.4474,0.249258,0,28.6966
1976-02-02 00:00:00,28.4322,0.221976,0.163881,28.818
1976-02-02 12:00:00,28.1138,0.184025,4.06983e-05,28.2978
1976-02-03 00:00:00,27.809,0.151094,0,27.9601
1976-02-03 12:00:00,27.45,0.110444,0,27.5605
1976-02-04 00:00:00,27.1531,0.0510441,0,27.2042
1976-02-04 12:00:00,26.8025,0.0456552,0,26.8482
1976-02-05 00:00:00,26.5131,0.0408353,0,26.554
1976-02-05 12:00:00,26.1729,0.0365242,0,26.2095
1976-02-06 00:00:00,25.8909,0.0326682,0,25.9236
1976-02-06 12:00:00,25.5629,0.0292194,3.52492e-05,25.5922
1976-02-07 00:00:00,25.2882,0.0261346,0,25.3143
1976-02-07 12:00:00,24.9701,0.0233755,7.09052e-05,24.9936
1976-02-08 00:00:00,25.8967,0.0396772,0.835586,26.7719
1976-02-08 12:00:00,26.0445,0.0418599,0.146516,26.2328
1976-02-09 00:00:00,29.2388,0.249416,1.98744,31.4757
1976-02-09 12:00:00,29.4881,0.234143,0.422279,30.1446
1976-02-10 00:00:00,31.8234,0.300234,0.525778,32.6494
1976-02-10 12:00:00,31.8034,0.249321,0.0863798,32.1391
1976-02-11 00:00:00,32.3862,0.220926,0.0984537,32.7056
1976-02-11 12:00:00,32.0499,0.178171,0,32.2281
1976-02-12 00:00:00,31.7004,0.14293,0,31.8434
1976-02-12 12:00:00,31.3263,0.115891,0.0353411,31.4776
1976-02-13 00:00:00,31.4425,0.101092,0.0270192,31.5706
1976-02-13 12:00:00,31.056,0.0273605,0,31.0833
1976-02-14 00:00:00,30.7186,0.0235024,0,30.7421
1976-02-14 12:00:00,30.3171,0.0210212,0,30.3381
1976-02-15 00:00:00,30.0853,0.0262589,0.854623,30.9662
1976-02-15 12:00:00,32.8373,0.257135,2.693,35.7874
1976-02-16 00:00:00,36.9127,0.499929,0.415586,37.8282
1976-02-16 12:00:00,37.0856,0.434227,1.40788,38.9277
1976-02-17 00:00:00,47.7995,4.36726,5.90731,58.0741
1976-02-17 12:00:00,48.3601,3.63069,0,51.9908
1976-02-18 00:00:00,47.8157,2.83939,0,50.6551
1976-02-18 12:00:00,47.1236,2.22359,0,49.3472
1976-02-19 00:00:00,46.5948,1.74404,0,48.3389
1976-02-19 12:00:00,45.9435,1.37055,0.0138771,47.328
1976-02-20 00:00:00,45.7587,1.08374,0.0236575,46.8661
1976-02-20 12:00:00,45.1588,0.855641,0,46.0144
1976-02-21 00:00:00,48.3279,1.178,10.7775,60.2835
1976-02-21 12:00:00,58.0798,2.12888,0,60.2087
1976-02-22 00:00:00,57.419,1.66011,0,59.0791
1976-02-22 12:00:00,56.5605,1.29583,0,57.8563
1976-02-23 00:00:00,55.9193,1.01262,0,56.9319
1976-02-23 12:00:00,55.0909,0.792309,4.00218e-05,55.8833
1976-02-24 00:00:00,56.0181,0.688063,0.533902,57.2401
1976-02-24 12:00:00,56.3339,0.60302,2.26409,59.201
1976-02-25 00:00:00,67.9778,1.38826,3.99163,73.3577
1976-02-25 12:00:00,68.5494,1.17744,0.250245,69.9771
1976-02-26 00:00:00,71.6305,1.01098,0.35557,72.9971
1976-02-26 12:00:00,72.0656,0.918539,4.65955,77.6437
1976-02-27 00:00:00,89.3782,2.41707,6.31077,98.106
1976-02-27 12:00:00,91.5056,2.19338,5.76312,99.4621
1976-02-28 00:00:00,110.322,3.90459,5.58077,119.808
1976-02-28 12:00:00,111.087,3.28626,1.32095,115.695
1976-02-29 00:00:00,116.507,2.91221,0.819203,120.239
1976-02-29 12:00:00,114.905,2.27883,0,117.184
1976-03-01 00:00:00,113.527,1.77022,0,115.297
1976-03-01 12:00:00,111.449,1.37572,0,112.825
1976-03-02 00:00:00,110.116,1.06966,0,111.186
1976-03-02 12:00:00,108.121,0.832162,0,108.953
1976-03-03 00:00:00,106.832,0.647817,0,107.48
1976-03-03 12:00:00,104.916,0.504683,0,105.421
1976-03-04 00:00:00,103.67,0.393508,0,104.064
1976-03-04 12:00:00,101.829,0.307119,0,102.137
1976-03-05 00:00:00,100.625,0.239959,0,100.865
1976-03-05 12:00:00,98.8566,0.187719,0,99.0443
1976-03-06 00:00:00,97.6915,0.147059,0,97.8385
1976-03-06 12:00:00,96.0028,0.11561,0.03801,96.1564
1976-03-07 00:00:00,96.3384,0.0968153,0.195147,96.6303
1976-03-07 12:00:00,95.1215,0.0755395,0.250857,95.4479
1976-03-08 00:00:00,99.572,0.165944,0.947411,100.685
1976-03-08 12:00:00,98.9929,0.155351,0,99.1483
1976-03-09 00:00:00,98.1771,0.134503,0.0672009,98.3788
1976-03-09 12:00:00,96.8389,0.119216,0.672506,97.6306
1976-03-10 00:00:00,105.562,0.53454,2.19452,108.291
1976-03-10 12:00:00,105.331,0.486255,0.192363,106.01
1976-03-11 00:00:00,107.297,0.44185,0.137219,107.876
1976-03-11 12:00:00,105.939,0.369637,0.906292,107.214
1976-03-12 00:00:00,130.452,8.11234,13.0716,151.636
1976-03-12 12:00:00,165.75,29.9728,2.43981,198.162
1976-03-13 00:00:00,190.373,64.2117,7.68781,262.272
1976-03-13 12:00:00,194.811,54.826,1.12296,250.76
1976-03-14 00:00:00,225.52,55.8242,1.12671,282.471
1976-03-14 12:00:00,226.734,45.0476,2.34108,274.123
1976-03-15 00:00:00,253.513,46.4307,0.323189,300.267
1976-03-15 12:00:00,252.825,37.5018,2.3721,292.698
1976-03-16 00:00:00,260.66,30.592,4.51333,295.766
1976-03-16 12:00:00,259.199,25.3092,1.1845,285.692
1976-03-17 00:00:00,291.845,32.2774,6.85756,330.98
1976-03-17 12:00:00,288.827,25.8116,3.74854,318.388
1976-03-18 00:00:00,303.161,24.0858,9.22893,336.476
1976-03-18 12:00:00,300.647,19.7539,12.8183,333.219
1976-03-19 00:00:00,316.346,19.3212,6.0157,341.683
1976-03-19 12:00:00,310.807,15.2337,0.373335,326.414
1976-03-20 00:00:00,309.229,12.0407,0.443292,321.713
1976-03-20 12:00:00,301.928,9.40377,0,311.331
1976-03-21 00:00:00,297.887,7.33948,0,305.227
1976-03-21 12:00:00,290.563,5.73465,0,296.298
1976-03-22 00:00:00,286.587,4.48633,0,291.073
1976-03-22 12:00:00,279.547,3.5147,0,283.062
1976-03-23 00:00:00,275.616,2.75791,0,278.374
1976-03-23 12:00:00,268.799,2.16795,0,270.967
1976-03-24 00:00:00,264.952,1.70763,0,266.66
1976-03-24 12:00:00,258.356,1.34807,0,259.705
1976-03-25 00:00:00,254.524,1.06689,0,255.591
1976-03-25 12:00:00,248.149,0.846686,0,248.996
1976-03-26 00:00:00,244.394,0.673979,0,245.068
1976-03-26 12:00:00,238.533,0.549096,0.133828,239.216
1976-03-27 00:00:00,238.126,0.568327,0.888448,239.583
1976-03-27 12:00:00,233.87,0.517133,0,234.387
1976-03-28 00:00:00,230.418,0.422878,0,230.841
1976-03-28 12:00:00,224.777,0.347513,0,225.125
1976-03-29 00:00:00,221.548,0.290878,0.129158,221.968
1976-03-29 12:00:00,221.839,0.486648,1.2997,223.625
1976-03-30 00:00:00,240.938,10.5376,21.4093,272.885
1976-03-30 12:00:00,301.001,97.1618,8.82321,406.986
1976-03-31 00:00:00,311.371,83.6426,0,395.013
1976-03-31 12:00:00,304.855,65.3341,0,370.189
1976-04-01 00:00:00,301.598,51.0949,0,352.693
1976-04-01 12:00:00,294.821,40.0138,0,334.834
1976-04-02 00:00:00,291.163,31.3844,0,322.548
1976-04-02 12:00:00,283.929,24.6589,0,308.588
1976-04-03 00:00:00,279.425,19.4126,0,298.838
1976-04-03 12:00:00,271.831,15.3159,0,287.147
1976-04-04 00:00:00,267.197,12.1131,0,279.31
1976-04-04 12:00:00,260.062,9.60596,0,269.668
1976-04-05 00:00:00,255.589,7.64035,0,263.229
1976-04-05 12:00:00,248.563,6.09672,0,254.66
1976-04-06 00:00:00,244.023,4.88218,0,248.905
1976-04-06 12:00:00,237.099,3.92455,0,241.023
1976-04-07 00:00:00,232.565,3.16769,0,235.732
1976-04-07 12:00:00,225.71,2.56794,0,228.278
1976-04-08 00:00:00,221.138,2.09131,0,223.229
1976-04-08 12:00:00,214.995,1.71133,0,216.706
1976-04-09 00:00:00,210.443,1.40735,0,211.85
1976-04-09 12:00:00,204.533,1.16325,0,205.696
1976-04-10 00:00:00,200.517,0.966458,0,201.483
1976-04-10 12:00:00,193.965,0.807115,0,194.772
1976-04-11 00:00:00,188.663,0.677513,0,189.34
1976-04-11 12:00:00,183.188,0.586731,0.111885,183.886
1976-04-12 00:00:00,179.258,0.500595,0,179.759
1976-04-12 12:00:00,174.513,0.427114,0,174.94
1976-04-13 00:00:00,170.705,0.366041,0,171.071
1976-04-13 12:00:00,165.352,0.306742,0,165.659
1976-04-14 00:00:00,160.76,0.246611,0,161.006
1976-04-14 12:00:00,155.507,0.187999,0,155.695
1976-04-15 00:00:00,154.73,2.07149,3.51214,160.314
1976-04-15 12:00:00,175.543,9.55497,2.2409,187.339
1976-04-16 00:00:00,177.096,7.92188,0,185.018
1976-04-16 12:00:00,172.037,6.2616,0,178.298
1976-04-17 00:00:00,167.293,4.96232,0,172.255
1976-04-17 12:00:00,173.418,9.45361,3.73759,186.61
1976-04-18 00:00:00,222.192,28.8208,5.07258,256.086
1976-04-18 12:00:00,298.523,149.264,35.3756,483.163
1976-04-19 00:00:00,317.843,147.312,0,465.155
1976-04-19 12:00:00,311.944,121.809,0,433.753
1976-04-20 00:00:00,308.464,101.241,0,409.705
1976-04-20 12:00:00,300.897,84.6166,0.180478,385.694
1976-04-21 00:00:00,358.374,127.43,7.04178,492.846
1976-04-21 12:00:00,401.658,153.823,2.93833,558.419
1976-04-22 00:00:00,413.515,151.48,0,564.995
1976-04-22 12:00:00,402.483,121.933,0,524.416
1976-04-23 00:00:00,396.093,98.5606,0,494.654
1976-04-23 12:00:00,392.99,113.79,69.2671,576.047
1976-04-24 00:00:00,431.888,224.112,14.0625,670.063
1976-04-24 12:00:00,451.116,227.651,13.394,692.162
1976-04-25 00:00:00,478.905,189.014,1.17993,669.099
1976-04-25 12:00:00,489.028,156.884,12.5019,658.414
1976-04-26 00:00:00,501.029,133.399,0,634.428
1976-04-26 12:00:00,487.381,105.673,0,593.054
1976-04-27 00:00:00,479.986,83.9495,0,563.935
1976-04-27 12:00:00,465.546,66.9011,0,532.447
1976-04-28 00:00:00,457.323,53.4976,0,510.821
1976-04-28 12:00:00,443.05,42.9383,0,485.988
1976-04-29 00:00:00,435.188,34.6008,0,469.788
1976-04-29 12:00:00,421.377,28.0011,0,449.378
1976-04-30 00:00:00,412.932,22.7623,0,435.694
1976-04-30 12:00:00,399.28,18.5912,0,417.872
1976-05-01 00:00:00,391.215,15.2589,0,406.474
1976-05-01 12:00:00,378.443,12.5871,0,391.031
1976-05-02 00:00:00,370.902,10.4365,0,381.339
1976-05-02 12:00:00,395.994,14.5518,5.15397,415.7
1976-05-03 00:00:00,404.854,13.8266,0,418.68
1976-05-03 12:00:00,392.13,11.229,0,403.359
1976-05-04 00:00:00,384.011,9.16206,0,393.173
1976-05-04 12:00:00,371.272,7.51203,0,378.785
1976-05-05 00:00:00,363.465,6.1901,0,369.656
1976-05-05 12:00:00,351.018,5.12693,0,356.145
1976-05-06 00:00:00,343.03,4.26835,0,347.299
1976-05-06 12:00:00,331.013,3.57193,0,334.585
1976-05-07 00:00:00,323.281,3.00444,0,326.286
1976-05-07 12:00:00,312.609,2.53978,0,315.149
1976-05-08 00:00:00,305.994,2.15741,0,308.152
1976-05-08 12:00:00,296.216,1.84116,0,298.057
1976-05-09 00:00:00,289.682,1.57824,0,291.26
1976-05-09 12:00:00,279.579,1.35853,0,280.937
1976-05-10 00:00:00,272.673,1.17399,0,273.847
1976-05-10 12:00:00,263.073,1.01819,0,264.091
1976-05-11 00:00:00,256.799,0.886021,0,257.685
1976-05-11 12:00:00,247.904,0.773368,0,248.677
1976-05-12 00:00:00,241.892,0.676917,0,242.569
1976-05-12 12:00:00,233.603,0.593985,0,234.197
1976-05-13 00:00:00,228.155,0.473469,0.0411935,228.67
1976-05-13 12:00:00,246.724,1.85518,8.35074,256.93
1976-05-14 00:00:00,260.037,2.33804,0,262.375
1976-05-14 12:00:00,253.118,1.91982,0,255.038
1976-05-15 00:00:00,248.95,1.58439,0,250.534
1976-05-15 12:00:00,242.551,1.33572,0.361054,244.248
1976-05-16 00:00:00,243.405,1.21247,0.164699,244.782
1976-05-16 12:00:00,255.553,3.24075,13.7303,272.524
1976-05-17 00:00:00,310.161,13.6244,2.96351,326.749
1976-05-17 12:00:00,308.083,10.9618,0,319.045
1976-05-18 00:00:00,302.013,8.64288,0,310.656
1976-05-18 12:00:00,292.336,6.83063,0,299.167
1976-05-19 00:00:00,286.039,5.41253,0,291.451
1976-05-19 12:00:00,276.352,4.30124,0,280.653
1976-05-20 00:00:00,269.731,3.42896,0,273.161
1976-05-20 12:00:00,260.089,2.74303,0,262.832
1976-05-21 00:00:00,253.29,2.20253,0,255.492
1976-05-21 12:00:00,244.309,1.77564,0,246.084
1976-05-22 00:00:00,238.556,1.43764,0,239.994
1976-05-22 12:00:00,231.2,1.21786,2.04715,234.465
1976-05-23 00:00:00,252.327,2.41236,3.99364,258.733
1976-05-23 12:00:00,265.754,2.65552,1.31335,269.723
1976-05-24 00:00:00,266.154,2.37926,0.611496,269.145
1976-05-24 12:00:00,259.57,2.04973,0,261.62
1976-05-25 00:00:00,255.03,1.75653,0,256.786
1976-05-25 12:00:00,247.062,1.51161,0,248.574
1976-05-26 00:00:00,241.513,1.30594,0,242.819
1976-05-26 12:00:00,233.442,1.13238,0,234.574
1976-05-27 00:00:00,227.888,0.985185,0,228.873
1976-05-27 12:00:00,220.168,0.859761,0,221.028
1976-05-28 00:00:00,214.917,0.752406,0,215.669
1976-05-28 12:00:00,207.625,0.660124,0,208.285
1976-05-29 00:00:00,204.575,1.48217,2.49634,208.554
1976-05-29 12:00:00,232.885,14.674,3.61288,251.172
1976-05-30 00:00:00,241.563,16.9916,0,258.555
1976-05-30 12:00:00,234.732,13.2111,0,247.943
1976-05-31 00:00:00,230.351,10.2775,0,240.629
1976-05-31 12:00:00,223.732,8.00054,0,231.733
1976-06-01 00:00:00,219.54,6.2326,0,225.773
1976-06-01 12:00:00,213.221,4.85942,0,218.081
1976-06-02 00:00:00,209.112,3.79241,0,212.904
1976-06-02 12:00:00,202.855,2.96292,0,205.818
1976-06-03 00:00:00,198.457,2.31773,0,200.774
1976-06-03 12:00:00,192.021,1.81557,0,193.836
1976-06-04 00:00:00,187.232,1.42446,0,188.657
1976-06-04 12:00:00,180.772,1.1196,0,181.892
1976-06-05 00:00:00,176.034,0.881739,0,176.916
1976-06-05 12:00:00,169.784,0.695963,0,170.48
1976-06-06 00:00:00,165.104,0.550692,0,165.655
1976-06-06 12:00:00,159.228,0.436941,0,159.665
1976-06-07 00:00:00,154.958,0.347734,0,155.306
1976-06-07 12:00:00,149.549,0.277655,0,149.827
1976-06-08 00:00:00,145.528,0.222496,0,145.751
1976-06-08 12:00:00,140.404,0.178985,0,140.583
1976-06-09 00:00:00,136.458,0.144582,0,136.602
1976-06-09 12:00:00,131.266,0.117305,0,131.383
1976-06-10 00:00:00,126.863,0.055253,0,126.918
1976-06-10 12:00:00,137.155,6.97958,2.26663,146.401
1976-06-11 00:00:00,146.622,9.50613,0,156.128
1976-06-11 12:00:00,142.247,7.5783,0,149.825
1976-06-12 00:00:00,139.352,6.06232,0,145.415
1976-06-12 12:00:00,134.536,4.86776,0,139.404
1976-06-13 00:00:00,134.237,6.63848,0.634721,141.51
1976-06-13 12:00:00,139.324,10.9815,0,150.305
1976-06-14 00:00:00,155.497,19.3295,3.22537,178.052
1976-06-14 12:00:00,179.732,28.2942,0.00318973,208.029
1976-06-15 00:00:00,176.534,22.3786,0.00310246,198.916
1976-06-15 12:00:00,173.048,17.816,0.496424,191.361
1976-06-16 00:00:00,169.263,14.1807,0,183.444
1976-06-16 12:00:00,164.097,11.3224,0,175.419
1976-06-17 00:00:00,160.655,9.07273,0,169.727
1976-06-17 12:00:00,155.618,7.29819,0,162.916
1976-06-18 00:00:00,151.563,5.89509,0,157.458
1976-06-18 12:00:00,146.917,4.78298,0.00223283,151.703
1976-06-19 00:00:00,143.836,3.8985,0,147.735
1976-06-19 12:00:00,139.329,3.19291,0,142.522
1976-06-20 00:00:00,135.987,2.62809,0,138.615
1976-06-20 12:00:00,131.471,2.17423,0,133.645
1976-06-21 00:00:00,127.757,1.80804,0,129.565
1976-06-21 12:00:00,123.356,1.51132,0,124.867
1976-06-22 00:00:00,120.087,1.26978,0,121.357
1976-06-22 12:00:00,115.95,1.07222,0,117.022
1976-06-23 00:00:00,112.56,0.909829,0,113.47
1976-06-23 12:00:00,108.488,0.775672,0,109.264
1976-06-24 00:00:00,105.19,0.664267,0,105.854
1976-06-24 12:00:00,104.43,2.76673,2.66232,109.859
1976-06-25 00:00:00,116.807,9.69211,1.82574,128.325
1976-06-25 12:00:00,114.761,7.60383,0,122.365
1976-06-26 00:00:00,111.922,5.93748,0,117.859
1976-06-26 12:00:00,108.591,4.6417,0,113.232
1976-06-27 00:00:00,106.724,3.95708,0.886859,111.568
1976-06-27 12:00:00,110.301,4.37662,0.0188776,114.696
1976-06-28 00:00:00,113.079,4.39821,1.69463,119.172
1976-06-28 12:00:00,126.52,6.91131,1.30063,134.732
1976-06-29 00:00:00,129.589,6.58155,0,136.171
1976-06-29 12:00:00,125.963,5.11984,0,131.083
1976-06-30 00:00:00,123.18,3.98529,0,127.166
1976-06-30 12:00:00,119.436,3.10442,0,122.54
1976-07-01 00:00:00,116.596,2.42026,0,119.016
1976-07-01 12:00:00,113.011,1.88867,0,114.9
1976-07-02 00:00:00,110.202,1.47543,0,111.677
1976-07-02 12:00:00,107.083,1.15402,0,108.237
1976-07-03 00:00:00,105.066,0.903874,0,105.97
1976-07-03 12:00:00,101.755,0.709061,0,102.464
1976-07-04 00:00:00,98.3716,0.557218,0,98.9288
1976-07-04 12:00:00,94.8367,0.438758,0,95.2755
1976-07-05 00:00:00,92.3122,0.346245,0,92.6585
1976-07-05 12:00:00,89.2677,0.273911,0,89.5416
1976-07-06 00:00:00,86.7146,0.217279,0,86.9319
1976-07-06 12:00:00,83.47,0.172872,0,83.6428
1976-07-07 00:00:00,80.4373,0.137993,0,80.5753
1976-07-07 12:00:00,77.5088,0.110544,0,77.6194
1976-07-08 00:00:00,75.0651,0.0626949,0,75.1278
1976-07-08 12:00:00,71.9838,0.021825,0,72.0056
1976-07-09 00:00:00,68.9413,0.0195209,0,68.9608
1976-07-09 12:00:00,65.8735,0.01746,0,65.891
1976-07-10 00:00:00,63.3895,0.0156167,0,63.4052
1976-07-10 12:00:00,60.3675,0.013968,0,60.3815
1976-07-11 00:00:00,57.2971,0.0124934,0,57.3096
1976-07-11 12:00:00,54.3643,0.0111744,0,54.3755
1976-07-12 00:00:00,52.0054,0.00999469,0,52.0154
1976-07-12 12:00:00,49.4129,0.00893953,0,49.4218
1976-07-13 00:00:00,46.9314,0.00799576,0,46.9394
1976-07-13 12:00:00,44.3734,0.00485584,0,44.3783
1976-07-14 00:00:00,42.0264,0,0,42.0264
1976-07-14 12:00:00,39.4859,0,0,39.4859
1976-07-15 00:00:00,36.9755,0,0,36.9755
1976-07-15 12:00:00,34.8207,0,0,34.8207
1976-07-16 00:00:00,34.0824,0.230402,0.0156521,34.3285
1976-07-16 12:00:00,32.8418,0.343899,0,33.1857
1976-07-17 00:00:00,30.8638,0.307593,0,31.1714
1976-07-17 12:00:00,28.8627,0.275119,0,29.1379
1976-07-18 00:00:00,26.9795,0.246074,0,27.2256
1976-07-18 12:00:00,25.0841,0.220095,0,25.3042
1976-07-19 00:00:00,23.2652,0.196859,0,23.462
1976-07-19 12:00:00,21.8481,0.176076,0,22.0242
1976-07-20 00:00:00,21.002,0.157488,0,21.1595
1976-07-20 12:00:00,19.9973,0.146666,0.210088,20.3541
1976-07-21 00:00:00,20.0389,0.14523,0.809949,20.994
1976-07-21 12:00:00,20.2729,0.129898,0,20.4028
1976-07-22 00:00:00,19.9716,0.116184,0,20.0878
1976-07-22 12:00:00,19.6342,0.103918,0,19.7381
1976-07-23 00:00:00,19.1365,0.0929474,0,19.2294
1976-07-23 12:00:00,18.1839,0.0831346,0,18.267
1976-07-24 00:00:00,17.0324,0.0743579,0,17.1068
1976-07-24 12:00:00,15.5121,0.0665077,0,15.5786
1976-07-25 00:00:00,13.6338,0.0594863,0,13.6933
1976-07-25 12:00:00,11.9315,0.0532062,0,11.9847
1976-07-26 00:00:00,10.4293,0.0475891,0,10.4769
1976-07-26 12:00:00,9.55094,0.0762564,0.287097,9.91429
1976-07-27 00:00:00,9.58382,0.117793,0,9.70161
1976-07-27 12:00:00,8.7702,0.105357,0,8.87555
1976-07-28 00:00:00,7.71834,0.190222,0.399593,8.30816
1976-07-28 12:00:00,14.8248,6.10387,2.5717,23.5003
1976-07-29 00:00:00,16.2273,5.68423,0,21.9115
1976-07-29 12:00:00,15.8034,4.73389,0,20.5373
1976-07-30 00:00:00,14.9585,3.96282,0,18.9213
1976-07-30 12:00:00,13.8174,3.33431,0,17.1517
1976-07-31 00:00:00,12.674,2.82523,0.153555,15.6528
1976-07-31 12:00:00,12.4648,2.40936,0,14.8741
1976-08-01 00:00:00,12.2791,2.0557,0,14.3348
1976-08-01 12:00:00,11.8366,1.76176,0,13.5984
1976-08-02 00:00:00,10.7189,1.51619,0,12.2351
1976-08-02 12:00:00,9.56799,1.30997,0,10.878
1976-08-03 00:00:00,8.48018,1.13593,0,9.61612
1976-08-03 12:00:00,7.4049,0.988318,0,8.39322
1976-08-04 00:00:00,6.3458,0.862531,0,7.20833
1976-08-04 12:00:00,5.23073,0.754858,0,5.98559
1976-08-05 00:00:00,4.03485,0.662297,0,4.69714
1976-08-05 12:00:00,2.94257,0.556958,0,3.49952
1976-08-06 00:00:00,2.03477,0.46329,0,2.49806
1976-08-06 12:00:00,1.40161,0.414379,0,1.81599
1976-08-07 00:00:00,0.72693,0.370632,0,1.09756
1976-08-07 12:00:00,0.400775,0.331504,0,0.732278
1976-08-08 00:00:00,0.238161,0.296506,0,0.534667
1976-08-08 12:00:00,0.0573046,0.265203,0,0.322508
1976-08-09 00:00:00,0,0.237205,0,0.237205
1976-08-09 12:00:00,0,0.212162,0,0.212162
1976-08-10 00:00:00,0,0.189764,0,0.189764
1976-08-10 12:00:00,0,0.16973,0,0.16973
1976-08-11 00:00:00,0,0.151811,0,0.151811
1976-08-11 12:00:00,0,0.135784,0,0.135784
1976-08-12 00:00:00,0,0.121449,0,0.121449
1976-08-12 12:00:00,0,0.108627,0,0.108627
1976-08-13 00:00:00,0,0.097159,0,0.097159
1976-08-13 12:00:00,0,0.0869017,0,0.0869017
1976-08-14 00:00:00,0,0.0777272,0,0.0777272
1976-08-14 12:00:00,0.137763,0.0784728,0.140839,0.357075
1976-08-15 00:00:00,0.179898,0.0726659,0,0.252564
1976-08-15 12:00:00,0.0992222,0.0649943,0,0.164216
1976-08-16 00:00:00,0,0.0581327,0,0.0581327
1976-08-16 12:00:00,0,0.0519955,0,0.0519955
1976-08-17 00:00:00,0,0.0465062,0,0.0465062
1976-08-17 12:00:00,1.16043,0.723416,0.0538879,1.93774
1976-08-18 00:00:00,1.22711,0.678419,0,1.90553
1976-08-18 12:00:00,1.13121,0.606796,0,1.73801
1976-08-19 00:00:00,0.902766,0.542735,0,1.4455
1976-08-19 12:00:00,0.671158,0.485437,0,1.1566
1976-08-20 00:00:00,0.438616,0.434188,0,0.872804
1976-08-20 12:00:00,0.21634,0.38835,0,0.60469
1976-08-21 00:00:00,0.0287419,0.34735,0,0.376092
1976-08-21 12:00:00,0,0.31068,0,0.31068
1976-08-22 00:00:00,0,0.27788,0,0.27788
1976-08-22 12:00:00,0,0.248544,0,0.248544
1976-08-23 00:00:00,0,0.222304,0,0.222304
1976-08-23 12:00:00,0,0.198835,0,0.198835
1976-08-24 00:00:00,0,0.177843,0,0.177843
1976-08-24 12:00:00,0,0.159068,0,0.159068
1976-08-25 00:00:00,0,0.142275,0,0.142275
1976-08-25 12:00:00,0,0.127254,0,0.127254
1976-08-26 00:00:00,1.27228,1.01155,0.311182,2.59501
1976-08-26 12:00:00,1.57614,1.03863,0.00997189,2.62473
1976-08-27 00:00:00,1.55869,0.929359,0,2.48805
1976-08-27 12:00:00,1.33417,0.831244,0,2.16542
1976-08-28 00:00:00,1.05125,0.743487,0,1.79474
1976-08-28 12:00:00,0.771201,0.664995,0,1.4362
1976-08-29 00:00:00,0.494818,0.59479,0,1.08961
1976-08-29 12:00:00,0.273097,0.531996,0,0.805093
1976-08-30 00:00:00,0.109698,0.475832,0,0.58553
1976-08-30 12:00:00,0.00175713,0.425597,0,0.427354
1976-08-31 00:00:00,0,0.380665,0,0.380665
1976-08-31 12:00:00,0,0.340478,0,0.340478
1976-09-01 00:00:00,0,0.304532,0,0.304532
1976-09-01 12:00:00,0,0.272382,0,0.272382
1976-09-02 00:00:00,0,0.243626,0,0.243626
1976-09-02 12:00:00,0,0.217906,0,0.217906
1976-09-03 00:00:00,0,0.194901,0,0.194901
1976-09-03 12:00:00,0,0.174325,0,0.174325
1976-09-04 00:00:00,0,0.155921,0,0.155921
1976-09-04 12:00:00,0,0.13946,0,0.13946
1976-09-05 00:00:00,0,0.124737,0,0.124737
1976-09-05 12:00:00,0,0.111568,0,0.111568
1976-09-06 00:00:00,0,0.0997892,0,0.0997892
1976-09-06 12:00:00,0,0.0892541,0,0.0892541
1976-09-07 00:00:00,0,0.0798313,0,0.0798313
1976-09-07 12:00:00,0,0.0714033,0,0.0714033
1976-09-08 00:00:00,0,0.0638651,0,0.0638651
1976-09-08 12:00:00,0,0.0571226,0,0.0571226
1976-09-09 00:00:00,0,0.051092,0,0.051092
1976-09-09 12:00:00,0,0.0456981,0,0.0456981
1976-09-10 00:00:00,0,0.0408736,0,0.0408736
1976-09-10 12:00:00,0,0.0365585,0,0.0365585
1976-09-11 00:00:00,0,0.0326989,0,0.0326989
1976-09-11 12:00:00,0,0.0292468,0,0.0292468
1976-09-12 00:00:00,0,0.0261591,0,0.0261591
1976-09-12 12:00:00,0,0.0233974,0,0.0233974
1976-09-13 00:00:00,0,0.0209273,0,0.0209273
1976-09-13 12:00:00,0,0.018718,0,0.018718
1976-09-14 00:00:00,0,0.0167418,0,0.0167418
1976-09-14 12:00:00,0,0.0149744,0,0.0149744
1976-09-15 00:00:00,0,0.0133935,0,0.0133935
1976-09-15 12:00:00,0,0.0119795,0,0.0119795
1976-09-16 00:00:00,0,0.0107148,0,0.0107148
1976-09-16 12:00:00,0,0.00958359,0,0.00958359
1976-09-17 00:00:00,0,0.00857183,0,0.00857183
1976-09-17 12:00:00,0,0.00766688,0,0.00766688
1976-09-18 00:00:00,0,0.00207972,0,0.00207972
1976-09-18 12:00:00,0,0,0,0
1976-09-19 00:00:00,0,0,0,0
1976-09-19 12:00:00,0.492579,0.1306,0.222168,0.845347
1976-09-20 00:00:00,1.07841,0.242179,0,1.32059
1976-09-20 12:00:00,1.0276,0.216612,0,1.24421
1976-09-21 00:00:00,0.801934,0.193744,0,0.995678
1976-09-21 12:00:00,0.59581,0.173289,0,0.769099
1976-09-22 00:00:00,0.420915,0.154995,0,0.57591
1976-09-22 12:00:00,0.301937,0.138631,0,0.440569
1976-09-23 00:00:00,0.174275,0.123996,0,0.298271
1976-09-23 12:00:00,0.0372202,0.110905,0,0.148125
1976-09-24 00:00:00,0,0.0991966,0,0.0991966
1976-09-24 12:00:00,0,0.0887242,0,0.0887242
1976-09-25 00:00:00,0,0.0793573,0,0.0793573
1976-09-25 12:00:00,0,0.0709794,0,0.0709794
1976-09-26 00:00:00,0,0.0634859,0,0.0634859
1976-09-26 12:00:00,0,0.0567835,0,0.0567835
1976-09-27 00:00:00,0,0.0507887,0,0.0507887
1976-09-27 12:00:00,0.00645098,0.0454268,0.0062022,0.05808
1976-09-28 00:00:00,0.0177677,0.040631,0,0.0583987
1976-09-28 12:00:00,0.0175891,0.0363414,0,0.0539306
1976-09-29 00:00:00,0.0174123,0.0325048,0,0.0499171
1976-09-29 12:00:00,0.0172373,0.0290731,0,0.0463104
1976-09-30 00:00:00,0.0104919,0.0260038,0,0.0364957
1976-09-30 12:00:00,0,0.0232585,0,0.0232585
1976-10-01 00:00:00,0,0.0208031,0,0.0208031
1976-10-01 12:00:00,0,0.0186068,0,0.0186068
1976-10-02 00:00:00,0,0.0166424,0,0.0166424
1976-10-02 12:00:00,0,0.0148855,0,0.0148855
1976-10-03 00:00:00,0,0.0133139,0,0.0133139
1976-10-03 12:00:00,0,0.0119084,0,0.0119084
1976-10-04 00:00:00,0,0.0106512,0,0.0106512
1976-10-04 12:00:00,0.0673727,0.013606,0.158275,0.239254
1976-10-05 00:00:00,0.372994,0.0235223,0.300753,0.697269
1976-10-05 12:00:00,0.557418,0.0227496,0.0677946,0.647962
1976-10-06 00:00:00,0.500115,0.0203478,0,0.520463
1976-10-06 12:00:00,0.438519,0.0181997,0,0.456719
1976-10-07 00:00:00,0.428355,0.0162783,0,0.444633
1976-10-07 12:00:00,0.406022,0.0145597,0,0.420581
1976-10-08 00:00:00,0.103911,0.0130226,0,0.116933
1976-10-08 12:00:00,0,0.0116478,0,0.0116478
1976-10-09 00:00:00,0,0.0104181,0,0.0104181
1976-10-09 12:00:00,0,0.00931823,0,0.00931823
1976-10-10 00:00:00,0,0.00833448,0,0.00833448
1976-10-10 12:00:00,0,0.00745458,0,0.00745458
1976-10-11 00:00:00,0,0.000292921,0,0.000292921
1976-10-11 12:00:00,0,0,0,0
1976-10-12 00:00:00,0,0,0,0
1976-10-12 12:00:00,0,0,0,0
1976-10-13 00:00:00,0,0,0,0
1976-10-13 12:00:00,0,0,0,0
1976-10-14 00:00:00,0,0,0,0
1976-10-14 12:00:00,0,0,0,0
1976-10-15 00:00:00,0,0,0,0
1976-10-15 12:00:00,0,0,0,0
1976-10-16 00:00:00,0,0,0,0
1976-10-16 12:00:00,0,0,0,0
1976-10-17 00:00:00,0,0,0,0
1976-10-17 12:00:00,0,0,0,0
1976-10-18 00:00:00,0,0,0,0
1976-10-18 12:00:00,0,0,0,0
1976-10-19 00:00:00,0.00539727,0,0.00722981,0.0126271
1976-10-19 12:00:00,0.0793362,0,0.186406,0.265742
1976-10-20 00:00:00,0.221017,0,0,0.221017
1976-10-20 12:00:00,0.218781,0,0,0.218781
1976-10-21 00:00:00,0.216578,0,0,0.216578
1976-10-21 12:00:00,0.214387,0,0,0.214387
1976-10-22 00:00:00,0.174727,0,0,0.174727
1976-10-22 12:00:00,0.154858,0,0,0.154858
1976-10-23 00:00:00,0.0879515,0,0,0.0879515
1976-10-23 12:00:00,0.0612252,0,0,0.0612252
1976-10-24 00:00:00,0.309738,0.0167488,1.35952,1.68601
1976-10-24 12:00:00,1.09568,0.0662938,0.200643,1.36261
1976-10-25 00:00:00,1.15074,0.0636931,0,1.21443
1976-10-25 12:00:00,1.13867,0.0569688,1.7404e-06,1.19564
1976-10-26 00:00:00,1.12707,0.0509544,0,1.17803
1976-10-26 12:00:00,1.11513,0.045575,0,1.16071
1976-10-27 00:00:00,1.10377,0.0407636,0,1.14454
1976-10-27 12:00:00,1.0921,0.03646,0,1.12856
1976-10-28 00:00:00,1.08098,0.0326108,0,1.11359
1976-10-28 12:00:00,1.06956,0.029168,0,1.09873
1976-10-29 00:00:00,1.04164,0.0260887,0,1.06773
1976-10-29 12:00:00,0.990162,0.0233344,0,1.0135
1976-10-30 00:00:00,0.923446,0.0208709,0,0.944317
1976-10-30 12:00:00,0.977596,0.0201098,0.222987,1.22069
1976-10-31 00:00:00,1.40002,0.027043,0.198776,1.62583
1976-10-31 12:00:00,1.42428,0.0246142,0,1.4489
1976-11-01 00:00:00,1.40982,0.0220156,0,1.43184
1976-11-01 12:00:00,1.39509,0.0196914,0,1.41478
1976-11-02 00:00:00,1.38093,0.0176125,0,1.39854
1976-11-02 12:00:00,1.36625,0.0157531,0,1.38201
1976-11-03 00:00:00,1.30798,0.01409,0,1.32207
1976-11-03 12:00:00,1.25914,0.0126025,0,1.27175
1976-11-04 00:00:00,1.20911,0.011272,0,1.22039
1976-11-04 12:00:00,1.18434,0.010082,0,1.19442
1976-11-05 00:00:00,1.13601,0.0090176,0,1.14503
1976-11-05 12:00:00,1.11261,0.00806559,0,1.12067
1976-11-06 00:00:00,1.05093,0.0054853,0,1.05642
1976-11-06 12:00:00,1.01722,0,0,1.01722
1976-11-07 00:00:00,0.984789,0,0,0.984789
1976-11-07 12:00:00,0.972044,0,0,0.972044
1976-11-08 00:00:00,0.948533,0,0,0.948533
1976-11-08 12:00:00,0.934954,0,0,0.934954
1976-11-09 00:00:00,0.90357,0,0,0.90357
1976-11-09 12:00:00,0.868084,0,0,0.868084
1976-11-10 00:00:00,0.845698,0,0,0.845698
1976-11-10 12:00:00,0.835918,0,0,0.835918
1976-11-11 00:00:00,0.818123,0,0,0.818123
1976-11-11 12:00:00,0.807218,0,0,0.807218
1976-11-12 00:00:00,0.799057,0,0,0.799057
1976-11-12 12:00:00,0.790838,0,0,0.790838
1976-11-13 00:00:00,0.782844,0,0,0.782844
1976-11-13 12:00:00,0.774797,0,0,0.774797
1976-11-14 00:00:00,0.762318,0,0,0.762318
1976-11-14 12:00:00,0.753422,0,0,0.753422
1976-11-15 00:00:00,0.72238,0,0,0.72238
1976-11-15 12:00:00,0.705697,0,0,0.705697
1976-11-16 00:00:00,0.649529,0,0,0.649529
1976-11-16 12:00:00,0.62694,0,0,0.62694
1976-11-17 00:00:00,0.558348,0,0,0.558348
1976-11-17 12:00:00,0.522988,0,0,0.522988
1976-11-18 00:00:00,0.446124,0,0,0.446124
1976-11-18 12:00:00,0.42098,0,0,0.42098
1976-11-19 00:00:00,0.395642,0,0,0.395642
1976-11-19 12:00:00,0.384279,0,0,0.384279
1976-11-20 00:00:00,0.359338,0,0,0.359338
1976-11-20 12:00:00,0.349371,0,0,0.349371
1976-11-21 00:00:00,0.339637,0,0,0.339637
1976-11-21 12:00:00,0.333885,0,0,0.333885
1976-11-22 00:00:00,0.330519,0,0,0.330519
1976-11-22 12:00:00,0.327156,0,0,0.327156
1976-11-23 00:00:00,0.323858,0,0,0.323858
1976-11-23 12:00:00,0.320209,0,0,0.320209
1976-11-24 00:00:00,0.29703,0,0,0.29703
1976-11-24 12:00:00,0.284364,0,0,0.284364
1976-11-25 00:00:00,0.25574,0,0,0.25574
1976-11-25 12:00:00,0.235457,0,0,0.235457
1976-11-26 00:00:00,0.223963,0,0,0.223963
1976-11-26 12:00:00,0.219413,0,0,0.219413
1976-11-27 00:00:00,0.217204,0,0,0.217204
1976-11-27 12:00:00,0.215009,0,0,0.215009
1976-11-28 00:00:00,0.212845,0,0,0.212845
1976-11-28 12:00:00,0.210694,0,0,0.210694
1976-11-29 00:00:00,0.208573,0,0,0.208573
1976-11-29 12:00:00,0.206466,0,0,0.206466
1976-11-30 00:00:00,0.204388,0,0,0.204388
1976-11-30 12:00:00,0.202323,0,0,0.202323
1976-12-01 00:00:00,0.200287,0,0,0.200287
1976-12-01 12:00:00,0.198264,0,0,0.198264
1976-12-02 00:00:00,0.196269,0,0,0.196269
1976-12-02 12:00:00,0.194287,0,0,0.194287
1976-12-03 00:00:00,0.192332,0,0,0.192332
1976-12-03 12:00:00,0.19039,0,0,0.19039
1976-12-04 00:00:00,0.188474,0,0,0.188474
1976-12-04 12:00:00,0.186571,0,0,0.186571
1976-12-05 00:00:00,0.184694,0,0,0.184694
1976-12-05 12:00:00,0.182829,0,0,0.182829
1976-12-06 00:00:00,0.18099,0,0,0.18099
1976-12-06 12:00:00,0.179163,0,0,0.179163
1976-12-07 00:00:00,0.17736,0,0,0.17736
1976-12-07 12:00:00,0.17557,0,0,0.17557
1976-12-08 00:00:00,0.173804,0,0,0.173804
1976-12-08 12:00:00,0.17205,0,0,0.17205
1976-12-09 00:00:00,0.170319,0,0,0.170319
1976-12-09 12:00:00,0.1686,0,0,0.1686
1976-12-10 00:00:00,0.166904,0,0,0.166904
1976-12-10 12:00:00,0.16522,0,0,0.16522
1976-12-11 00:00:00,0.163558,0,0,0.163558
1976-12-11 12:00:00,0.161909,0,0,0.161909
1976-12-12 00:00:00,0.16028,0,0,0.16028
1976-12-12 12:00:00,0.158663,0,0,0.158663
1976-12-13 00:00:00,0.157067,0,0,0.157067
1976-12-13 12:00:00,0.155483,0,0,0.155483
1976-12-14 00:00:00,0.153609,0,0,0.153609
1976-12-14 12:00:00,0.151932,0,0,0.151932
1976-12-15 00:00:00,0.149631,0,0,0.149631
1976-12-15 12:00:00,0.147896,0,0,0.147896
1976-12-16 00:00:00,0.14576,0,0,0.14576
1976-12-16 12:00:00,0.14396,0,0,0.14396
1976-12-17 00:00:00,0.141041,0,0,0.141041
1976-12-17 12:00:00,0.137998,0,0,0.137998
1976-12-18 00:00:00,0.135539,0,0,0.135539
1976-12-18 12:00:00,0.135731,0,0.00950661,0.145237
1976-12-19 00:00:00,0.323548,0,0.123436,0.446984
1976-12-19 12:00:00,0.374626,0,0.0557628,0.430389
1976-12-20 00:00:00,0.53505,0,0.0669894,0.602039
1976-12-20 12:00:00,0.541399,0,2.48422e-06,0.541401
1976-12-21 00:00:00,0.535954,0,0,0.535954
1976-12-21 12:00:00,0.530789,0,5.76672e-06,0.530795
1976-12-22 00:00:00,0.525457,0,0,0.525457
1976-12-22 12:00:00,0.5204,0,5.26965e-06,0.520405
1976-12-23 00:00:00,0.515172,0,0,0.515172
1976-12-23 12:00:00,0.51022,0,5.42193e-06,0.510225
1976-12-24 00:00:00,0.505095,0,0,0.505095
1976-12-24 12:00:00,0.500246,0,4.01263e-06,0.50025
1976-12-25 00:00:00,0.495222,0,0,0.495222
1976-12-25 12:00:00,0.490214,0,0,0.490214
1976-12-26 00:00:00,0.48528,0,0,0.48528
1976-12-26 12:00:00,0.480374,0,0,0.480374
1976-12-27 00:00:00,0.475539,0,0,0.475539
1976-12-27 12:00:00,0.470948,0,4.9245e-06,0.470952
1976-12-28 00:00:00,0.55453,0,0.0890273,0.643558
1976-12-28 12:00:00,0.578242,0,0,0.578242
1976-12-29 00:00:00,0.572421,0,0,0.572421
1976-12-29 12:00:00,0.566855,0,6.36468e-06,0.566861
1976-12-30 00:00:00,0.561158,0,0,0.561158
1976-12-30 12:00:00,0.555741,0,7.6206e-06,0.555749
1976-12-31 00:00:00,0.550158,0,0,0.550158
1976-12-31 12:00:00,0.544854,0,7.45645e-06,0.544861
1977-01-01 00:00:00,0.539381,0,0,0.539381
"""
        self.extract_api = StringIO(extract.decode())
        self.extract_api = tsutils.asbestfreq(
            pd.read_csv(self.extract_api, index_col=0, parse_dates=True, header=0)
        )

    def test_api(self):
        out = tsutils.common_kwds("tests/data_plotgen.plt").astype("float64")
        assert_frame_equal(out, self.extract_api)