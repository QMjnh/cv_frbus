' Program for stochastic sims using linver under VAR expectations

' The simulations are executed around a baseline in which
' the values of all linver variables are zero.  When the effective
' lower bound on the funds rate (ZLB) is imposed, the actual
' baseline (neutral) value of the nominal federal funds rate must
' be supplied in the series rff_neutral, so that the value of the
' ZLB relative to the zero baseline can be calculated.

' The stochastic shocks are based on the historical residuals of
' the 52 stochastic equations in FRB/US, and they are applied to
' the error terms of the corresponding linearized equations. 
'

' Key parameters
'
' mpolicy         designates the monetary policy rule
' zero_bound      designates whether the ZLB is imposed
'   zlb           value of ZLB (typically 0)
'   rff_neutral   neutral value of nominal funds rate
' fpolicy         designates the fiscal policy rule
'
' nreplic         number of stochastic replications
' nsimqtrs        length of each replication

' residuals_file  name of text file with historical equation residuals
' draw_method     method for sampling from historical residuals
' resid_drawstart first historical quarter from which to sample residuals     
' resid_drawend   last historical quarter from which to sample residuals

' The available settings for the mpolicy, fpolicy, and draw_method
' parameters are noted below and described in more detail in the
' LINVER_IN_EVIEWS document.


' ************************************************************
' Section 0:  Subs and workfile
' ************************************************************

  include /background_code/master_library

' Workfile    
  %wfstart = "1965q1"
  %wfend = "2200q4"
  %mainpage = "main"
  wfcreate(wf=aaa,page={%mainpage}) q {%wfstart} {%wfend}


' ************************************************************
' Section 1:  Parameters
' ************************************************************

' File containing linver XML code
  string xmlpath = "linver.xml"

' Simulation range 
  string simstart = "2025q1"
  scalar nsimqtrs = 200

' Monetary policy options 
' policy rule ("intay" "tay" "tlr" "gen" "rr" "ex")
  string mpolicy = "intay"
' effective lower bound (ZLB) on funds rate ("yes" "no")
  string zero_bound = "yes"
  if zero_bound = "yes" then
    scalar zlb = 0
    smpl @all
    series rff_neutral = 2 
  endif
' adjustment factor for policymakers estimate of equilbrium 
' real funds rate ("0" "1")
  string drstar_val = "0"

' Fiscal policy rule ("s" "d" "x")
  string fpolicy = "s"

' Stochastic parameters
  scalar nreplic = 5000
  string residuals_file = "hist_residuals.txt"
  string draw_method = "state"  '"boot" "mvnorm" "state"

  string resid_drawstart = "1970q1"
  string resid_drawend = "2019q4"
  rndseed 12345

' Scenario suffixes
  %suftrack = "_0"
  %suf = "_1"

' Tracked variables (must include xgap2, lur, rff, picx4 if statistics
' subroutine is called)
  string tracknames = "xgap2 lur rff picx4 "
  tracknames = tracknames + " lurgap rg10 pic4 lurnat anngr hggdpt"

' Settings text file
  text settings


' *************************************************************
' Section 2:  Load linver  
' *************************************************************

  statusline loading linver

' Coefficients and equations
  string modname = "linver"
  read_xml_model(path={xmlpath})

' Zero bound
  if zero_bound = "yes" then
    {modname}.replace rff - rff_aerr = _
       @recode(rffrule>rffmin_linver,rffrule, rffmin_linver)
  endif

' Add extra equations
  {modname}.append anngr = 100*(xgdp_l-xgdp_l(-4))
  {modname}.append lurgap = lur-lurnat

' Set all linver data = 0
  smpl @all
  %varlist = {modname}.@varlist
  for !i = 1 to @wcount(%varlist)
    %tmp = @word(%varlist,!i)
    series {%tmp} = 0
  next

