hidden_dim=128
num_layers=3
log_interval=10
test_interval=10
ckpt_interval=2
batch_size=128
epsilon=0.00001
input_dim=40
time_steps=201
offset=100    # used to shift window while testing time_steps/2 works well

model_dir='./models'
model_name='ckpt40_mfcc_switchb_2conv_l2-146'
sl_clsf_model_name='nw_silence_clf_xgb.pkl'
