import os
import h5py
import numpy as np
import json
import pickle as pkl

import tensorflow as tf
import tensorflow.contrib.eager as tfe

import librosa
import pydub
from pyAudioAnalysis import audioBasicIO as aIO
from pyAudioAnalysis import audioSegmentation as aS

import CRNN
import utils


#Tensorflow initialization
gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=1.0)
config = tf.ConfigProto(gpu_options=gpu_options,intra_op_parallelism_threads=1)
config.gpu_options.allow_growth = True
tf.enable_eager_execution(config=config,device_policy=tfe.DEVICE_PLACEMENT_SILENT)

#current model name ckpt128logmel_2conv-74

#extract features

def extract_feature2d_file(file_name,num_mfcc=40):
    X, sample_rate = librosa.load(file_name)
    stft = np.abs(librosa.stft(X))
    mel = librosa.feature.melspectrogram(X, sr=sample_rate, hop_length=int(0.015*sample_rate), n_fft= int(0.030*sample_rate))
    log_mel=librosa.core.power_to_db(mel)
    mfccs = librosa.feature.mfcc(S=librosa.power_to_db(mel), n_mfcc=num_mfcc)  #using precomputed mel spectrograms for mfcc computation
    chroma = librosa.feature.chroma_stft(S=stft, sr=sample_rate)
    contrast = librosa.feature.spectral_contrast(S=stft, sr=sample_rate)
    tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(X),
    sr=sample_rate,chroma=chroma)      # all the features are [feat_, sample points]  frame duration= 30ms with 15 ms overlap
    return mfccs,chroma,mel,contrast,tonnetz,log_mel,X, sample_rate


def feat_ext(file_path,file_name):
    if file_name.endswith(".wav"):
        mfccs, chroma, mel, contrast,tonnetz,log_mel,X, sample_rate= extract_feature2d_file(os.path.join(file_path, file_name),num_mfcc=40)
    else:
        print("File type not supported!")

    ## TODO: Currently just use log_mel_spectogram
    return mfccs,X,sample_rate


def normalization(tensor_in, epsilon=.0001):
    tensor_in=tf.reshape(tensor_in,[-1,utils.input_dim,utils.time_steps])
    mean,variance = tf.nn.moments(tensor_in,axes=[1],keep_dims=1)
    tensor_normalized = (tensor_in-mean)/(variance+tf.cast(epsilon,tf.float64))

    return tensor_normalized


def compute_timeline(logits,pad,contiguous,random_wins):
    """
    :return: return start and ending time of zeros in logit
    """

    segments=[]
    logits_class_id=tf.argmax(logits,axis=1)
    idx=0
    logits_class_id=np.array(logits_class_id)
    list_logits_class_id=list(logits_class_id)
    seq_logits_class_id=list_logits_class_id[0].reshape(1,-1)

    for arr in list_logits_class_id[1:contiguous]:
        seq_logits_class_id=np.concatenate((seq_logits_class_id,arr.reshape(1,-1)),axis=1)

    if pad>0:
        seq_logits_class_id= seq_logits_class_id.reshape(-1)[:-pad]
    else:
        seq_logits_class_id= seq_logits_class_id.reshape(-1)

    for i in range(len(list_logits_class_id[contiguous:])):
        logits_idx=i+contiguous
        curr_logits=list_logits_class_id[logits_idx].reshape(-1)
        idx=0
        while idx < len(curr_logits):
            if curr_logits[idx]==1:
                idx+=1
                continue
            else:
                start_idx=idx+random_wins[i][0]
                while idx < len(curr_logits) and curr_logits[idx] !=1:
                    idx+=1
                end_idx=idx+random_wins[i][0]-1
                if end_idx >= len(seq_logits_class_id):
                    end_idx=len(seq_logits_class_id)-1        #this should take care of the extra pad
                seq_logits_class_id[start_idx:end_idx]=0

    while idx < len(seq_logits_class_id):
        if seq_logits_class_id[idx]==1:
            idx+=1
            continue
        else:
            start_idx=idx
            while idx < len(seq_logits_class_id) and seq_logits_class_id[idx] !=1:
                idx+=1
            end_idx=idx-1
            #if end_idx-start_idx>6:
            start_time=(start_idx-2)*15
            end_time=(end_idx+1)*15
            if end_time-start_time>100:
                segments.append((start_time,end_time))
    
    return segments

