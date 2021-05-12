import pandas as pd
import os, sys

def shimadzu_to_df (txt_file_path: str, flow_rate=1.0, out_type='fl') :
    '''Takes a .txt file generated by LabSolutions with a Shimadzu HPLC and
    returns a pandas dataframe of first uv points and then fl points.
    Optional arguments: flow rate in ml/min. Default: 1.0'''

    # only works if file name has only a number in it. Maybe rethink and generalize
    sample_num = int(txt_file_path.rpartition('/')[2].replace('.txt', ''))
    sample_name = f'{sample_num:02}'

    uv_name = '[LC Chromatogram(Detector A-Ch1)]'
    fl_name = '[LC Chromatogram(Detector B-Ch1)]'
    points_name = '# of Points'
    start_name = 'R.Time (min)	Intensity'

    with open(txt_file_path, 'r') as f:
        uv_yes = False
        fl_yes = False
        # find the line_num of uv and fl start and end
        for line_num, line in enumerate(f) :
            if uv_name in line :
                uv_yes = True
            elif start_name in line and uv_yes :
                uv_start = line_num
                uv_yes = False
            elif fl_name in line :
                fl_yes = True
            elif start_name in line and fl_yes :
                fl_start = line_num
                fl_yes = False
            elif points_name in line :
                nr_of_points = int(line.split()[3])
            max_line = line_num

    # read data frames from file
    if out_type == 'uv' :
        data_start = uv_start
        label = f'uv.{sample_name}'
    elif out_type == 'fl' :
        data_start = fl_start
        label = f'fl.{sample_name}'

    # create list of lines to skip for pd.read_table to not use skipfooter to be able to use c-engine
    skr = [ x for x in range(max_line) if x <= data_start or x > (data_start + nr_of_points) ]

    df = pd.read_table(txt_file_path, skiprows=skr, header=None)
    df.iloc[:,0] = df.iloc[:,0] * flow_rate
    df.columns = ['ret.t.ml.min', label]
    df = df.set_index('ret.t.ml.min')
    return df

def shimadzu_to_csv_batch(dir: str, flow_rate: float, out_type: str) :
    '''Applies shimadzu_to_df on all Shimadzu .txt files in a directory.'''

    dir_list = os.listdir(dir)

    out_df_list = []
    for file in dir_list :
        if '.txt' in file :
            out_df_list.append(shimadzu_to_df(f'{dir}/{file}', flow_rate, out_type))

    out_df = pd.concat(out_df_list, axis=1)
    out_df = out_df.sort_index(axis=1)

    out_df.to_csv(f'{dir}/processed.csv')
    return f'{dir}/processed.csv'

if __name__ == '__main__' :

    dir = ''

    dir = input('\nPlease enter directory name:\n').replace('\\', '').rstrip()

    while os.path.isdir(dir) == False :
        dir = input('Input not a directory. Try again: ').replace('\\', '').rstrip()

    num_of_files = len(os.listdir(dir))
    print(f'\n{num_of_files} files found in this directory.')

    try :
        flow_rate = float(input('\nPlease enter the flow rate as ml/min (defaults to 1.0 if left empty):\n'))
    except ValueError :
        flow_rate = 1.0

    out_type = input('\nWhich traces do you want? UV (\'uv\') or fluorescence (\'fl\')?\n(Defaults to \'fl\' if left empty)\n')
    if out_type.strip() == '' :
        out_type = 'fl'

    shimadzu_to_csv_batch(dir, flow_rate, out_type)

    print(f'\nSuccess! {num_of_files} files have been processed. The results are found in:\n{dir}/processed.csv\n')

    # if open == True :
    #     subprocess.call(['open', '-R', shimadzu_to_csv_batch(dir)])
    # else :
    #     shimadzu_to_csv_batch(dir)