' Monetary and fiscal policy
  {modname}.replace rffrule = rffrule_aerr + rff{mpolicy}
  {modname}.replace rstar = rstar_aerr + rstar(-1) _
                + {drstar_val}*.05*(rrtr - rstar(-1))
  if fpolicy = "x" then
    {modname}.replace trpt = 0
  else
    {modname}.replace trpt = trpt_aerr + trpt{fpolicy}
  endif

  string simend
  call dateshift(simstart,simend,nsimqtrs-1)

' add setup information to settings text file
  settings.append stochstic simulation length: {nsimqtrs}  
  settings.append stochastic reps = {nreplic}
  settings.append draw method = {draw_method}
  settings.append monetary policy rff{mpolicy}; fiscal policy trpt{fpolicy} 
  settings.append ZLB = {zero_bound}
  settings.append drstar = {drstar_val}



' *************************************************************
' Section 3:  Read stochastic shocks
' *************************************************************

  statusline creating shocks
  call make_stochastic_shocks


' ************************************************************
' Section 4:  Finish setting up
' ************************************************************

' Tracked variables
  scalar ntrack = @wcount(tracknames)
  group track {tracknames}
  for !i = 1 to ntrack
  ' for each tracked variable, create a solution matrix
    %vv = @word(tracknames,!i)
    matrix(nsimqtrs,nreplic) {%vv}_mat
  next
  smpl @all
  for !i = 1 to ntrack
  ' for each tracked variable, set its *_base value to zero
    %vv = @word(tracknames,!i)
    series {%vv}_base = 0
  next

' Set rffmin_linver for ZLB
  smpl @all
  if zero_bound = "yes" then
    series rffmin_linver = (zlb-rff_neutral)
  endif

' Baseline tracking
  statusline tracking
  smpl {simstart} {simend}
  {modname}.addassign @all
  {modname}.addinit(v=n) @all
  {modname}.scenario(n,a={%suftrk}) "deterministic baseline"
  {modname}.solveopt(o=n)
  {modname}.solve
  scalar mm = @max(@abs(xgap{%suftrk}-xgap))
  if mm > .00001 then
    statusline tracking failed
    stop
  endif

' Monetary policy eqs must have zero add factors when ZLB is
' imposed
  if zero_bound = "yes" then
    smpl @all
    for %yy rff rff{mpolicy} rffrule
      {%yy}_a = 0
      {%yy}_aerr = 0
    next
  endif

' Make sure model still tracks
  {modname}.solve
  scalar mm = @max(@abs(xgap{%suftrk}-xgap))
  if mm > .0000001 then
    statusline nonzero baseline simulation
    stop
  endif


' ************************************************************
' Section 5:  Stochastic sims
' ************************************************************

  statusline running stochastic sims

  {modname}.scenario(n,a={%suf}) "stoch sims"
  matrix(nsimqtrs,nshocks) stocherrors


'*********************************************
'stochastic simulation loop (sims are run one at a time)

  tic

  smpl {simstart} {simend}
  for !i = 1 to nreplic
    statusline !i
    if draw_method = "boot" or draw_method = "state" then
    ' load the randomly drawn shock quarters and load associated
    ' the shocks into their _aerr error variables
      for !k = 1 to nsimqtrs
        !index = index_mat(!k,!i)
        matplace(stocherrors, @rowextract(errormat, !index), !k, 1)
      next
    endif
    if draw_method = "mvnorm" then
    ' draw random shocks from the error distribution
      nrnd(nrnderrors)
      matrix stocherrors = nrnderrors*@transpose(sdmat)
    endif  
    mtos(stocherrors,shock_aerr)
    {modname}.solve
  ' store solution values 
    for !j = 1 to ntrack
      %temp = track.@seriesname(!j)
      %temp1 = %temp + "_mat"
      stom({%temp}{%suf},tmp)
      colplace({%temp1},tmp,!i)  
    next
  next

  scalar elapsed = @toc
  !elapsed = elapsed
  settings.append simulation time = {!elapsed} seconds  

  call statistics


