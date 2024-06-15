%*******************************************************************
% Program to first verify the validity of the user-supplied
% parameter settings defined in the master stochsims program and
% the set other parameters as needed. If a mandatory user-supplied
% setting does not exist or if a user-supplied setting is invalid,
% the program will flag the error and stop execution.
%********************************************************************

disp("  ");
disp("Parameter initialization"); 
disp("  ");
fail_flag = "no";


% Verify that the mandatory user-supplied expectational version of
% the model is defined and valid

if exist('expvers') == 0
    disp("error: undefined expectational version"); 
    fail_flag = "yes";
    return
else
    valid_vers = {'var','mcap','mcapwp','mceall'};
    if isempty(find(strcmp(expvers,valid_vers))) == 1
        disp("error: invalid expectational version");
        fail_flag = "yes";
        return
    end
end


% Verify that the mandatory user-supplied monetary policy rule is
% defined and valid

if exist('mprule') == 0
    disp("error: undefined monetary policy rule"); 
    fail_flag = "yes";
    return
else
    rulelist = {'tay','intay','fpt','infpt','ait','rw','kr'};
    rulelist = horzcat(rulelist,'adur','aait');
    if isempty(find(strcmp(mprule,rulelist))) == 1
        disp("error: invalid monetary policy rule selected");
        fail_flag = "yes";
        return
    end
end


% Verify that the mandatory user-supplied indicator for imposing
% the ELB constraint exists and is valid

if exist('elb_imposed') == 0
    disp("error: elb_imposed undefined"); 
    fail_flag = "yes";
    return
else
    if strcmp(elb_imposed,"yes") == 0 & strcmp(elb_imposed,"no") == 0
        disp("error: elb_imposed must equal yes or no");
        fail_flag = "yes";
        return
    end
end


% If the ELB constraint is imposed, verify that elb has been
% defined. Also, verify that any user-supplied value of elbqtrs is
% valid; if elbqtrs has not been defined, set it to the default.

if strcmp(elb_imposed,"yes")
    if exist('elb') == 0
        disp("error: ELB imposed but elb not defined");
        fail_flag = "yes";
        return
    end
    if exist('elbqtrs') == 0
        if strcmp(expvers,"var")
            elbqtrs = 1;
        else
            elbqtrs = 61;
        end
    else
        if elbqtrs < 1
            disp("error: user set elbqtrs < 1");
            fail_flag = "yes";
            return
        end
        if elbqtrs > 61
            disp("warning: elbqtrs>61, convergence fails likely");
        end
        if elbqtrs > 1 & strcmp(expvers,"var")
            disp("error: user set elbqtrs>1 with VAR expectations");
            fail_flag = "yes";
            return
        end
    end
else
    if exist('elb')==1
        disp("warning: elb defined by user but ELB not imposed");
    end
    if exist('elbqtrs')==1
        disp("warning: elbqtrs defined by user but ELB not imposed");
    end
    elb = -9999;
end


% If the selected monetary policy rule is nonlinear, verify that
% any user-defined value for asymqtrs is valid; if undefined, set
% asymqtrs equal to its default value 

if strcmp(mprule,"adur") | strcmp(mprule,"aait")
    if exist('asymqtrs') == 0 
        if strcmp(expvers,"var")
            asymqtrs = 1;
        else
            if strcmp(elb_imposed,"yes")
                asymqtrs = elbqtrs;
            else
                asymqtrs = 61;
            end
        end
    else
        if asymqtrs < 1
            disp("error: asymqtrs<1");
            fail_flag = "yes";
            return
        end
        if exist('elbqtrs') == 1
            if asymqtrs > elbqtrs
                disp("error: asymqtrs>elbqtrs");
                fail_flag = "yes";
                return
            end
        end
    end
else
    if exist('asymqtrs') == 1
        disp("warning: asymqtrs set by user but not needed");
    end
end


