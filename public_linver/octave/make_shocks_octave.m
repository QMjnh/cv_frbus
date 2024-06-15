%******************************************************************
% Program to generate the random shocks that will be used in the
% stochastic simulations, where the shocks are based on the
% historical residuals of the main FRB/US behavior equations. More
% information about available sampling options can be found in the
% stochsims manual.
%
% Required inputs:
%   residuals_file -- a CSV text file holding the historical
%     FRB/US residuals; see the stochsims manual for information
%     about its construction and required format
%   draw_method -- the sampling procedure to be used to construct
%     random shocks. Permissable settings are "boot" (standard
%     bootstrapping), "mvnorm" (random draws from an estimated
%     multinormal distribution), and "state" (state-contingent
%     bootstrapping)
%   nreplic -- number of simulated paths to be generated
%   nsimqtrs -- number of quarters in each simulated path
%   exog_names -- namelist of the exogenous variables of the model
%   rescale_wpshocks -- indicator of whether pre-1983 wage and
%     price shocks are to be rescaled so that their variances match
%     that recorded from 1983 on 
%
% Optional inputs:
%   res_drop -- list of shocks to be excluded from the standard set
%     of shocks applied during the stochastic simulations
%   alt_range -- alternative historical range to be used in
%     sampling; if draw_method = "state", the first element of 
%     alt_range should be set no later than 1970Q1 and the last
%     element should be set no earlier than 2009Q4
%
% Outputs:
%   shocks -- the matrix of shocks that will be used in the
%      stochastic, with dimensions nreplic X nsimqts X nsv 
%   shock_names -- namelist of shocks 
%   shock_locs -- locations of shocks in the list of the model's
%     exogenous variables
%   nsv -- number of shocks
%******************************************************************

disp("  ");
disp("Computing shocks to be used in stochastic simulations");
disp("  ");
fail_flag = "no";



%******************************************************************
% Retrieve historical residuals and other information from the
% csv text file, which is assumed to have the following structure:
%   1. The first column contains the observation dates of the
%      residuals, the subsequent columns the residuals of the
%      individual equations, and the final column a recession
%      indicator. 
%   2. The column headers are in the first row, starting with
%      "obs", followed by the names of the residuals, and ending
%      with "recind" in the final column, all in lower
%      case. Residual names should match the shock names in the
%      model, e.g., ebfi_l_aerr.
%   3. Observation dates in the first column should take the form
%      e.g. 2002Q2.
%   4. The recession indicator reported in the final column has
%      values values equal to 0 for quarters when the economy was
%      not in recession, 1 for the quarters of the recession
%      beginning in 1970Q1, 2 for the recession beginning in
%      1974Q1, and so on for subsequent recessions. The Great
%      Recession should be indexed by the number 7.
%*****************************************************************



if exist('OCTAVE_VERSION')
    C = csv2cell(residuals_file);
    % C contains everything in the residuals_file
    [jrows,jcols] = size(C);
    % residual observation dates -- first column of C starting in
    % row 2
    residual_dates = C(2:jrows,1);
    % recession index values -- last column of C starting in row 2
    recind = cell2mat(C(2:jrows,jcols));
    % residual series names -- first row of C starting in
    % column 2
    shock_names = C(1,2:jcols-1)';
    % historical residuals -- everything else
    residuals = cell2mat(C(2:jrows,2:jcols-1));
    nobs = size(residual_dates,1);
    sample_range = {residual_dates(1),residual_dates(nobs)};
else		    
    csvdata = readtable(residuals_file);
    shock_names = csvdata.Properties.VariableNames;
    sz = size(shock_names);
    shock_names = shock_names(1,2:sz(2)-1)';
    C = table2cell(csvdata);
    % C contains everything in the residuals_file except
    % the top row of shock names
    [jrows,jcols] = size(C);
    % residual observation dates -- first column of C
    residual_dates = C(:,1);
    % recession index values -- last column of C
    recind = cell2mat(C(:,jcols));
    % historical residuals -- the other columns
    residuals = cell2mat(C(:,2:jcols-1));
    nobs = size(residual_dates,1);
    sample_range = string({residual_dates(1),residual_dates(nobs)});
end
    

