from matplotlib import plt



def plot_sample(x, y, axis):
    img = x.reshape(96, 96)
    axis.imshow(img, cmap='gray')
    if y is not None:
        axis.scatter(y[0::2] * 48 + 48, y[1::2] * 48 + 48, marker='x', s=10)


# plot loss 
def plot_loss(loss):
    """Plot trainig/validation/test loss during training"""

    fig = plt.figure()
    num_data_types = len(loss)
    if num_data_types == 2:
        plt.plot(loss[0], label='train loss')
        plt.plot(loss[1], label='valid loss')
    elif num_data_types == 3:
        plt.plot(loss[0], label='train loss')
        plt.plot(loss[1], label='valid loss')
        plt.plot(loss[2], label='test loss')

        plt.xlabel('epoch')
        plt.ylabel('loss')
        plt.legend(loc='best')
        plt.show()
    return plt


def plot_conv_weights(layer, figsize=(6, 6)):
    """nolearn's plot the weights of a specific layer"""

    fig = plt.figure()
    W = layer.W.get_value()
    shape = W.shape
    nrows = np.ceil(np.sqrt(shape[0])).astype(int)
    ncols = nrows

    for feature_map in range(shape[1]):
        figs, axes = plt.subplots(nrows, ncols, figsize=figsize)

        for ax in axes.flatten():
            ax.set_xticks([])
            ax.set_yticks([])
            ax.axis('off')

        for i, (r, c) in enumerate(product(range(nrows), range(ncols))):
            if i >= shape[0]:
                break
            axes[r, c].imshow(W[i, feature_map], cmap='gray',
                              interpolation='nearest')
    plt.show()
    return plt


def plot_weights(weights):
    fig = pyplot.figure(figsize=(6, 6))
    fig.subplots_adjust(
        left=0, right=1, bottom=0, top=1, hspace=0.05, wspace=0.05)

    for i in range(16):
        ax = fig.add_subplot(4, 4, i + 1, xticks=[], yticks=[])
        ax.imshow(weights[:, i].reshape(96, 96), cmap='gray')
    pyplot.show()




def plot_conv_activity(layer, x, figsize=(6, 8)):
    """nolearn's plot the acitivities of a specific layer.
        x : numpy.ndarray (1 data point) """

    fig = plt.figure()

    # compile theano function
    input_var = T.tensor4('input').astype(theano.config.floatX)
    get_activity = theano.function([input_var], get_output(layer, input_var))

    # get activation info
    activity = get_activity(x)

    # reshape 
    shape = activity.shape
    nrows = np.ceil(np.sqrt(shape[1])).astype(int)
    ncols = nrows

    figs, axes = plt.subplots(nrows + 1, ncols, figsize=figsize)
    axes[0, ncols // 2].imshow(1 - x[0][0], cmap='gray', interpolation='nearest')
    axes[0, ncols // 2].set_title('original')

    for ax in axes.flatten():
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('off')

    for i, (r, c) in enumerate(product(range(nrows), range(ncols))):
        if i >= shape[1]:
            break
        ndim = activity[0][i].ndim
        if ndim != 2:
            raise ValueError("Wrong number of dimensions, image data should "
                             "have 2, instead got {}".format(ndim))
        axes[r + 1, c].imshow(-activity[0][i], cmap='gray',
                              interpolation='nearest')
    plt.show()
    return plt


def occlusion_heatmap(net, x, target, square_length=7):
    """An occlusion test that checks an image for its critical parts.
    In this function, a square part of the image is occluded (i.e. set
    to 0) and then the net is tested for its propensity to predict the
    correct label. One should expect that this propensity shrinks of
    critical parts of the image are occluded. If not, this indicates
    overfitting.
    Depending on the depth of the net and the size of the image, this
    function may take awhile to finish, since one prediction for each
    pixel of the image is made.
    Currently, all color channels are occluded at the same time. Also,
    this does not really work if images are randomly distorted by the
    batch iterator.
    See paper: Zeiler, Fergus 2013
    Parameters
    ----------
    net : NeuralNet instance
      The neural net to test.
    x : np.array
      The input data, should be of shape (1, c, x, y). Only makes
      sense with image data.
    target : int
      The true value of the image. If the net makes several
      predictions, say 10 classes, this indicates which one to look
      at.
    square_length : int (default=7)
      The length of the side of the square that occludes the image.
      Must be an odd number.
    Results
    -------
    heat_array : np.array (with same size as image)
      An 2D np.array that at each point (i, j) contains the predicted
      probability of the correct class if the image is occluded by a
      square with center (i, j).
    """
    if (x.ndim != 4) or x.shape[0] != 1:
        raise ValueError("This function requires the input data to be of "
                         "shape (1, c, x, y), instead got {}".format(x.shape))
    if square_length % 2 == 0:
        raise ValueError("Square length has to be an odd number, instead "
                         "got {}.".format(square_length))

    num_classes = get_output_shape(net.layers_[-1])[1]
    img = x[0].copy()
    bs, col, s0, s1 = x.shape

    heat_array = np.zeros((s0, s1))
    pad = square_length // 2 + 1
    x_occluded = np.zeros((s1, col, s0, s1), dtype=img.dtype)
    probs = np.zeros((s0, s1, num_classes))

    # generate occluded images
    for i in range(s0):
        # batch s1 occluded images for faster prediction
        for j in range(s1):
            x_pad = np.pad(img, ((0, 0), (pad, pad), (pad, pad)), 'constant')
            x_pad[:, i:i + square_length, j:j + square_length] = 0.
            x_occluded[j] = x_pad[:, pad:-pad, pad:-pad]
        y_proba = net.predict_proba(x_occluded)
        probs[i] = y_proba.reshape(s1, num_classes)

    # from predicted probabilities, pick only those of target class
    for i in range(s0):
        for j in range(s1):
            heat_array[i, j] = probs[i, j, target]
    return heat_array



def plot_occlusion(net, X, target, square_length=7, figsize=(9, None)):
    """Plot which parts of an image are particularly import for the
    net to classify the image correctly.
    See paper: Zeiler, Fergus 2013
    Parameters
    ----------
    net : NeuralNet instance
      The neural net to test.
    X : numpy.array
      The input data, should be of shape (b, c, 0, 1). Only makes
      sense with image data.
    target : list or numpy.array of ints
      The true values of the image. If the net makes several
      predictions, say 10 classes, this indicates which one to look
      at. If more than one sample is passed to X, each of them needs
      its own target.
    square_length : int (default=7)
      The length of the side of the square that occludes the image.
      Must be an odd number.
    figsize : tuple (int, int)
      Size of the figure.
    Plots
    -----
    Figure with 3 subplots: the original image, the occlusion heatmap,
    and both images super-imposed.
    """
    return _plot_heat_map(net, X, figsize, lambda net, X, n: occlusion_heatmap(net, X, target[n], square_length))