% If the ELB constraint is imposed, set predqtrs (the number of
% quarters requiring additive adjustments to the path of the
% federal funds rate) to elbqtrs. If the ELB constraint is not
% imposed and one of the nonlinear policy rules is used, set
% predqtrs equal asymqtrs. If no ELB constraint is imposed on a
% linear rule, set predqtrs equal to zero.

if strcmp(elb_imposed,"yes")
    predqtrs = elbqtrs;
else
    if strcmp(mprule,"adur") | strcmp(mprule,"aait")
        predqtrs = asymqtrs;
    else
        predqtrs = 0;
    end
end


% The default setting is that no unemployment threshold is
% imposed on liftoff from the ELB. If the user has optionally
% imposed one, verify that its value has been defined.

if exist('uthresh_imposed') == 0
    uthresh_imposed = "no";
else
    if strcmp(uthresh_imposed,"yes") == 0 & strcmp(uthresh_imposed,"no") == 0
        a = "error: invalid setting for uthresh_imposed, ";
        a = a + "must be yes, no or not defined";
        disp(a);
        fail_flag = "yes";
        return
    end
end
if strcmp(uthresh_imposed,"no") & exist('uthresh')==1
    disp("warning: uthresh defined by user but U threshold not imposed");
end
if strcmp(uthresh_imposed,"yes") & exist('uthresh')==0
    disp("error: no value defined for uthresh");
    fail_flag = "yes";
    return
end
if strcmp(uthresh_imposed,"yes") & strcmp(elb_imposed,"yes") == 0
    disp("error: ELB must be imposed to use thresholds");
    fail_flag = "yes";
    return
end


    
% The default setting is that no inflation threshold is imposed on
% liftoff from the ELB. If the user has optionally imposed one,
% verify that its value and measure have been defined

if exist('pithresh_imposed') == 0
    pithresh_imposed = "no";
else
    if strcmp(pithresh_imposed,"yes")== 0 & strcmp(pithresh_imposed,"no") == 0
        a = "error: invalid setting for pithresh_imposed, ";
        a = a + "must be yes, no or not defined";
        disp(a);
        fail_flag = "yes";
        return
    end
end
if strcmp(pithresh_imposed,"no") 
    if exist('pithresh')==1
        a = "warning: pithresh defined by user but PI ";
        a = a + "threshold not imposed";
        disp(a);            
    end
    if exist('pithresh_var')==1
        a="warning: pithresh_var defined by user ";
        a = a + "but PI threshold not imposed";
        disp(a);
    end
end
if strcmp(pithresh_imposed,"yes") 
    if exist('pithresh')==0
        disp("error: no value defined for pithresh");
        fail_flag = "yes";
        return
    end
    if exist('pithresh_var')==0
        disp("error: pithresh_var not defined");
        fail_flag = "yes";
        return
    else

    a = {'pic4','pic12','pic20','picx4','picx12','picx20'}; 
        if isempty(find(strcmp(pithresh_var,a))) == 1
            disp("error: invalid pithresh_var setting");
            fail_flag = "yes";
            return
        end
    end
end
if strcmp(pithresh_imposed,"yes") & strcmp(elb_imposed,"yes") == 0
    disp("error: ELB must be imposed to use thresholds");
    fail_flag = "yes";
    return
end



% If one threshold has been imposed but the other has not, simplify
% the coding of the solution algorithm by imposing the other
% threshold with a value that it ensures it will never bind

thresh_case = 0;
if strcmp(uthresh_imposed,"yes") & strcmp(pithresh_imposed,"no")
    thresh_case = 1;
end
if strcmp(uthresh_imposed,"no") & strcmp(pithresh_imposed,"yes")
    thresh_case = 2;
end
if thresh_case == 1
    pithresh_imposed = "yes";
    pithresh = -9999;
    pithresh_var = "picx4";
end
if thresh_case == 2
    uthresh_imposed = "yes";
    uthresh = 9999;
end


% If either threshold has been imposed, set the maximum length the
% commitment is imposed (maxfgq) equal to its default predqtrs
% unless it has already been defined by the user, in which case
% verify that the user-supplied setting is valid