' **************************************************************************
' **************************************************************************
' **************************************************************************
' **************************************************************************
' **************************************************************************
' **************************************************************************
' **************************************************************************
' **************************************************************************
  subroutine makestats(string %trkname)

  %trkmat = %trkname + "_mat"
  %statsmat = %trkname + "_stats"
  matrix(nsimqtrs,!nstats) {%statsmat}

  smpl {simstart} {simend}

' loop over each simulation quarter
  for !ii2 = 1 to nsimqtrs
  ' put simulation replications for this quarter into matrix tempm1
    matrix tempm1 = @sort(@rowextract({%trkmat},!ii2))
    {%statsmat}(!ii2,1) = {%trkname}_base(!lqtr + !ii2)
    {%statsmat}(!ii2,2) = @mean(tempm1)
    {%statsmat}(!ii2,3) = tempm1(1,@floor(.50*nreplic))
    {%statsmat}(!ii2,4) = @stdevp(tempm1)
    {%statsmat}(!ii2,5) = tempm1(1,@floor(.15*nreplic))
    {%statsmat}(!ii2,6) = tempm1(1,@floor(.85*nreplic))
    {%statsmat}(!ii2,7) = tempm1(1,@floor(.05*nreplic))
    {%statsmat}(!ii2,8) = tempm1(1,@floor(.95*nreplic))
  next

' also create individual series for each statistic
  series {%trkname}_base = 0
  series {%trkname}_mn = 0
  series {%trkname}_med  = 0
  series {%trkname}_se  = 0
  series {%trkname}_lo70 = 0
  series {%trkname}_hi70 = 0
  series {%trkname}_lo90 = 0
  series {%trkname}_hi90 = 0

  group {%trkname}_group {%trkname}_base {%trkname}_mn {%trkname}_med _
  {%trkname}_se {%trkname}_lo70 _
  {%trkname}_hi70  {%trkname}_lo90 {%trkname}_hi90

  mtos({%statsmat},{%trkname}_group)

  endsub


' **************************************************************************
' **************************************************************************
  subroutine tableform(string %tabname, string %nrows)

    table(@val(%nrows),9) {%tabname}

    {%tabname}.setwidth(1:13) 8
    {%tabname}.setjust(r1c1:r{%nrows}c9) right
    {%tabname}.setformat(r2c2:r{%nrows}c9) f.3
    {%tabname}(1,1) = "qtr"
    {%tabname}(1,2) = "baseline"
    {%tabname}(1,3) = "mean"
    {%tabname}(1,4) = "median"
    {%tabname}(1,5) = "stdev"
    {%tabname}(1,6) = "70%-low"
    {%tabname}(1,7) = "70%-hi"
    {%tabname}(1,8) = "90%-low"
    {%tabname}(1,9) = "90%-hi"

  endsub


' **************************************************************************
' **************************************************************************
  subroutine statistics

  statusline computing statistics

  !nstats = 8

  smpl {simstart} {simend}
  !index = 2
  series year = @year
  series quarter = @quarter
  alpha yyyyqq = @str(year) + "Q" + @str(quarter)
  !lqtr = @dtoo(simstart) - 1

' create a summary table in which to store key results
  call tableform("summary_tab","100")


