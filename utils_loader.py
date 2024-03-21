import os
from matplotlib import pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split
import torch
from TaskSampler import TaskSampler
import pandas as pd
from metrics import find_mid, find_transitions
from utilities import printc, sliding_windows
from utils_dataset import ClassificationDataset, CustomDataset, NormalDataset
from torch.utils.data import Dataset, DataLoader
import numpy as np
from scipy.signal import butter, lfilter, freqz
def butter_lowpass(cutoff, fs, order=5):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)
def low_pass_filter(data, cutoff, fs, order=5):
    """
    Apply a low-pass filter to the data.

    Parameters:
    - data: numpy array of shape (N, 6), where N is the number of data points.
    - cutoff: The cutoff frequency of the filter (Hz).
    - fs: The sampling rate of the data (Hz).
    - order: The order of the filter.

    Returns:
    - filtered_data: The filtered data, numpy array of shape (N, 6).
    """
    # Design the Butterworth filter
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter_lowpass(cutoff, fs, order=order)

    # Apply the filter to each channel
    smoothed_filtered_data = np.zeros_like(data)
    for i in range(data.shape[1]):  # Assuming data shape is (N, 6)
        filtered_data = lfilter(b, a, data[:, i])
        smoothed_filtered_data[:, i] = np.convolve(filtered_data, np.ones(10)/10, mode='same')
    return smoothed_filtered_data

def get_e2_e4():
    folder = './datasets/physiq/segment_sessions_one_repetition_data_E2'
    files = []
    dict_mapping = dict()
    for file in os.listdir(folder):
        if '.csv' not in file:
            continue
        if '120' not in file:
            continue
        files.append(file)
        subject = file.split('_')[1]
        if subject not in dict_mapping:
            dict_mapping[subject] = [file]
        else:
            dict_mapping[subject].append(file)
            
    inputs = []
    labels = []
    for k, v in dict_mapping.items():
        v = sorted(v)
        v_concat = []
        for i in v:
            path_file = os.path.join(folder, i)
            df = pd.read_csv(path_file)
            v_concat.append(df.iloc[:, 1:7].values)
        e2 = np.concatenate(v_concat, axis=0)
        inputs.append(e2)
        labels.append([0] * e2.shape[0]) # e2
    
    folder = './datasets/physiq/segment_sessions_one_repetition_data_E4'
    files = []
    dict_mapping = dict()
    for file in os.listdir(folder):
        if '.csv' not in file:
            continue
        if '120' not in file:
            continue
        files.append(file)
        subject = file.split('_')[1]
        if subject not in dict_mapping:
            dict_mapping[subject] = [file]
        else:
            dict_mapping[subject].append(file)
    
    for k, v in dict_mapping.items():
        v = sorted(v)
        v_concat = []
        for i in v:
            path_file = os.path.join(folder, i)
            df = pd.read_csv(path_file)
            v_concat.append(df.iloc[:, 1:7].values)
        e4 = np.concatenate(v_concat, axis=0)
        inputs.append(e4)
        labels.append([1] * e4.shape[0])
    inputs = np.concatenate(inputs, axis=0)
    labels = np.concatenate(labels, axis=0)
    return inputs, labels
    