if strcmp(uthresh_imposed,"yes") | strcmp(pithresh_imposed,"yes")
    if exist('maxfgq') == 0
        maxfgq = predqtrs;
    else
        if maxfgq < 1 | maxfgq > predqtrs
            disp("error: maxfgq not between 1 and predqtrs");
            fail_flag = "yes";
            return
        end
    end
end


% If the ELB is imposed, the default setting is that the ECFS
% option is used with a floor on the projected output gap equal to
% -15 percent. If the ELB is not imposed, the ECFS option is not
% permitted.
    
if exist('ecfs_option') == 0 
    if strcmp(elb_imposed,"no")
        ecfs_option = "no";
    else
        ecfs_option = "yes";
    end
end
if strcmp(ecfs_option,"no") & exist('ecfs_floor') > 0
    disp('warning: ecfs_floor defined by user but ecfs not used');
end
if exist('ecfs_floor') == 0 & strcmp(ecfs_option,'yes')
    ecfs_floor = -15;
end
if strcmp(ecfs_option,"yes") & strcmp(elb_imposed,"no")
    disp("warning: ELB not imposed so ECFS option is turned off");
    ecfs_option = "no";
end

% The default setting for cyclical term premium effects is to use
% the ones embedded in the standard model equations (ctp_option=0)
% but the user can opt to either suppress these effects
% (ctp_option=1) or override them with a specification less likely
% to make the model unstable (ctp_option=2)

if exist('ctp_option') == 0
    ctp_option = 0;
end
if ctp_option~=0 & ctp_option~=1 & ctp_option~=2
    a = "Error: invalid setting for ctp_option, ";
    a = a + "must equal 0, 1, or 2";
    disp(a);
    fail_flag = "yes";
    return
end


% The default setting for the cyclicality of the trend personal tax
% rate, tax_gamma, is .00130 if expvers equals mceall and .00075
% otherwise 

if exist('tax_gamma') == 0
    if strcmp(expvers,"mceall") 
        tax_gamma = .00130;
    else
        tax_gamma = .00075;
    end
end
if tax_gamma < 0
    disp("Error: tax_gamma must be greater than zero");
    fail_flag = "yes";
    return
end
if tax_gamma ~= .00075 & tax_gamma ~= .00130
    disp("Warning: tax_gamma set to non-standard value");
end


% If user-supplied settings for the stochastic simulation
% parameters have not been defined, set them equal to their
% defaults. 

if exist('nreplic') == 0
    nreplic = 5000;
end

if exist('nsimqtrs') == 0
    nsimqtrs = 200;
else
    if nsimqtrs < 101
        a = "nsimqtrs<101, so no steady-state simulated";
        a = strcat(a," distributional statistics will be computed");
        disp(a);
    end
end

track_names = {'xgap2','lur','ugap','lep_l','pic4','picx4', ...
              'rff','rg10'};
if exist('add_track_names') == 1
    track_names = horzcat(track_names,add_track_names);
end

if exist('residuals_file') == 0
    residuals_file = 'hist_residuals.txt';
end

if exist('draw_method') == 0
    draw_method = "state";
else
    valid_meths = {'boot','state','mvnorm'};
    if isempty(find(strcmp(draw_method,valid_meths))) == 1
        disp("Error: invalid sampling method selected");
        fail_flag = "yes";
        return
    end
end

if exist('rescale_wpshocks') == 0
    rescale_wpshocks = "yes";
else
    yesno = {"yes","no"};
    if isempty(find(strcmp(rescale_wpshocks,yesno))) == 1
        disp("Error: rescale_wpshocks must be either yes or no"); 
        fail_flag = "yes";
        return
    end
end

if exist('save_option') == 0
    save_option = "no";
else
    if strcmp(save_option,"full")==0 & strcmp(save_option,"limited") == 0
        disp("Error: invalid setting for save_option");
        fail_flag = "yes";
        return
    else
        if exist('save_name') == 0
            save_name = "stochsims_results";
        end
    end
end





