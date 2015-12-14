
from collections import OrderedDict

input_variable_blocks = OrderedDict((
('Datasets', '''
    ndtset jdtset udtset
    '''),
('Basis set', '''
    ecut ecutsm
    '''),
('Bands', '''
    nband nbdbuf
    '''),
('k-point grid', '''
    kptopt nkpt kpt wtk ngkpt kptrlatt
    nshiftk shiftk kptbounds kptns
    '''),
('Models', '''
    ixc ppmodel ppmfreq usepawu upawu jpawu
    '''),
('PAW options', '''
    bxctmindg  dmatpawu   dmatpuopt   dmatudiag  iboxcut
    jpawu  lpawu   lexexch  mqgriddg  ngfftdg
    pawcpxocc   pawcross   pawecutdg   pawfatbnd
    pawlcutd   pawlmix   pawmixdg   pawnhatxc   pawnphi
    pawntheta   pawnzlm   pawoptmix   pawovlp
    pawprtden   pawprtdos   pawprtvol   pawprtwf
    pawspnorb   pawstgylm   pawsushat   pawusecp
    pawxcdev   prtcs   prtefg   prtfc   prtnabla
    ptcharge  quadmom  spnorbscl  usedmatpu   upawu
    useexexch   usepawu   usexcnhat
    '''),
('SCF procedure', '''
    iscf nstep nline tolvrs tolwfr
    toldfe toldff tolimg tolmxf tolrff
    '''),
('KSS generation', '''
    kssform nbandkss
    '''),
('GW procedure', '''
    optdriver gwcalctyp spmeth nkptgw kptgw
    bdgw nqptdm qptdm
    '''),
('GW param', '''
    ecuteps ecutsigx ecutwfn nomegasf
    nfreqim nfreqre freqremax npweps rhoqpmix
    '''),
('GW options', '''
    userre awtr symchi gwpara symsigma gwmem fftgw
    '''),
('Structural optimization', '''
    amu  bmass  delayperm   diismemory   dilatmx   dtion   dynimage
    ecutsm  friction   fxcartfactor  getcell   getxcart   getxred
    goprecon   goprecprm  iatcon   iatfix   iatfixx   iatfixy   iatfixz
    imgmov   ionmov   istatimg  mdtemp   mdwall  natfix   natfixx
    natfixy   natfixz   natcon   nconeq   nimage   nnos   noseinert
    ntime   ntimimage  optcell  pimass   pitransform   prtatlist  qmass
    random_atpos   restartxf  signperm   strfact   strprecon   strtarget
    tolimg   tolmxf  vel   vis  wtatcon
    '''),
('Response function', '''
    bdeigrf elph2_imagden esmear frzfermi
    ieig2rf mkqmem mk1mem prepanl prepgkk
    prtbbb rfasr rfatpol rfddk rfdir rfelfd
    rfmeth rfphon rfstrs rfuser rf1atpol rf1dir
    rf1elfd rf1phon rf2atpol rf2dir rf2elfd
    rf2phon rf3atpol rf3dir rf3elfd rf3phon
    sciss smdelta td_maxene td_mexcit
    '''),
('Wannier 90', '''
    w90iniprj w90prtunk
    '''),
('Parallelisation', '''
    gwpara localrdwf ngroup_rf npband npfft
    npimage   npkpt   npspinor paral_kgb
    paral_rf use_gpu_cuda
    '''),
('Unit cell', '''
    acell angdeg rprim ntypat znucl natom typat xred xcart
    '''),
('Symmetries', '''
    nsym symrel tnons spgroup
    '''),
('Printing', '''
    prtvol enunit
    '''),
('Files', '''
    irdddk irdden ird1den irdqps irdkss irdscr
    irdsuscep irdwfk irdwfq ird1wf getcell
    getddk getden getgam_eig2nkq getkss getocc
    getqps getscr getsuscep getvel getwfk
    getwfq getxcart getxred get1den get1wf
    '''),
))