def get_e2_e4():
    folder = './datasets/physiq/segment_sessions_one_repetition_data_E2'
    files = []
    dict_mapping = dict()
    for file in os.listdir(folder):
        if '.csv' not in file:
            continue
        if '120' not in file:
            continue
        files.append(file)
        subject = file.split('_')[1]
        if subject not in dict_mapping:
            dict_mapping[subject] = [file]
        else:
            dict_mapping[subject].append(file)
            
    inputs = []
    labels = []
    for k, v in dict_mapping.items():
        v = sorted(v)
        v_concat = []
        v_label = []
        for i in v:
            path_file = os.path.join(folder, i)
            df = pd.read_csv(path_file)
            # add a -1 label at the end of the first half and add another last value of input to the input to match the length:
            v_concat.append(np.append(df.iloc[:, 1:7].values, df.iloc[-1::, 1:7].values, axis=0))
            v_label.append([0] * df.shape[0] + [2])
        e2 = np.concatenate(v_concat, axis=0)
        e2_label = np.concatenate(v_label, axis=0)
        printc(e2.shape, e2_label.shape)
        inputs.append(e2)
        labels.append(e2_label) # e2
    
    folder = './datasets/physiq/segment_sessions_one_repetition_data_E4'
    files = []
    dict_mapping = dict()
    for file in os.listdir(folder):
        if '.csv' not in file:
            continue
        if '120' not in file:
            continue
        files.append(file)
        subject = file.split('_')[1]
        if subject not in dict_mapping:
            dict_mapping[subject] = [file]
        else:
            dict_mapping[subject].append(file)
    
    for k, v in dict_mapping.items():
        v = sorted(v)
        v_concat = []
        v_label = []
        for i in v:
            path_file = os.path.join(folder, i)
            df = pd.read_csv(path_file)
            v_concat.append(np.append(df.iloc[:, 1:7].values, df.iloc[-1::, 1:7].values, axis=0))
            v_label.append([1] * df.shape[0] + [2])
        # v_concat.insert(len(v_concat), v_concat[0][:len(v_concat[0])//2])
        # v_concat[0] = v_concat[0][len(v_concat[0])//2:]
        e4 = np.concatenate(v_concat, axis=0)
        e4_label = np.concatenate(v_label, axis=0)
        inputs.append(e4)
        labels.append(e4_label) # e2
        
    inputs = np.concatenate(inputs, axis=0)
    labels = np.concatenate(labels, axis=0)
    # low pass filter:
    # print(inputs.shape)
    # inputs = low_pass_filter(inputs, 10, 50)
    # print(inputs.shape)
    

    return inputs, labels
    

