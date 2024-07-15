1. No interventions:
- beta: 0.13
- death_prop: 2.67

2. Lockdown (50%) - no vaccine:
- beta: 0.06
- death_prob: 1.18




Download the epidemiology.csv file from https://health.google.com/covid-19/open-data/

For calibration to run, go to analysis.py in the covasim package and edit the remove_db function:

def remove_db(self):
        '''
        Remove the database file if keep_db is false and the path exists.

        New in version 3.1.0.
        '''
        def is_file_open(file_path):
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for item in proc.open_files():
                        if file_path == item.path:
                            return proc
                except Exception:
                    continue
            return None
    
        try:
            op = import_optuna()
            op.delete_study(study_name=self.run_args.name, storage=self.run_args.storage)
            if self.verbose:
                print(f'Deleted study {self.run_args.name} in {self.run_args.storage}')
        except Exception as E:
            print('Could not delete study, skipping...')
            print(str(E))
        if os.path.exists(self.run_args.db_name):
            try:
                os.remove(self.run_args.db_name)
                if self.verbose:
                    print(f'Removed existing calibration {self.run_args.db_name}')
            except Exception as E:
                print(str(E))
                proc = is_file_open(self.run_args.db_name)
                if proc:
                    print(f'The file is currently being used by process {proc.info["name"]} (PID: {proc.info["pid"]}).')
                    proc.terminate()
                    proc.wait() 
                    print(f'Terminated process {proc.info["name"]} (PID: {proc.info["pid"]}).')
        return
