# Disfluency Removal API
Disfluency Detection, Removal and Correction following the paper:
**[Increase Apparent Public Speaking Fluency By Speech Augmentation](https://arxiv.org/abs/1812.03415)** 
* **To run:**
    - `python audio_receiver_remover.py 7777`
    - `7777` is the <port_number> to host the API
    - Open the `index.html` in Chrome/Firefox 
    - Navigate to the tool & use the samples! 

* **If you change the <port_number>**
    - Go to `/js/vis.js` and replace all `http://localhost:7777/` with `http://localhost:<new_port_number>/`
* **Required Packages:**
    - web.py
    - librosa
    - tensorflow-gpu (>=1.5)
    - pydub
    - pyAudioAnalysis
    - soundfile
    - h5py
    - scipy
    - numpy
    - sklearn
    - pickle

### Citation
If you use our tool please consider citing our paper:
```
@inproceedings{das2019increase,
  title={Increase Apparent Public Speaking Fluency by Speech Augmentation},
  author={Das, Sagnik and Gandhi, Nisha and Naik, Tejas and Shilkrot, Roy},
  booktitle={ICASSP 2019-2019 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)},
  pages={6890--6894},
  year={2019},
  organization={IEEE}
}
```
### Contact
If you have any questions with the code please open an issue. Thanks.
Sagnik Das- sadas@cs.stonybrook.edu
