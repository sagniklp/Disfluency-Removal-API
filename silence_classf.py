####
import os
import numpy as np
import pickle 
import scipy
import random
import array

from sklearn.preprocessing import StandardScaler
from sklearn.externals import joblib

import librosa
from pydub import AudioSegment
import soundfile as sf

import umm_seg
import utils


def make_one_channel(file_path,file_name):
	track=AudioSegment.from_file(os.path.join(file_path,file_name))
	track=track.set_channels(1)
	track=track.set_frame_rate(22050)
	track.export(os.path.join(file_path,file_name))

def extract_feature(X,sample_rate,num_mfcc=40):
	stft = np.abs(librosa.stft(X))
	mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=num_mfcc).T,axis=0)
	chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T,axis=0)
	mel = np.mean(librosa.feature.melspectrogram(X, sr=sample_rate).T,axis=0)
	contrast = np.mean(librosa.feature.spectral_contrast(S=stft, sr=sample_rate).T,axis=0)
	tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(X),
	sr=sample_rate).T,axis=0)
	return [mfccs,chroma,mel,contrast,tonnetz]


def append_zeros(in_features):
	max_len = 128
	features = np.array(in_features)
	
	final_features = []
	for feature in features:
		#print feature
		temp_feature = []
		for i in range(len(feature)):
			f=feature[i]
			if i==0:
				temp = np.zeros(max_len)
				temp[:len(f)] = f
				temp_feature.append(temp)
		final_features.append(temp_feature)
	
	final = np.reshape(np.array(final_features),(len(final_features),-1))
	scaler = StandardScaler()
	final=scaler.fit_transform(final)
	print final.shape
	return final    


def load_audio_segments(file_path, file_name, sil_start_time, sil_end_time):
	segs=[]
	#get max dur
	track=AudioSegment.from_file(os.path.join(file_path,file_name))
	total_dur=track.duration_seconds
	#sr=track.frame_rate
	all_seg, sr = librosa.load(os.path.join(file_path,file_name))
	for idx in range(len(sil_start_time)):
		start_time=float(sil_start_time[idx])-0.5
		end_time=float(sil_end_time[idx])+0.5
		start_idx=librosa.time_to_samples(start_time,sr=sr)[0]
		end_idx=librosa.time_to_samples(end_time,sr=sr)[0]
		seg=all_seg[start_idx:end_idx]

		if len(seg) > 0:
			segs.append(seg)
	return segs,sr


def classify_intervals(file_path, file_name, sil_start_time, sil_end_time):
	#load_classifier
	svc=joblib.load(os.path.join('./models/',utils.sl_clsf_model_name))
	print "Model loaded.."

	audio_segs,sr=load_audio_segments(file_path, file_name, sil_start_time, sil_end_time)

	print "Segments loaded.."
	all_features=[]

	for seg in audio_segs:
		all_features.append(extract_feature(seg,sr))

	print "Features loaded.."

	all_features=append_zeros(all_features)

	print "Appended zeros.."
	y_pred = list(svc.predict(all_features))
	print y_pred

	new_sil_start_time=[]
	new_sil_end_time=[]

	for idx in range(len(y_pred)):
		if y_pred[idx]==1 and float(sil_end_time[idx])- float(sil_start_time[idx]) > 0.3:
			new_sil_start_time.append(sil_start_time[idx])
			new_sil_end_time.append(sil_end_time[idx])
		elif float(sil_end_time[idx])- float(sil_start_time[idx]) >0.7:
			new_sil_start_time.append(sil_start_time[idx])
			new_sil_end_time.append(sil_end_time[idx])

	print new_sil_start_time
	print new_sil_end_time

	return new_sil_start_time,new_sil_end_time