def call_umm_segmentation(features,pad,contiguous,random_wins):
    '''
    Parameters
    ----------
    list of features in size (128,201)
    length of padding
    number of contiguous segments
    [(start,end)] for all the random windows
    '''

    model=CRNN.Model(utils.hidden_dim,utils.num_layers,utils.input_dim)
    # load checkpoint
    checkpoint_prefix = os.path.join(utils.model_dir, utils.model_name)

    step_counter = tf.train.get_or_create_global_step()
    checkpoint = tfe.Checkpoint(
        model=model, step_counter=step_counter)

    if tf.train.checkpoint_exists(checkpoint_prefix):
        checkpoint.restore(checkpoint_prefix)
    norm_feats=normalization(tf.convert_to_tensor(features))
    logit = model(norm_feats, training=False)
    time_segments = compute_timeline(logit,pad,contiguous,random_wins)

    return time_segments

def segment_feat(features):
    """
    Parameters
    ----------
    features of the entire audio segment

    Returns
    -------
        list of features in size (128,201)
        length of padding
        number of contiguous segments
        [(start,end)] for all the random windows
    """
    #pad with zeros to make divisable by 201
    cols=features.shape[1]
    multiplier=(cols/utils.time_steps)+((cols%utils.time_steps) > 0)
    pad=utils.time_steps*multiplier - cols
    padded_feats=np.pad(features,((0,0),(0,pad)),'constant',constant_values=0)

    #create segments
    seg_features=np.hsplit(padded_feats,multiplier)
    contiguous= len(seg_features)
    split_size=utils.time_steps
    offset=utils.offset
    random_wins=[]
    for i in range(0,cols,offset):
        if i>0 and i<=(cols-split_size):
            temp=np.random.randint(i-offset,i)
            random_wins.append((temp,temp+split_size))
            seg_features.append(padded_feats[:,temp:temp+split_size])

    return seg_features,pad,contiguous,random_wins


def silence_intervals(file_path,file_name):
    """
    returns two lists of start and end times
    """
    nsil_start_time=[]
    nsil_end_time=[]
    sil_start_time=[]
    sil_end_time=[]
    #read file 
    audio, sample_rate = librosa.load(os.path.join(file_path,file_name))
    
    #silence extraction using librosa
    nsil_intv=librosa.effects.split(audio, top_db=30).astype('float32') / sample_rate
    
    #silence extraction using pyAudioanalysis
    # [Fs, x] = aIO.readAudioFile(os.path.join(file_path,file_name))
    # nsil_intv = np.array(aS.silenceRemoval(x, Fs, 0.020, 0.020, smoothWindow = 0.7, Weight = 0.3, plot = False))
    # print "non-sil segments="+str(nsil_intv)

    #silence detection using webrtcvad (voice activity detection)
    #nsil_intv=np.array(vad_webrtcvad(file_path,file_name))


    dur=librosa.get_duration(y=audio, sr=sample_rate)
    print nsil_intv
    print dur
    print sample_rate
    curr_sil_start=0.0
    curr_sil_end=0.0
    for i in range(nsil_intv.shape[0]):
        nsil_start_time.append(nsil_intv[i][0])
        #sil_start_time=list(np.array(sil_start_time)/sample_rate)

        nsil_end_time.append(nsil_intv[i][1])
        #sil_end_time=list(np.array(sil_end_time)/sample_rate)

    for i in range(len(nsil_start_time)):
        curr_sil_end=nsil_start_time[i]
        sil_start_time.append(str(curr_sil_start))
        sil_end_time.append(str(curr_sil_end))
        curr_sil_start=nsil_end_time[i]

    print sil_start_time
    print sil_end_time
    return sil_start_time,sil_end_time
