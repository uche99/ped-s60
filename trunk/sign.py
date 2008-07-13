#
# sign.py
#
# This file takes care of converting an usigned testrange build into
# a signed one using opensignsis.py.
#

# full path to opensignsis
opensignsis = 'opensignsis.py'

from make import verstr, system

def main():
    system('%s Ped_%s_3rdEd_unsigned_testrange.sis Ped_%s_3rdEd_signed_imei_{imei}.sis' % \
        (opensignsis, verstr(), verstr()))

if __name__ == '__main__':
    main()
