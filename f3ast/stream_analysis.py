import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def read_stream_file( filename ):
    """ Read stream file, and return pandas dataframe. """
    
    data = pd.read_csv(
        filename, 
        skiprows=3, skipfooter=1, 
		sep='\s+', engine='python', 
        names = ['t', 'x', 'y']
        )
    
    # time in milliseconds (time steps defined in multiples of 100 ns...)
    data['t'] = data['t'] * 0.1e-6 
    
    return data


def plot_stream_file(filename, savefig=False):
    """ 
    Plot stream file xy distribution and dwell time statistics.
    
    Args:
    filename: filename of stream file (including extension)
    savefig: True/False - will be saved under the same name/path as the input file
    """
    
    data = read_stream_file( filename )
    aspect_ratio_ax0 = (np.max(data['x']) - np.min(data['x'])) / (np.max(data['y']) - np.min(data['y']))
    fig, axes = plt.subplots( figsize=(4*(1+aspect_ratio_ax0), 4*1), ncols=2, width_ratios=(aspect_ratio_ax0, 1.) )  
    fig.suptitle(filename)

    # stream distribution in xy
    axes[0].set_aspect('equal')
    axes[0].axis('off')
    grouped_data = data.groupby(['x', 'y'], as_index=False).sum()
    cdata = axes[0].hexbin( grouped_data['x'], grouped_data['y'], C=grouped_data['t'], cmap=plt.cm.viridis )
    plt.colorbar(cdata, shrink=0.8, ax=axes[0], label='net dwell time (ms)')

    # histogram
    axes[1].set_title('dwell time distribution')
    axes[1].hist( 1e3 * data['t'], bins='rice', 
        label=f'net time {np.sum(data["t"]):.1f} s\n{len(data)} commands')
    axes[1].set_xlabel('Dwell time [ms]')
    axes[1].legend(loc='best')
    axes[1].yaxis.tick_right()
    axes[1].yaxis.set_label_position("right")

    plt.tight_layout()
    
    if savefig:
        plt.savefig(f'{filename[:-4]}.png', dpi=200, bbox_inches='tight', transparent=True)

    return None