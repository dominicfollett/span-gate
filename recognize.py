#!/usr/bin/env python

from pathlib import Path

import pickle
import openface
import zerorpc

home = str(Path.home())

# Open NN and trained classifier.
align = openface.AlignDlib("{}/openface/models/dlib/shape_predictor_68_face_landmarks.dat".format(home))
net = openface.TorchNeuralNet("{}/openface/models/openface/nn4.small2.v1.t7".format(home), imgDim=96, cuda=False)
le, clf = pickle.load(open('./lib/generated-embeddings/classifier.pkl', 'rb'), encoding='latin1')

class Recognize():

    def __init__(self):
        pass

    def ping(self):
        return True

    def infer(self, img, verbose=False):
        #print("\n=== {} ===".format(img))
        start = time.time()

        # Align the face:
        alignedFace = align.align(96, img, None,
            landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
        
        if alignedFace is None:
            print("Unable to align image.")
            return None
        if verbose:
            print("Alignment took {} seconds.".format(time.time() - start))

        start = time.time()
        r = net.forward(alignedFace)
        print("Neural network forward pass took {} seconds.".format(time.time() - start))

        # TODO check this
        rep = r.reshape(1, -1)

        start = time.time()
        # Predict who is being seen.
        predictions = clf.predict_proba(rep).ravel()

        # Get person.
        maxI = np.argmax(predictions)
        person = le.inverse_transform(maxI)
        confidence = predictions[maxI]

        if verbose:
            print("Prediction took {} seconds.".format(time.time() - start))
        else:
            # https://github.com/cmusatyalab/openface/issues/274
            print("Predict {} with {:.2f} confidence.".format(person.decode('utf-8'), confidence))
        return person

if __name__ == '__main__':
    print("Starting RPC server.")
    s = zerorpc.Server(Recognize())
    s.bind("tcp://0.0.0.0:4242")
    s.run()