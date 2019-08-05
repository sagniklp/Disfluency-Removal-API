'''
This file serves as the api to receive 
the file from the user-end as http request
sends the segmentation results as http response.
'''
import os
import web
import random
import json
import wave
import umm_seg
import numpy as np
import silence_classf
import csv
import librosa

# the full path to current dir, this is required to load the assets
dir_=os.path.abspath('.')+'/'
	
urls = (
	'/getaudio' , 'get_audio_file',
	'/curr_audio.wav' , 'send_audio_curr',
	'/sample_1.wav' , 'send_audio_sample1',
	'/sample_2.wav' , 'send_audio_sample2',
	'/sample_3.wav' , 'send_audio_sample3',
	'/sample_4.wav' , 'send_audio_sample4',
	'/getsample' , 'get_sample_file'
)

app = web.application(urls, globals())

class get_sample_file:
	def GET(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')

		return "GET Success"

	def POST(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')
		data=web.input()

		start_time=[]
		end_time=[]
		sil_start_time=[]
		sil_end_time=[]

		if data.type=='audio/mpeg':
			wf=open(dir_+'storage/'+str(data.url)[-6:]+'.mp3','wb')
			wf.write(data.file)
			wf.close()

		elif data.type=='audio/wav':
			#read sample and create a copy
			sample_name=data.filename
			sf=open(dir_+'storage/'+sample_name,'rb')
			wav_bytes=sf.read()

			file_name='curr.wav'
			wf=open(dir_+'storage/'+file_name,'wb')
			wf.write(wav_bytes)
			wf.close()
			print "audio received ..."

			# make single channel [uncomment if passing dual channel audio]
			#silence_classf.make_one_channel(dir_+'storage',file_name)

			# call voice separation required coz due to ambient noise the silence detection doesn't work properly
			#new_fn_bg,new_fn_fg=silence_classf.vocal_separation(dir_+'storage',file_name)
			#sil_file_name=new_fn_fg

			# call umm segmentation
			feats,X,sample_rate=umm_seg.feat_ext(dir_+'storage',file_name)
			seg_feats,pad,contiguous,rand_wins=umm_seg.segment_feat(feats)
			seg_feats=np.array(seg_feats)
			time_segments=umm_seg.call_umm_segmentation(seg_feats,pad,contiguous,rand_wins)
			
			#print time_segments_temp
			if len(time_segments) == 0:
				start_time.append(0.0)
				end_time.append(0.0)
			else:
				# return list of start and end times
				for segment in time_segments:
					start_time.append(segment[0]/1000.0)
					end_time.append(segment[1]/1000.0)

			## get silence segments
			sil_start_time, sil_end_time=umm_seg.silence_intervals(dir_+'storage',file_name)
			

			## check if a silence is adjacent to a filler then extend boundaries to merge them
			for idx1 in range(len(start_time)):
				for idx2 in range(len(sil_start_time)):
					if start_time[idx1]-float(sil_end_time[idx2]) < 0.3 and start_time[idx1]-float(sil_end_time[idx2]) >= 0:
						sil_end_time[idx2]=str(start_time[idx1])
					elif float(sil_start_time[idx2])-end_time[idx1] < 0.3 and float(sil_start_time[idx2])-end_time[idx1]>= 0:	
						sil_start_time[idx2]=str(end_time[idx1])
			#print disf_sil_start_time
			
			print "Going to classify silences.."
			##call silence classfication for visualization
			disf_sil_start_time, disf_sil_end_time =silence_classf.classify_intervals(dir_+'storage',file_name, sil_start_time, sil_end_time)
			
			print "Done silence classification.. going into silencing fillers"
			#deleting fillers
			silence_classf.silence_fillers(dir_+'storage',file_name,start_time,end_time,sil_start_time,sil_end_time)

			print "Going to reduce silences.."
			#reduce silences
			sil_start_time,sil_end_time,disf_sil_start_time, disf_sil_end_time=silence_classf.reduce_silences(dir_+'storage',file_name)

			print "Final post-processing (increasing volume etc.)"
			#enhance
			silence_classf.enhancement(dir_+'storage',file_name)

			
			return json.dumps({'msg':"Your file is uploaded!",
			'start_time':start_time,'end_time':end_time, 
			'sil_start_time':sil_start_time, 
			'sil_end_time':sil_end_time,
			'disf_sil_start_time':disf_sil_start_time, 
			'disf_sil_end_time':disf_sil_end_time,
			})

	def OPTIONS(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')
		return "OPTIONS Success"

class send_audio_curr:

	def GET(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')

		return open(dir_+'storage/ano_new_curr.wav','rb')

class send_audio_sample1:

	def GET(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')

		return open(dir_+'storage/ano_sample_1.wav','rb')

class send_audio_sample2:

	def GET(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')

		return open(dir_+'storage/ano_sample_2.wav','rb')

class send_audio_sample3:

	def GET(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')

		return open(dir_+'storage/ano_sample_3.wav','rb')

class send_audio_sample4:

	def GET(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')

		return open(dir_+'storage/ano_sample_4.wav','rb')


class get_audio_file:


	def GET(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')

		return "GET Success"

	def POST(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')
		data=web.input()

		start_time=[]
		end_time=[]
		sil_start_time=[]
		sil_end_time=[]

		if data.type=='audio/mpeg':
			wf=open(dir_+'storage/'+str(data.url)[-6:]+'.mp3','wb')
			wf.write(data.file)
			wf.close()

		elif data.type=='audio/wav':

			print("\n\n\n",data.url)
			file_name=str(data.url)[-6:]+'.wav'
		
			print("Trying to load now")
			#file_name='curr.wav'
			wf=open(dir_+'storage/'+file_name,'wb')
			wf.write(data.file)
			wf.close()
			print "audio received ..."

			# make single channel [uncomment if passing dual channel audio]
			#silence_classf.make_one_channel(dir_+'storage',file_name)

			# call voice separation required coz due to ambient noise the silence detection doesn't work properly
			#new_fn_bg,new_fn_fg=silence_classf.vocal_separation(dir_+'storage',file_name)
			#sil_file_name=new_fn_fg

			# call umm segmentation
			feats,X,sample_rate=umm_seg.feat_ext(dir_+'storage',file_name)
			seg_feats,pad,contiguous, rand_wins=umm_seg.segment_feat(feats)
			seg_feats=np.array(seg_feats)
			time_segments=umm_seg.call_umm_segmentation(seg_feats,pad,contiguous,rand_wins)
			
			if len(time_segments) == 0:
				start_time.append(0.0)
				end_time.append(0.0)
			else:
				# return list of start and end times
				for segment in time_segments:
					start_time.append(segment[0]/1000.0)
					end_time.append(segment[1]/1000.0)

			## get silence segments
			sil_start_time, sil_end_time=umm_seg.silence_intervals(dir_+'storage',file_name)

			## check if a silence is adjacent to a filler then extend boundaries to merge them
			for idx1 in range(len(start_time)):
				for idx2 in range(len(sil_start_time)):
					if start_time[idx1]-float(sil_end_time[idx2]) < 0.3 and start_time[idx1]-float(sil_end_time[idx2]) >= 0:
						sil_end_time[idx2]=str(start_time[idx1])
					elif float(sil_start_time[idx2])-end_time[idx1] < 0.3 and float(sil_start_time[idx2])-end_time[idx1]>= 0:	
						sil_start_time[idx2]=str(end_time[idx1])
			#print disf_sil_start_time
			
			print "Going to classify silences.."
			##call silence classfication for visualization
			disf_sil_start_time, disf_sil_end_time =silence_classf.classify_intervals(dir_+'storage',file_name, sil_start_time, sil_end_time)
			
			print "Done silence classification.. going into silencing fillers"
			#deleting fillers
			silence_classf.silence_fillers(dir_+'storage',file_name,start_time,end_time,sil_start_time,sil_end_time)

			print "Going to reduce silences.."
			#reduce silences
			sil_start_time,sil_end_time,disf_sil_start_time, disf_sil_end_time=silence_classf.reduce_silences(dir_+'storage',file_name)

			print "Final post-processing (increasing volume etc.)"
			#enhance
			silence_classf.enhancement(dir_+'storage',file_name)


			return json.dumps({'msg':"Your file is uploaded!",
			'start_time':start_time,'end_time':end_time, 
			'sil_start_time':sil_start_time, 
			'sil_end_time':sil_end_time,
			'disf_sil_start_time':disf_sil_start_time, 
			'disf_sil_end_time':disf_sil_end_time,
			})

	def OPTIONS(self):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		web.header('Access-Control-Allow-Methods',  'POST, GET, OPTIONS')
		return "OPTIONS Success"


if __name__ == "__main__":
	app.run()