def get_e2_e2prime():
    # e2 is regulr exercise: [0, 200], [200, 400] for example
    # e2 prime is the starting at half and ending at the next half: [100, 300], [300, 0-100]
    folder = './datasets/physiq/segment_sessions_one_repetition_data_E2'
    files = []
    dict_mapping = dict()
    for file in os.listdir(folder):
        if '.csv' not in file:
            continue
        if '120' not in file:
            continue
        files.append(file)
        subject = file.split('_')[1]
        if subject not in dict_mapping:
            dict_mapping[subject] = [file]
        else:
            dict_mapping[subject].append(file)
            
    # permute the order:
    # np.random.shuffle(files)
    inputs = []
    labels = []
        
    # e2 prime:
    for k, v in dict_mapping.items():
        v = sorted(v)
        v_concat = []
        for i in v:
            path_file = os.path.join(folder, i)
            df = pd.read_csv(path_file)
            v_concat.append(df.iloc[:, 1:7].values)
        e2 = np.concatenate(v_concat, axis=0)
        # move v_concat[0][:len(v_concat[0])//2] to the end:
        v_concat.insert(len(v_concat), v_concat[0][:len(v_concat[0])//2])
        v_concat[0] = v_concat[0][len(v_concat[0])//2:]
        e2_prime = np.concatenate(v_concat, axis=0)
        inputs.append(e2_prime)
        labels.append([1] * e2_prime.shape[0]) # e2 prime
        
        inputs.append(e2)
        labels.append([0] * e2.shape[0]) # e2
        
    inputs = np.concatenate(inputs, axis=0)
    labels = np.concatenate(labels, axis=0)
    return inputs, labels
from torch.utils.data import SubsetRandomSampler
def test_idea_dataloader_er_ir(config):
    
    inputs, labels = get_e2_e4()
    sw = sliding_windows(config['window_size'], config['step_size'])
    is_middle = find_mid(labels, config['window_size'], config['step_size'], dense_label=True)
    segmented_samples, segmented_labels = sw(torch.tensor(inputs), torch.tensor(labels))
    assert len(segmented_labels) == len(is_middle), 'Length of labels and is_middle do not match {} and {}'.format(len(segmented_labels), len(is_middle))
    segmented_labels = list(zip(segmented_labels, is_middle))

    # Split the dataset into train, val and test:
    train_samples, test_samples, train_labels, test_labels = train_test_split(segmented_samples, segmented_labels, test_size=0.5, random_state=42)
    # unzip:
    train_labels, _ = zip(*train_labels)
    test_labels, test_middle = zip(*test_labels)
    
    test_transitions = find_transitions(test_labels, config['window_size'], config['step_size'], dense_label=False)

    test_labels = list(zip(test_labels, list(zip(test_transitions, test_middle))))
    # val split:
    train_samples, val_samples, train_labels, val_labels = train_test_split(train_samples, train_labels, test_size=0.2, random_state=42)
    
    train_set = ClassificationDataset(train_samples, train_labels)
    val_set = ClassificationDataset(val_samples, val_labels)
    test_set = ClassificationDataset(test_samples, test_labels)
    # subsample the dataset:
    # printc('Train set size:', train_samples.shape, 'Val set size:', val_samples.shape, 'Test set size:', test_samples.shape)
    # train_sampler = SubsetRandomSampler(list(range(0, len(train_samples), 500)))
    # # val:
    # val_sampler = SubsetRandomSampler(list(range(0, len(val_samples), 500)))
    train_loader = DataLoader(
        train_set,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0,
        pin_memory=True,
        # sampler=train_sampler
        )
    val_loader = DataLoader(
        val_set,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0,
        pin_memory=True,
        # sampler=val_sampler
        )
    test_loader = DataLoader(
        test_set,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0,
        pin_memory=True,)
    return train_loader, val_loader, test_loader
    
    

from sklearn.preprocessing import LabelEncoder
        
def test_idea_dataloader_burpee_pushup(config):
    item = np.load('./datasets/WEAR/inertial.npy', allow_pickle=True)
    inputs, labels = item.item()['data'], item.item()['labels']
    le = LabelEncoder().fit(labels)
    labels = le.transform(labels)
    is_middle = find_mid(labels, config['window_size'], config['step_size'], dense_label=True)
    sw = sliding_windows(config['window_size'], config['step_size'])
    segmented_samples, segmented_labels = sw(torch.tensor(inputs), torch.tensor(labels))
    assert len(segmented_labels) == len(is_middle), 'Length of labels and is_middle do not match {} and {}'.format(len(segmented_labels), len(is_middle))
    segmented_labels = list(zip(segmented_labels, is_middle))
    # Split the dataset into train, val and test:
    train_samples, test_samples, train_labels, test_labels = train_test_split(segmented_samples, segmented_labels, test_size=0.5, random_state=42)
    # unzip:
    train_labels, _ = zip(*train_labels)
    test_labels, test_middle = zip(*test_labels)
    # transition:
    test_transitions = find_transitions(test_labels, config['window_size'], config['step_size'], dense_label=False)
    
    test_labels = list(zip(test_labels, list(zip(test_transitions, test_middle))))
    # val split:
    train_samples, val_samples, train_labels, val_labels = train_test_split(train_samples, train_labels, test_size=0.2, random_state=42)
    train_set = ClassificationDataset(train_samples, train_labels)
    val_set = ClassificationDataset(val_samples, val_labels)
    test_set = ClassificationDataset(test_samples, test_labels)
    # subsample the dataset:
    # printc('Train set size:', train_samples.shape, 'Val set size:', val_samples.shape, 'Test set size:', test_samples.shape)
    # train_sampler = SubsetRandomSampler(list(range(0, len(train_samples), 500)))
    # # val:
    # val_sampler = SubsetRandomSampler(list(range(0, len(val_samples), 500)))
    train_loader = DataLoader(
        train_set,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0,
        pin_memory=True,
        # sampler=train_sampler
        )
    val_loader = DataLoader(
        val_set,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0,
        pin_memory=True,
        # sampler=val_sampler
        )
    test_loader = DataLoader(
        test_set,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0,
        pin_memory=True,)
    return train_loader, val_loader, test_loader
            
            
            
    
    
    
from sklearn.model_selection import LeavePGroupsOut

def get_dataloaders(config):
    if config['fsl']:
        return fsl_dataloaders(config)
    else:
        return non_fsl_dataloaders(config)

def non_fsl_dataloaders(config):
    """
    Get dataloaders for the train, val, test sets for non-FSL

    Args:
        config (_type_): NA
    """
    inputs, labels, users = _load(config)
    inputs = np.array(inputs, dtype=np.object_)
    labels = np.array(labels, dtype=np.object_)
    users = np.array(users)
    sw = sliding_windows(config['window_size'], config['step_size'])
    if config['cross_subject']['enabled']:
        lpgo = LeavePGroupsOut(n_groups=config['cross_subject']['n_groups'])
        num_splits = lpgo.get_n_splits(inputs, labels, users)
        printc('Number of splits:', num_splits)
        # only get the first split:
        train_index, test_index = next(iter(lpgo.split(inputs, labels, users)))
        # split train-val on index:
        
        train_index, val_index = train_test_split(train_index, test_size=0.1, random_state=config['seed'])
        # percentage of train, val, and test:
        printc('Cross Validation info on Train:', len(train_index) / len(inputs), 'Val:', len(val_index) / len(inputs), 'Test:', len(test_index) / len(inputs))
        train_samples, train_labels = inputs[train_index], labels[train_index]
        val_samples, val_labels = inputs[val_index], labels[val_index]
        test_samples, test_labels = inputs[test_index], labels[test_index]
        # concat:
        train_samples = np.concatenate(train_samples, axis=0)
        train_labels = np.concatenate(train_labels, axis=0)
        val_samples = np.concatenate(val_samples, axis=0)
        val_labels = np.concatenate(val_labels, axis=0)
        test_samples = np.concatenate(test_samples, axis=0)
        test_labels = np.concatenate(test_labels, axis=0)
        # add the where the transition is:
        test_transitions = find_transitions(test_labels, config['window_size'], config['step_size'], dense_label=True)
        train_samples, train_labels = sw(torch.tensor(train_samples), torch.tensor(train_labels))
        val_samples, val_labels = sw(torch.tensor(val_samples), torch.tensor(val_labels))
        test_samples, test_labels = sw(torch.tensor(test_samples), torch.tensor(test_labels))
        test_labels = list(zip(test_labels, test_transitions))
       
        
        
    else:        
        segmented_samples, segmented_labels = sw(torch.tensor(inputs), torch.tensor(labels))
        # Split the dataset into train, val and test:
        train_samples, test_samples, train_labels, test_labels = train_test_split(segmented_samples, segmented_labels, test_size=0.2, random_state=42)
        train_samples, val_samples, train_labels, val_labels = train_test_split(train_samples, train_labels, test_size=0.2, random_state=42)
    train_set = NormalDataset(train_samples, train_labels)
    val_set = NormalDataset(val_samples, val_labels)
    test_set = NormalDataset(test_samples, test_labels)
    train_loader = DataLoader(
        train_set,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0,
        pin_memory=True,)
    val_loader = DataLoader(
        val_set,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0,
        pin_memory=True,)
    test_loader = DataLoader(
        test_set,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0,
        pin_memory=True,)
    return train_loader, val_loader, test_loader
        
    


    

def fsl_dataloaders(config):
    """
    Get dataloaders for the train and test sets for FSL

    :param config: A dictionary containing the following keys:
        - 'n_way': Number of classes in a task
        - 'n_shot': Number of support examples per class in a task
        - 'n_query': Number of query examples per class in a task
        - 'n_tasks_per_epoch': Number of tasks per epoch
    :return: A tuple of (train_loader, test_loader)
    """
    # Load the dataset
    raise NotImplementedError('FSL dataloaders not implemented correctly due to users variable added in physqics')
    inputs, labels = _load(config)
    sw = sliding_windows(300, 50)
    segmented_samples, segmented_labels = sw(torch.tensor(inputs), torch.tensor(labels))
    # Split the dataset into train, val and test:
    train_samples, test_samples, train_labels, test_labels = train_test_split(segmented_samples, segmented_labels, test_size=0.5, random_state=42)
    # val split:
    # train_samples, val_samples, train_labels, val_labels = train_test_split(train_samples, train_labels, test_size=0.2, random_state=42)
    train_set = CustomDataset(train_samples, train_labels)
    # val_set = CustomDataset(val_samples, val_labels)
    test_set = CustomDataset(test_samples, test_labels)
    # train_set = CustomDataset(segmented_samples, segmented_labels)
    n_way = config['n_way']
    n_shot = config['n_shot']
    n_query = config['n_query']
    n_tasks_per_epoch = config['n_tasks_per_epoch']
    allowed_label = config['allowed_label']
    batch_size = config['batch_size']
    train_sampler = TaskSampler(train_set, allowed_label, n_way, n_shot, batch_size, n_query, n_tasks_per_epoch)
    train_loader = DataLoader(
        train_set,
        batch_sampler=train_sampler,
        num_workers=0,
        pin_memory=True,
        collate_fn=train_sampler.episodic_collate_fn,
    )
    # val_loader = DataLoader(
    #     val_set,
    #     batch_sampler=train_sampler,
    #     num_workers=0,
    #     pin_memory=True,
    #     collate_fn=wrapped_collate_fn,
    # )
    test_loader = DataLoader(
        test_set,
        batch_sampler=train_sampler,
        num_workers=0,
        pin_memory=True,
        collate_fn=train_sampler.episodic_collate_fn,
    )
    return train_loader, test_loader


def _load(config):
    if config['dataset']['name'].lower() == 'physiq_e1':
        return _load_physiq_e1()
    elif config['dataset']['name'].lower() == 'physiq_e2':
        return _load_physiq_e2()
    elif config['dataset']['name'].lower() == 'physiq_e3':
        return _load_physiq_e3()
    elif config['dataset']['name'].lower() == 'opportunity':
        raise NotImplementedError('Opportunity dataset not implemented correctly in the dataClean.py with users variable')
        return _load_opportunity()
    else:
        raise ValueError(f'Unknown dataset: {config["dataset"]}')
    
def _load_physiq_e1():
    inp = np.load('./datasets/physiq/physiq_permute_e1.npy', allow_pickle=True)
    inputs, labels, users = inp.item()['inputs'], inp.item()['labels'], inp.item()['users']
    return inputs, labels, users

def _load_physiq_e2():
    inp = np.load('./datasets/physiq/physiq_permute_e2.npy', allow_pickle=True)
    inputs, labels, users = inp.item()['inputs'], inp.item()['labels'], inp.item()['users']
    return inputs, labels, users

def _load_physiq_e3():
    inp = np.load('./datasets/physiq/physiq_permute_e3.npy', allow_pickle=True)
    inputs, labels, users = inp.item()['inputs'], inp.item()['labels'], inp.item()['users']
    return inputs, labels, users


def _load_opportunity():
    inp = np.load('./datasets/OpportunityUCIDataset/loco_2_mask.npy', allow_pickle=True)
    inputs, labels = inp.item()['inputs'], inp.item()['labels']
    return inputs, labels
    
class MultiEpochsDataLoader(torch.utils.data.DataLoader):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._DataLoader__initialized = False
        self.batch_sampler = _RepeatSampler(self.batch_sampler)
        self._DataLoader__initialized = True
        self.iterator = super().__iter__()

    def __len__(self):
        return len(self.batch_sampler.sampler)

    def __iter__(self):
        for i in range(len(self)):
            yield next(self.iterator)


class _RepeatSampler(object):
    """ Sampler that repeats forever.

    Args:
        sampler (Sampler)
    """

    def __init__(self, sampler):
        self.sampler = sampler

    def __iter__(self):
        while True:
            yield from iter(self.sampler)