%[exceldata,txtdata] = xlsread(residuals_file);
%ncols = size(exceldata,2);
%nrows = size(exceldata,1);
%recind = exceldata(:,ncols);
%residuals = exceldata(:,1:ncols-1);
%shock_names = txtdata(1,2:ncols)';
%residual_dates = txtdata(2:nrows+1,1);
%nobs = size(residual_dates,1);
%sample_range = {residual_dates(1),residual_dates(nobs)};
%if ~exist('OCTAVE_VERSION')
%    sample_range = string(sample_range);
%end



%******************************************************************
% Set-up for constructing the matrix of random shocks
%******************************************************************

% Verify that all shocks in the residuals file are in the model
% variables in the model; if not, stop execution.

z = intersect(exog_names,shock_names);
if size(z,1) < size(shock_names,1)
    display("Error: variables in the residuals file are not in the model.");
    fail_flag = "yes";
    return
end

% If the rescaling option is selected, adjust pre-1983 wage and
% price residuals so that their variances matches that of the
% later sample

if strcmp(rescale_wpshocks,"yes")
    ploc = find(strcmp(shock_names,"picxfe_aerr"));
    wloc = find(strcmp(shock_names,"pieci_aerr"));
    sq = find(strcmp(residual_dates,"1982Q4"));
    eq = size(residuals,1); 
    p1 = std(residuals(1:sq,ploc));
    w1 = std(residuals(1:sq,wloc));
    p2 = std(residuals(sq+1:eq,ploc));
    w2 = std(residuals(sq+1:eq,wloc));
    residuals(1:sq,ploc) = residuals(1:sq,ploc)*p2/p1;
    residuals(1:sq,wloc) = residuals(1:sq,wloc)*w2/w1;    
end
    
% If an alternative sample range has been defined, shrink the shock
% matrix to conform to the alternative sample period.

if exist('alt_range') == 1  
    start_qtr = find(strcmp(residual_dates,alt_range(1)));
    end_qtr = find(strcmp(residual_dates,alt_range(2)));
    if isempty(start_qtr) == 1 | isempty(end_qtr)
        display("Error: invalid alternative sample period");
        fail_flag = "yes";
        return
    end
    residuals = residuals(start_qtr:end_qtr,:);
    recind = recind(start_qtr:end_qtr);
    sample_range = alt_range;
end


% If a list of excluded residuals has been defined, shrink the
% residuals matrix and the shock namelist to conform.

if exist('res_drop')
    aaa = union(shock_names,res_drop);
    if size(union(shock_names,res_drop),1) > size(shock_names,1) 
        display("some or all excluded residuals not in the model");
	fail_flag = "yes"
        return
    end
    keepers = [1:size(shock_names,1)]*0 + 1;
    for i=1:size(shock_names,1)
        aaa = intersect(shock_names(i),res_drop);
        keepers(i) = isempty(aaa);
    end
    allnames_index = [1:size(shock_names,1)];
    keepers_index = allnames_index(keepers==1);
    residuals= residuals(:,keepers_index);
    shock_names = shock_names(keepers_index,:);
end


% Demean the historical residuals and compute their
% variance-covariance matrix

ones = residuals*0 + 1;
residuals = residuals - ones.*mean(residuals);
shocks_vc = cov(residuals);
 

% Find the location of the equation shocks in the exogenous
% variable list

shock_locs = [1:size(shock_names,1)];
for i = 1:size(shock_names,1);
    shock_locs(i) = find(strcmp(exog_names,shock_names(i)));
end;
 

% Initialize a shocks matrix to hold random shocks for all
% replications, quarters and behavioral equation shocks

nsv = size(shock_names,1);
nqtrs = nsimqtrs;
shocks = zeros(nreplic,nqtrs,nsv);


% Set seed so that the same sequence of random numbers is
% created each time (note:  Although each Octave execution will draw
% the same random sequence each time and each Matlab execution will
% draw the same random sequence each time, the Octave sequence will
% not be the same as the Matlab sequence.)
if exist('OCTAVE_VERSION')
    rand("seed",12345);
else
    rng('default');
end


%******************************************************************
% Fill the shock matrix using the selected sampling procedure
%******************************************************************

% If draw_method = "boot", fill shocks matrix by randomly
% sampling the historical quarters of the residuals matrix

if find(strcmp(draw_method,"boot"))
    nhqtrs = size(residuals,1);
    for ireplic = 1:nreplic
        randqtr = randi(nhqtrs,nsimqtrs,1);
	shocks(ireplic,:,:) = residuals(randqtr,:);
    end
end


% If draw_method = "mvnorm", fill shocks matrix by randomly
% sampling from an N(0,vc_shocks) distribution

