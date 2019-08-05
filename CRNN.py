import tensorflow as tf
import pickle as pkl
import tensorflow.contrib.eager as tfe
import tensorflow.contrib.cudnn_rnn as cudnn_rnn
from tensorflow.contrib.layers import batch_norm
import gc
import time
import numpy as np


################ Model to be used with MFCC 40 #######################

class Model(tf.keras.Model):
    """
    CRNN Model for umm detection in speech segments
    Network structure is inspired by Cakir et. al. (https://arxiv.org/pdf/1702.06286.pdf)
    """
    def __init__(self,hidden_dim,num_layers,input_dim):
        super(Model, self).__init__()

        #conv_maxpool
        self._input_shape=[-1,input_dim,201,1]

        self.conv1=tf.layers.Conv2D(filters=32,kernel_size=8, padding='same')
        self.freq_maxpool1=tf.layers.MaxPooling2D((5,1),(5,1),
                                                   padding='valid')  

        self.conv2=tf.layers.Conv2D(filters=64,kernel_size=4, padding='same')
        self.freq_maxpool2 = tf.layers.MaxPooling2D((4, 1), (4, 1),
                                                     padding='valid')  

        self.conv3=tf.layers.Conv2D(filters=64,kernel_size=4, padding='same')
        self.freq_maxpool3 = tf.layers.MaxPooling2D((2, 1), (2, 1),
                                                     padding='valid')  


        self.freq_avgpool1 = tf.layers.AveragePooling2D((8, 1), (4, 1),
                                                        padding='valid')  
        self.freq_avgpool2 = tf.layers.AveragePooling2D((8, 1), (8, 1),
                                                        padding='valid')  

        #gru units
        self.grucells=self._add_cells([tf.contrib.rnn.GRUCell(num_units=hidden_dim) for _ in range(num_layers)])   #TODO: use dropoutwrapper

        self.rnn=tf.contrib.rnn.MultiRNNCell(self.grucells)

        #feedforward
        self.fc1 = tf.layers.Dense(100, activation=tf.nn.relu)
        self.fcf = tf.layers.Dense(2)

    def __call__(self, inputs,training):
        """
        :param inputs: represents a batch of input features [batch,freq_dim=input_dim,timesteps=201,channels=1]
        :param training: boolean representing it's a training phase or not
        :return: logits tensor with shape [batch,2,201]
        """
        y=tf.reshape(inputs,self._input_shape)
        y=tf.cast(y,tf.float32)

        y=self.conv1(y)
        y = tf.nn.relu(y)
        y=self.freq_maxpool1(y)
        if training:
            y=tf.nn.dropout(y,keep_prob=0.75)

        y=self.conv2(y)
        y = tf.nn.relu(y)
        y=self.freq_maxpool2(y)
        if training:
            y=tf.nn.dropout(y,keep_prob=0.75)

        # Stack y in freq dimension  input dimension: [batch,freq_dim,timesteps=201,channels]
                                    #output dimension: [batch,(freq_dim* channels),timesteps=201]
        #NHWC -> NCHW
        y=tf.transpose(y,[0,3,1,2])
        #[N,C,H,W] -> [N,(C*H),W]
        N,C,H,W=y.get_shape().as_list()
        y=tf.reshape(y,[N,(C*H),W])

        # Feed to GRU input:[batch,sequence,timesteps] expected_input to GRU cells: [batch,sequence]*timesteps
        y=tf.unstack(y,axis=2)    # -> returns list of [batch_size,sequence] of size timesteps
        rnn_outs,final_state=tf.nn.static_rnn(self.rnn,y,dtype=tf.float32)   #-> rnn_outs: timestep list of outputs  final_state:
        y=tf.stack(rnn_outs,axis=1)   # ->  [batch,timesteps,hidden_dim]

        y=self.fc1(y)                 # ->  [batch,timesteps, 100]
        if training:
            y=tf.nn.dropout(y,keep_prob=0.5)

        y=self.fcf(y)                 # -> [batch, timesteps, 2]
        y=tf.transpose(y,[0,2,1])
        if not training:
            y=tf.nn.softmax(y,axis=1)

        return y

    def _add_cells(self, cells):
        # "Magic" required for keras.Model classes to track all the variables in
        # a list of tf.layers.Layer objects.
        for i, c in enumerate(cells):
            setattr(self, "cell-%d" % i, c)
        return cells
