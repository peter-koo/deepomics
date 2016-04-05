#/bin/python

import numpy as np
import theano
import theano.tensor as T
from lasagne.layers import BatchNormLayer, ParametricRectifierLayer, NonlinearityLayer
from lasagne.nonlinearities import sigmoid, rectify, softmax
from lasagne.init import GlorotUniform, Constant
from lasagne.objectives import binary_crossentropy, categorical_crossentropy
from lasagne.updates import nesterov_momentum, adagrad, rmsprop, total_norm_constraint, sgd, adam
from lasagne.regularization import l1, l2 

def simple_genome_motif_model(shape, num_labels):

	input_var = T.tensor4('inputs')
	target_var = T.ivector('targets')

    # create model
	layer1 = {'layer': 'input',
	          'input_var': input_var,
	          'shape': shape}
	layer2 = {'layer': 'convolution', 
	          'num_filters': 200, 
	          'filter_size': (8, 1),
	          'W': GlorotUniform(),
	          'b': None,
	          'norm': 'batch', 
	          'activation': 'prelu',
	          'pool_size': (4, 1)}
	layer3 = {'layer': 'convolution', 
	          'num_filters': 200, 
	          'filter_size': (8, 1),
	          'W': GlorotUniform(),
	          'b': None,
	          'dropout': .2,
	          'norm': 'batch', 
	          'activation': 'prelu',
	          'pool_size': (4, 1)}
	layer4 = {'layer': 'dense', 
	          'num_units': 200, 
	          'default': True,
	          'W': GlorotUniform(),
	          'b': Constant(0.05), 
	          'dropout': .5,
	          'norm': 'batch',
	          'activation': 'prelu'}
	layer5 = {'layer': 'dense', 
	          'num_units': num_labels, 
	          'default': True,
	          'W': GlorotUniform(),
	          'b': Constant(0.05),
	          'activation': softmax}

	layers = [layer1, layer2, layer3, layer4, layer5]

	# optimization parameters
	optimization = {"objective": "categorical",
                "optimizer": "nesterov_momentum", 
                "learning_rate": 0.1,
                "weight_norm": 5,
                "l1": 1e-7,
                "l2": 1e-8, 
                "momentum": 0.9
                }


	return layers, input_var, target_var, optimization