def vocal_separation(file_path,file_name):
	'''
	Code is borrowed from Librosa examples
	'''
	y, sr = librosa.load(os.path.join(file_path,file_name))
	print "file loaded for vocal"
	# And compute the spectrogram magnitude and phase
	S_full, phase = librosa.magphase(librosa.stft(y))

	# We'll compare frames using cosine similarity, and aggregate similar frames
	# by taking their (per-frequency) median value.
	#
	# To avoid being biased by local continuity, we constrain similar frames to be
	# separated by at least 2 seconds.
	#
	# This suppresses sparse/non-repetetitive deviations from the average spectrum,
	# and works well to discard vocal elements.

	S_filter = librosa.decompose.nn_filter(S_full,
										   aggregate=np.median,
										   metric='cosine',
										   width=int(librosa.time_to_frames(2, sr=sr)))

	# The output of the filter shouldn't be greater than the input
	# if we assume signals are additive.  Taking the pointwise minimium
	# with the input spectrum forces this.
	S_filter = np.minimum(S_full, S_filter)

	# We can also use a margin to reduce bleed between the vocals and instrumentation masks.
	# Note: the margins need not be equal for foreground and background separation
	margin_i, margin_v = 2, 2
	power = 1

	mask_i = librosa.util.softmask(S_filter,
								   margin_i * (S_full - S_filter),
								   power=power)

	mask_v = librosa.util.softmask(S_full - S_filter,
								   margin_v * S_filter,
								   power=power)

	# Once we have the masks, simply multiply them with the input spectrum
	# to separate the components
	S_foreground = mask_v * S_full
	S_background = mask_i * S_full

	#S_modified=S_full-S_foreground

	back_y_fg = librosa.istft(S_foreground)
	back_y_bg = librosa.istft(S_background)
	#modified_y = librosa.istft(S_modified)

	new_fn_bg='output_bg.wav'
	new_fn_fg='output_fg.wav'
	librosa.output.write_wav(os.path.join(file_path,new_fn_fg),back_y_fg,sr)
	librosa.output.write_wav(os.path.join(file_path,new_fn_bg),back_y_bg,sr)

	return new_fn_bg,new_fn_fg


def silence_fillers(file_path,file_name,start_time,end_time,sil_start_time,sil_end_time):
	org_track=AudioSegment.from_file(os.path.join(file_path,file_name))
	org_track=org_track.set_frame_rate(22050)
	sample_rate=org_track.frame_rate
	sample_width=org_track.frame_width
	samples = np.array(org_track.get_array_of_samples())
	
	for idx in range(len(start_time)):
		
		pydub_start_t=start_time[idx]*1000		#pydub works in ms
		pydub_end_t=end_time[idx]*1000
		start_sample_id=librosa.time_to_samples(start_time[idx],sr=sample_rate)[0]
		end_sample_id=librosa.time_to_samples(end_time[idx],sr=sample_rate)[0]

		temp_track=AudioSegment.silent(duration=(pydub_end_t-pydub_start_t),frame_rate=sample_rate)
		temp_array= np.array(temp_track.get_array_of_samples())
		samples[start_sample_id:start_sample_id+temp_array.shape[0]]=temp_array
		
		# do a median filtering on samples
		samples[start_sample_id-7:start_sample_id+temp_array.shape[0]+7]=scipy.signal.medfilt(samples[start_sample_id-7:start_sample_id+temp_array.shape[0]+7],kernel_size=3)		

	#to deal with the noise in the silences
	for idx in range(len(sil_start_time)):
		pydub_start_t=float(sil_start_time[idx])*1000		#pydub works in ms
		pydub_end_t=float(sil_end_time[idx])*1000
		start_sample_id=librosa.time_to_samples(float(sil_start_time[idx]),sr=sample_rate)[0]
		end_sample_id=librosa.time_to_samples(float(sil_end_time[idx]),sr=sample_rate)[0]

		temp_track=AudioSegment.silent(duration=(pydub_end_t-pydub_start_t),frame_rate=sample_rate)
		temp_array= np.array(temp_track.get_array_of_samples())
		samples[start_sample_id:start_sample_id+temp_array.shape[0]]=temp_array

		# do a median filtering on samples
		samples[start_sample_id-7:start_sample_id+temp_array.shape[0]+7]=scipy.signal.medfilt(samples[start_sample_id-7:start_sample_id+temp_array.shape[0]+7],kernel_size=3)

	sf.write(os.path.join(file_path,'new_'+file_name),samples.astype('int16'),sample_rate)


