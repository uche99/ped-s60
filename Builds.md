Ped is distributed in so called SIS files (Symbian OS installation files). Every release contains more than one such file. Depending on which phone model you have and what Python scripts you want to develop using Ped, you should download a different SIS file.

Currently, every Ped release includes following SIS files:

## S60 3rd edition, no caps (3rdEd\_no\_caps) ##

  * Use this build if you have a phone supporting S60 3rd edition platform (all newer S60 phones).
  * This build doesn't have any additional Symbian OS capabilities enabled which means that you may not be able to execute scripts that make use of some advanced features of your phone.
  * It can be installed and used right after downloading.

## S60 3rd edition, unsigned testrange (3rdEd\_unsigned\_testrange) ##

  * Use this build if you have a phone supporting S60 3rd edition platform (all newer S60 phones).
  * This build have all the _User Blanket Grant_ and _Symbian Signed_ capabilities enabled. It is not signed so you will have to sign it for your phone before you will be able to install it. Thanks to the capabilities, you will be able to use most of your phone's features.
  * To sign it, go to [Open Signed Online](https://www.symbiansigned.com/app/page/public/openSignedOnline.do), enter the IMEI number of your phone (enter `*`#06# on the standby screen to get it), your e-mail, select the downloaded SIS file and select **all** capabilities. Fill out the rest of the fields. You will receive a link to your signed SIS file in an e-mail.

## S60 2nd edition (2ndEd) ##

  * Use this build if you have a phone supporting S60 2nd edition platform (older S60 phones).
  * Since the capabilities were introduced in S60 3rd edition, there is nothing more you need to do. Just download and install.