'**************************************
' loop over each tracked variable,
  for !ii1 = 1 to ntrack

    %trkname = track.@seriesname(!ii1)

  ' compute statistics
    call makestats(%trkname)

  ' load statistics into variable-specific table
    %tabname = %trkname + "_tab"
    call tableform(%tabname,@str(nsimqtrs+2))
    for !ii2 = 1 to nsimqtrs
      {%trkname}_tab(!ii2+2,1) = yyyyqq(!lqtr + !ii2)
      for !ii3 = 1 to !nstats
        {%trkname}_tab(!ii2+2,!ii3+1) = {%trkname}_stats(!ii2,!ii3)
      next
    next

  ' load statistics for each q4 observation into summary table
    !index = !index + 1
    summary_tab(!index,1) = %trkname
    !index = !index + 1
    for !ii2 = 1 to nsimqtrs
      if quarter(!lqtr+!ii2) = 3 then
        for !ii3 = 1 to !nstats + 1
          summary_tab(!index,!ii3) = {%trkname}_tab(!ii2+2,!ii3)
        next
        !index = !index + 1
      endif
      if quarter(!lqtr+!ii2) = 4 then
        for !ii3 = 1 to !nstats + 1
          summary_tab(!index,!ii3) = {%trkname}_tab(!ii2+2,!ii3)
        next
        !index = !index + 1
      endif
    next

  ' make graph showing 70 and 90 percent bands
    graph {%trkname}_graph.band {%trkname}_lo90 {%trkname}_hi90 {%trkname}_lo70 _
    {%trkname}_hi70
    {%trkname}_graph.addtext(t) %trkname
    {%trkname}_graph.setelem(1) hatch(2) fillcolor(@rgb(192,192,192))
    {%trkname}_graph.setelem(2) fillcolor(@rgb(192,192,192))
    {%trkname}_graph.setelem(1) legend(90 percent confidence band)
    {%trkname}_graph.setelem(2) legend()
    {%trkname}_graph.setelem(3) legend(70 percent confidence band)
    {%trkname}_graph.setelem(4) legend()
    {%trkname}_graph.options size(6,4.5)
    {%trkname}_graph.legend display inbox position(.1,-.1)
    {%trkname}_graph.options outlineband
  next

  lur_graph.addtext(t,just(c),font("arial",16)) Unemployment Rate
  rff_graph.addtext(t,just(c),font("arial",16)) Federal Funds Rate
  picx4_graph.addtext(t,just(c),font("arial",16)) 4-qtr Core Inflation Rate
  xgap2_graph.addtext(t,just(c),font("arial",16)) Output gap


'**************************************
' summary graph and spool
  summary_tab.deleterow(!index) 100
  graph summary_graph.merge lur_graph rff_graph xgap2_graph picx4_graph
  summary_graph.addtext(t,just(c),font("Arial",16)) _
        Stochastic Simulation Confidence Bands
  spool results
  results.append settings
  results.append summary_graph
  results.append summary_tab
  results.append error_tab
  results.name 1 settings
  results.name 2 summary_graph
  results.name 3 summary_tab
  results.name 4 error_tab

  results.display

  endsub


' **************************************************************************
' **************************************************************************
  subroutine make_stochastic_shocks

' Load residual file
  text shock_txt
  shock_txt.append(file) {residuals_file}
  svector shock_svec = shock_txt.@svectornb
  scalar nrows = @rows(shock_svec)

' shock names are in first row sandwiched between "obs" and "recind"
  string shock_names = shock_svec(1)
  shock_names = @replace(shock_names,","," ")
  scalar ncols = @wcount(shock_names)
  shock_names = @replace(shock_names,"obs","")
  shock_names = @replace(shock_names,"recind","")
  scalar nshocks = @wcount(shock_names)  

' check that all shocks are variables in linver
  string exogvars = @lower({modname}.@exoglist)
  string shocks_check = @wintersect(shock_names,exogvars)
  scalar nshocks_check = @wcount(shocks_check)
  if nshocks_check <> nshocks then
    %err = "Error: at least one shock is not an exogenous variable "
    %err = %err + "in the model"
    @uiprompt(%err)
    stop
  endif