if find(strcmp(draw_method,"mvnorm"))
    for ireplic = 1:nreplic
        shocks(ireplic,:,:) = mvnrnd(zeros(nsimqtrs,nsv),shocks_vc);
    end
end

% If draw_method = "state", the sampling procedure depends on
% the randomly-chosen state of the economy as determined by a
% markov-switching model. In the normal state, shocks are
% bootstrapped from the residuals of historical non-recessionary
% quarters. In the mild slump state, shocks equal the residuals
% seen in one of the recessions that occurred between 1970 and
% 2001. In the severe slump state, shocks equal the residuals of
% the Great Recession. 

if find(strcmp(draw_method,"state"))
    
    % Verify that the sample range is valid
    sstart = str2num(strrep(char(sample_range(1)),"Q","0"));
    send = str2num(strrep(char(sample_range(2)),"Q","0"));
    if sstart > 197001 | send < 200904
        disp("Error: invalid range for recession sampling");
        fail_flag = "yes";
        return
    end
    
    % Define transition probabilities from the normal state to the
    % severe slump state (ps31), the  mild slump state (ps32), or
    % the normal state (ps33). For simplicity, assume that these
    % values are also the probabilities that the economy in the
    % first quarter of each replication will be in a severe slump
    % (ps1), a mild slump(ps2), or a normal state (ps3).
    
    ps31 = .006;
    ps32 = .035;
    ps33 = .959;
    ps1 = ps31;
    ps2 = ps32;
    ps3 = ps33;
        
    % For each replication, simulate a stochastic path for the
    % state of the economy for quarters 1 through nqtrs, randomly
    % sampling from appropriate elements of the residuals matrix
    % based on the current state. Save these paths in state_mat. 
    
    state_mat = zeros(nreplic,nqtrs);
    for ireplic = 1:nreplic
        
        % Initialize the state in the first quarter
        z = rand;
        if z <= ps1
            state = 1;
        else
            if z <= ps1+ps2
                state = 2;
            else
                state = 3;
            end
        end
        
        % Advance through the nqtrs of the current replication, 
        % updating the state and drawing state-contingent shocks
        % along the way.
        iqtr = 1;
        while iqtr <= nqtrs
            
            % If not in the first quater, update the state
            if iqtr > 1
                z = rand;
                if z > ps33+ps32;
                    state = 1;
                end
                if z <= ps33+ps32 & z > ps33
                    state = 2;
                end
                if z <= ps33
                    state = 3;
                end
            end
            
            % If in a normal state, fill the shocks matrix for the
            % current replication and quarter with the residuals
            % from a random nonrecessionary historical quarter 
            if state == 3
                qnorm = find(recind==0);
                z = residuals(qnorm,:);
                nhqtrs = size(z,1);
                randqtr = randi(nhqtrs);
                shocks(ireplic,iqtr,:) = z(randqtr,:);
                state_mat(ireplic,iqtr) = 3;
                iqtr = iqtr + 1;
            end
            
            % If in a mild slump state, randomly select one of the
            % six mild historical recessions and load its residuals
            % into the shock matrix
            if state == 2
                episode = randi(6);
                qmrec = find(recind==episode);
                t1 = iqtr;
                t2 = iqtr + size(qmrec,1)-1;
                if t2 > nqtrs
                    % historical recession longer than remaining
                    % slots in shocks matrix, so trim to fit
                    t2 = nqtrs;
                    n = t2 - t1 + 1;
                    qmrec = qmrec(1:n);
                end
                shocks(ireplic,t1:t2,:) = residuals(qmrec,:);
                state_mat(ireplic,t1:t2) = 2;
                iqtr = t2 + 1;
            end
                        
            % If in a severe slump state, load the shocks matrix
            % with the residuals from the Great Recession as
            % indicated by recind = 7
            if state == 1
                qsrec = find(recind==7);
                t1 = iqtr;
                t2 = iqtr + size(qsrec,1) - 1;
                if t2 > nqtrs
                    % historical recession longer than remaining
                    % slots in shocks matrix, so trim to fit
                    t2 = nqtrs;
                    n = t2 - t1 + 1;
                    qsrec = qsrec(1:n);
                end
                shocks(ireplic,t1:t2,:) = residuals(qsrec,:);
                state_mat(ireplic,t1:t2) = 1;
                iqtr = t2 + 1;
            end
        end
    end
end

                
