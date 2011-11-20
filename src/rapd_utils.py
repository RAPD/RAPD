__author__ = "Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2009/07/08"

"""
rapd_utils has a few useful dicts and functions used in rapd
"""

bravais   = ['1', '5', '3', '22', '23', '21', '16', '79', '75', '143', '146', '196', '197', '195']

subgroups = {  'None' : [],
               '1'    : [],
               '5'    : [],
               '3'    : ['4'],
               '22'   : [],
               '23'   : ['24'],
               '21'   : ['20'],
               '16'   : ['17','18','19'],
               '79'   : ['80','97','98'],
               '75'   : ['76','77','78','89','90','91','95','94','93','92','96'],
               '143'  : ['144','145','149','151','153','150','152','154','168','169','170','171','172','173','177','178','179','180','181','182'],
               '146'  : ['155'],
               '196'  : ['209','210'],
               '197'  : ['199','211','214'],
               '195'  : ['198','207','208','212','213'] }

intl2std =   { 'None' : 'None',
               '1'   : 'P1',      #* Bravais 
               '5'   : 'C2',      #*
               '3'   : 'P2',      #*
               '4'   : 'P21',
               '22'  : 'F222',    #*
               '23'  : 'I222',    #*
               '24'  : 'I212121',
               '21'  : 'C222',    #*
               '20'  : 'C2221',
               '16'  : 'P222',    #*
               '17'  : 'P2221',
               '18'  : 'P21212',
               '19'  : 'P212121',
               '79'  : 'I4',      #*
               '80'  : 'I41',
               '97'  : 'I422',
               '98'  : 'I4122',
               '75'  : 'P4',      #*
               '76'  : 'P41',
               '77'  : 'P42',
               '78'  : 'P43',
               '89'  : 'P422',
               '90'  : 'P4212',
               '91'  : 'P4122',
               '95'  : 'P4322',
               '93'  : 'P4222',
               '94'  : 'P42212',
               '92'  : 'P41212',
               '96'  : 'P43212',
               '143' : 'P3',      #*
               '144' : 'P31',
               '145' : 'P32',
               '149' : 'P312',
               '151' : 'P3112',
               '153' : 'P3212',
               '150' : 'P321',
               '152' : 'P3121',
               '154' : 'P3221',
               '168' : 'P6',
               '169' : 'P61',
               '170' : 'P65',
               '171' : 'P62',
               '172' : 'P64',
               '173' : 'P63',
               '177' : 'P622',
               '178' : 'P6122',
               '179' : 'P6522',
               '180' : 'P6222',
               '181' : 'P6422',
               '182' : 'P6322',
               '146' : 'R3',      #*
               '155' : 'R32',
               '196' : 'F23',     #*
               '209' : 'F432',
               '210' : 'F4132',
               '197' : 'I23',     #*
               '199' : 'I213',
               '211' : 'I432',
               '214' : 'I4132',
               '195' : 'P23',     #*
               '198' : 'P213',
               '207' : 'P432',
               '208' : 'P4232',
               '212' : 'P4332',
               '213' : 'P4132' }

std2intl = dict((value,key) for key, value in intl2std.iteritems())


std_sgs = ['None','P1','C2','P2','P21','F222','I222','I212121','C222','C2221','P222',
           'P2221','P21212','P212121','I4','I41','I422','I4122','P4','P41','P42','P43',
           'P422','P4212','P4122','P4322','P4222','P42212','P41212','P43212','P3','P31',
           'P32', 'P312','P3112','P3212','P321','P3121','P3221','P6','P61','P65','P62',
           'P64','P63','P622','P6122','P6522','P6222','P6422','P6322','R3','R32','F23',
           'F432','F4132','I23','I213','I432','I4132','P23''P213''P432','P4232','P4332',
           'P4132']


#
#  Some utility functions     
#
def print_dict(in_dict):
    keys = in_dict.keys()
    keys.sort()
    for key in keys:
        print key,'::',in_dict[key]
    print ''
        
months = { 'Jan' : '01',
           'Feb' : '02',
           'Mar' : '03',
           'Apr' : '04',
           'May' : '05',
           'Jun' : '06',
           'Jul' : '07',
           'Aug' : '08',
           'Sep' : '09',
           'Oct' : '10',
           'Nov' : '11',
           'Dec' : '12'}

def zerofillday(day_in):
    #print day_in
    intday = int(day_in)
    #print intday
    strday = str(intday)
    #print strday
    if len(strday) == 2:
        return(strday)
    else:
        return('0'+strday)
    
def date_adsc_to_sql(datetime_in):
    #print datetime_in
    spldate = datetime_in.split()
    #print spldate
    time  = spldate[3]
    #print time
    year  = spldate[4]
    #print year
    month = months[spldate[1]]
    #print month
    day   = zerofillday(spldate[2])
    #print day
    
    date = '-'.join((year,month,day))
    #print date
    #print ' '.join((date,time))
    return('T'.join((date,time)))


    

if __name__ == "__main__":
    
    print_dict(intl2std)
    print_dict(std2intl)