' loop through the remaining rows to extract observation dates (qtrs) from
' the first word, recession index values (recindvec) from the last word, and
' the shock values (shockvals) from the other words
  string qtrs = " "
  matrix(nrows-1,nshocks) shockvals
  vector(nrows-1) recindvec
  for !i = 2 to nrows
    string shock_line = shock_svec(!i)
    shock_line = @replace(shock_line,","," ")
    qtrs = qtrs + " " + @word(shock_line,1)
    for !j = 2 to ncols-1
      shockvals(!i-1,!j-1) = @val(@word(shock_line,!j))
    next
    recindvec(!i-1) = @val(@word(shock_line,ncols))
  next

  qtrs = @lower(qtrs)
  string resid_filestart = @word(qtrs,1)
  string resid_fileend = @word(qtrs,@wcount(qtrs))
  series recind
  smpl {resid_filestart} {resid_fileend}
  mtos(recindvec,recind)
  group shock_aerr {shock_names}
  mtos(shockvals,shock_aerr)


' Test that residual range is valid
  smpl {resid_filestart} {resid_fileend}
  scalar jstart = resid_drawstart < resid_filestart
  scalar jend = resid_drawend > resid_fileend
  if jstart = 1 or jend = 1 then
    %err = "Error: selected residual range exceeds the data endpoints of "
    %err = %err + "the residuals data file"
    @uiprompt(%err)
    stop
  endif

' Demean residuals
  smpl {resid_drawstart} {resid_drawend}
  for !i = 1 to @wcount(shock_names)
    %vname = @word(shock_names,!i)
    scalar mn = @mean({%vname})
    {%vname} = {%vname} - mn
  next
    
  smpl {resid_drawstart} {resid_drawend}
  stom(shock_aerr,errormat)
  scalar nresidqtrs = @obssmpl

' create table of error statistics
  vector(nshocks) stddev
  for !i = 1 to nshocks
    stddev(!i) = @stdev(@columnextract(errormat,!i))
    next
  vector mnerr = @cmean(errormat)
  !nrows = 3 + nshocks
  !ncols = 3
  table(!nrows,!ncols) error_tab
  error_tab.setjust(r1c1:r{!nrows}c1) left
  error_tab.setwidth(1) 20
  error_tab(1,1) = "error"
  error_tab(1,2) = "mean"
  error_tab(1,3) = "std-dev"
  for !i = 1 to nshocks
    error_tab(!i+3,1) = @word(shock_names,!i)
    error_tab(!i+3,2) = mnerr(!i)
    error_tab(!i+3,3) = stddev(!i)
  next

' add information to text file
  settings.append residuals source = {residuals_file}
  settings.append residuals range = {resid_drawstart}-{resid_drawend}, {nresidqtrs} qtrs
  settings.append number of shocks = {nshocks}
  settings.append shocked variables = {shock_names}
  settings.append draw method = {draw_method}


'******************************************************************
' Fill the shock matrix using the selected sampling procedure
'******************************************************************

' *************************************
 'draw_method = "boot"
  if draw_method = "boot" then
    matrix(nresidqtrs, 1) i_col
    for !i = 1 to nresidqtrs
      i_col(!i,1) = !i
    next
    scalar resample_add =  nsimqtrs - nresidqtrs
    matrix(nsimqtrs,1) temp_mat
    matrix(nsimqtrs,nreplic) index_mat
    for !j = 1 to nreplic
      temp_mat = @resample(i_col, resample_add)
      matplace(index_mat, temp_mat, 1, !j)
    next
  endif

' *************************************
' draw_method = "mvnorm"
  if draw_method = "mvnorm" then
    sym vcmat = @cov(errormat)
    matrix sdmat = @cholesky(vcmat)
    matrix(nsimqtrs,nshocks) nrnderrors
  endif