def reduce_silences(file_path,file_name):
	#do a bandpass 50Hz to 8Khz
	org_track=AudioSegment.from_file(os.path.join(file_path,'new_'+file_name))
	samples = np.array(org_track.get_array_of_samples())
	hpass_track=org_track.high_pass_filter(300)
	lpass_track=hpass_track.low_pass_filter(3000)
	lpass_track.export(os.path.join(file_path,'new_'+file_name), format="wav")

	#read file 
	X, sample_rate = librosa.load(os.path.join(file_path,'new_'+file_name))
	# print '#######'+str(X.shape)

	#get_new_silences because we added silences at fillers
	sil_start_time, sil_end_time=umm_seg.silence_intervals(file_path,'new_'+file_name)

	##call silence classfication
	disf_sil_start_time, disf_sil_end_time =classify_intervals(file_path,'new_'+file_name, sil_start_time, sil_end_time)

	#get a histogram of silences
	disf_start_time=[float(x) for x in disf_sil_start_time]
	disf_end_time=[float(x) for x in disf_sil_end_time]
	start_time=[float(x) for x in sil_start_time]
	end_time=[float(x) for x in sil_end_time]

	#find out the fluent silences
	fluent_sil_start_time=list(set(start_time)-set(disf_start_time))
	fluent_sil_end_time=list(set(end_time)-set(disf_end_time))
	fluent_sil_end_time.sort()
	fluent_sil_start_time.sort()

	#find fluent silence times
	intv= np.array(fluent_sil_end_time)-np.array(fluent_sil_start_time)
	hist,bins=np.histogram(intv)
	#take median of the bins
	optimal_sil_dur= np.median(bins)

	del_start_sample_id=[]
	del_end_sample_id=[]

	# make all the disflent silences of optimal_sil_dur	
	for idx in range(len(disf_sil_start_time)):
		del_start_time=float(disf_sil_start_time[idx])+(optimal_sil_dur/2)
		del_end_time=float(disf_sil_end_time[idx])-(optimal_sil_dur/2)
		del_start_sample_id.append(librosa.time_to_samples(del_start_time,sr=sample_rate)[0])
		del_end_sample_id.append(librosa.time_to_samples(del_end_time,sr=sample_rate)[0])

	#also check for other silences which are more than optimal silence dur
	for idx in range(len(fluent_sil_start_time)):
		if float(fluent_sil_end_time[idx])-float(fluent_sil_start_time[idx])>optimal_sil_dur:
			del_start_time=float(fluent_sil_start_time[idx])+(optimal_sil_dur/2)
			del_end_time=float(fluent_sil_end_time[idx])-(optimal_sil_dur/2)
			del_start_sample_id.append(librosa.time_to_samples(del_start_time,sr=sample_rate)[0])
			del_end_sample_id.append(librosa.time_to_samples(del_end_time,sr=sample_rate)[0])

	del_start_sample_id.sort()
	del_end_sample_id.sort()

	print X.shape
	new_X=np.zeros((1,))
	curr_start=0
	curr_end=0
	for idx in range(len(del_start_sample_id)):
		curr_end=del_start_sample_id[idx]
		new_X=np.concatenate((new_X,X[curr_start:curr_end,]))
		curr_start=del_end_sample_id[idx]

	#add the final one
	new_X=np.concatenate((new_X,X[curr_start:,]))

	#librosa doesn't work https://github.com/librosa/librosa/issues/640
	#use pysoundfile
	sf.write(os.path.join(file_path,'new_'+file_name),new_X[1:],sample_rate)
	return sil_start_time, sil_end_time, disf_sil_start_time, disf_sil_end_time


def enhancement(file_path,file_name):
	audio,sr=librosa.load(os.path.join(file_path,'new_'+file_name))
	shift=0
	while shift in [0,1,-1]:
		shift=random.randint(-4,4)
	shifted=librosa.effects.pitch_shift(audio, sr, n_steps=shift)
	librosa.output.write_wav(os.path.join(file_path,'ano_new_'+file_name), shifted, sr)