' *************************************
' If draw_method = "state", the sampling procedure depends on
' the randomly-chosen state of the economy as determined by a
' markov-switching model. In the normal state, shocks are
' bootstrapped from the residuals of historical non-recessionary
' quarters. In the mild slump state, shocks equal the residuals
' seen in one of the recessions that occurred between 1970 and
' 2001. In the severe slump state, shocks equal the residuals of
' the Great Recession. 

  if draw_method = "state" then
    
  ' Verify that the sample range is valid
    scalar jstart = resid_drawstart > "1970Q1"
    scalar jend = resid_drawend < "2009q4"
    if jstart = 1 or jend = 1 then
      %err = "Error: when using the state error draw method, the residual "
      %err = %err + "range must start no later than 1970q1 and end no "
      %err = %err + "earlier than 2009q4"
      @uiprompt(%err)
      stop
    endif

  ' locations of good and medium and bad qtrs
    smpl @all
    series bad_qtrs =  recind = 1
    series medium_qtrs1 = recind = 2
    series medium_qtrs2 = recind = 3
    series medium_qtrs3 = recind = 4
    series medium_qtrs4 = recind = 5
    series medium_qtrs5 = recind = 6
    series medium_qtrs6 = recind = 7
    series medium_qtrs = recind > 1
    series good_qtrs = recind = 0

    smpl {resid_drawstart} {resid_drawend}
    call dateshift(resid_drawstart,%pp,-1)
    series ttrend = @trend(%pp)
    smpl {resid_drawstart} {resid_drawend} if bad_qtrs = 1
    stom(ttrend,bad_qindex)
    smpl {resid_drawstart} {resid_drawend} if good_qtrs = 1
    stom(ttrend,good_qindex)
    smpl {resid_drawstart} {resid_drawend} if medium_qtrs = 1
    stom(ttrend,medium_qindex)
    smpl {resid_drawstart} {resid_drawend} if medium_qtrs1 = 1
    stom(ttrend,medium_qindex1)
    smpl {resid_drawstart} {resid_drawend} if medium_qtrs2 = 1
    stom(ttrend,medium_qindex2)
    smpl {resid_drawstart} {resid_drawend} if medium_qtrs3 = 1
    stom(ttrend,medium_qindex3)
    smpl {resid_drawstart} {resid_drawend} if medium_qtrs4 = 1
    stom(ttrend,medium_qindex4)
    smpl {resid_drawstart} {resid_drawend} if medium_qtrs5 = 1
    stom(ttrend,medium_qindex5)
    smpl {resid_drawstart} {resid_drawend} if medium_qtrs6 = 1
    stom(ttrend,medium_qindex6)

    smpl {resid_drawstart} {resid_drawend}
    scalar nerrors = @obssmpl
    scalar total_bad_qtrs = @sum(bad_qtrs)
    scalar total_good_qtrs = @sum(good_qtrs)
    scalar total_medium_qtrs = @sum(medium_qtrs)
    scalar total_medium_qtrs1 = @sum(medium_qtrs1)
    scalar total_medium_qtrs2 = @sum(medium_qtrs2)
    scalar total_medium_qtrs3 = @sum(medium_qtrs3)
    scalar total_medium_qtrs4 = @sum(medium_qtrs4)
    scalar total_medium_qtrs5 = @sum(medium_qtrs5)
    scalar total_medium_qtrs6 = @sum(medium_qtrs6)

    matrix(nsimqtrs, nreplic) index_mat
    matrix(nsimqtrs, nreplic) states_mat = 0

    
  ' Define transition probabilities from the normal state to the
  ' severe slump state (ps31), the  mild slump state (ps32), or
  ' the normal state (ps33). For simplicity, assume that these
  ' values are also the probabilities that the economy in the
  ' first quarter of each replication will be in a severe slump
  ' (ps1), a mild slump (ps2), or a normal state (ps3).
    
    scalar ps31 = .006
    scalar ps32 = .035
    scalar ps33 = .959
    scalar ps1 = ps31
    scalar ps2 = ps32
    scalar ps3 = ps33

    scalar state = 0
    scalar abc
    scalar xyz

        
  ' For each replication, simulate a stochastic path for the
  ' state of the economy for quarters 1 through nsimqtrs, randomly
  ' sampling from appropriate elements of the residuals matrix
  ' based on the current state. Save these paths in state_mat. 
    
    for !ireplic = 1 to nreplic
 
        !qtrnum = 1
        rnd(abc)
        if abc <= ps1 then
            state = 1
        endif
        if ps1 < abc and abc < ps1+ps2 then
            state = 2
        endif
        if ps1+ps2 <= abc and abc <= 1 then
            state = 3
        endif

        while !qtrnum <= nsimqtrs
            if !qtrnum > 1 then
                rnd(xyz)
                if xyz <= ps33 then
                    state = 3
                endif
                if (ps33 < xyz and xyz < ps31+ps33)  then
                    state = 1
                endif
                if (ps31+ps33 <= xyz and xyz <= 1) then
                    state = 2
                endif
            endif

            states_mat(!qtrnum, !ireplic) = state

          ' draw random historical qtr based on current state
            rnd(xyz)
            if state = 1 then
                if (!qtrnum < nsimqtrs or !qtrnum = nsimqtrs) then
                    if !qtrnum + total_bad_qtrs - 1 < nsimqtrs then
                        scalar loopend = !qtrnum + total_bad_qtrs - 1
                    else
                        scalar loopend = nsimqtrs
                    endif
                    for !ii = !qtrnum to loopend
                        index_mat(!ii, !ireplic) = bad_qindex(!ii-!qtrnum+1)
                        states_mat(!ii, !ireplic) = 1
                    next
                    !qtrnum = loopend
                endif
                !qtrnum = !qtrnum + 1
                if (!qtrnum < nsimqtrs or !qtrnum = nsimqtrs) then
                    rnd(xyz)
                    scalar good_num = xyz * total_good_qtrs + 1
                    index_mat(!qtrnum, !ireplic) = good_qindex(good_num)
                    states_mat(!qtrnum, !ireplic) = 3
                endif
            endif
            if state = 2 then
                scalar which_rec
                rndint(which_rec,5)
                which_rec=which_rec+1
                %which_rec = @str(which_rec)
                if (!qtrnum < nsimqtrs or !qtrnum = nsimqtrs) then
                    if !qtrnum + total_medium_qtrs{%which_rec} - 1 < nsimqtrs then
                        scalar loopend = !qtrnum + total_medium_qtrs{%which_rec} -1
                    else
                        scalar loopend = nsimqtrs
                    endif

                    for !ii = !qtrnum to loopend
                        index_mat(!ii, !ireplic) = medium_qindex{%which_rec}(!ii-!qtrnum+1)
                        states_mat(!ii, !ireplic) = 2
                    next
                    !qtrnum = loopend
                endif
                !qtrnum = !qtrnum + 1
                if (!qtrnum < nsimqtrs or !qtrnum = nsimqtrs) then
                    rnd(xyz)
                    scalar good_num = xyz * total_good_qtrs + 1
                    index_mat(!qtrnum, !ireplic) = good_qindex(good_num)
                    states_mat(!qtrnum, !ireplic) = 3
                endif
            endif
            if state = 3 then
                if (!qtrnum < nsimqtrs or !qtrnum = nsimqtrs) then
                    rnd(xyz)
                    scalar good_num = xyz * total_good_qtrs + 1
                    index_mat(!qtrnum, !ireplic) = good_qindex(good_num)
                    states_mat(!qtrnum, !ireplic) = 3
                endif
            endif

            !qtrnum = !qtrnum + 1
        wend
    next

    !freq_good = @sum(@eeq(states_mat,3+states_mat*0))/(nsimqtrs*nreplic)
    !freq_med  = @sum(@eeq(states_mat,2+states_mat*0))/(nsimqtrs*nreplic)
    !freq_bad  = @sum(@eeq(states_mat,1+states_mat*0))/(nsimqtrs*nreplic)

    settings.append frequency good state = {!freq_good}
    settings.append frequency medium recession state = {!freq_med}
    settings.append frequency bad recession state = {!freq_bad}
  endif


endsub
