# import the necessary packages
from scipy.spatial import distance as dist
from imutils.video import FileVideoStream
from imutils.video import VideoStream
from imutils import face_utils
import argparse
import imutils
import time
import dlib
import cv2



import pyfirmata
#import time

board = pyfirmata.Arduino('COM15')     # use your arduino COM port
video_capture = cv2.VideoCapture(0)

def eye_aspect_ratio(eye):
        # compute the euclidean distances between the two sets of
        # vertical eye landmarks (x, y)-coordinates
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])

        # compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        C = dist.euclidean(eye[0], eye[3])

        # compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)

        # return the eye aspect ratio
        return ear
 
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--shape-predictor",default="shape_predictor_68_face_landmarks.dat",
        help="path to facial landmark predictor")
ap.add_argument("-v", "--video", type=str, default="camera",
        help="path to input video file")
ap.add_argument("-t", "--threshold", type = float, default=0.18,  #################  0.252
        help="threshold to determine closed eyes")
ap.add_argument("-f", "--frames", type = int, default=3,     ###################  2
        help="the number of consecutive frames the eye must be below the threshold")

def main() :
    args = vars(ap.parse_args())
    EYE_AR_THRESH = args['threshold']
    EYE_AR_CONSEC_FRAMES = args['frames']

    # initialize the frame counters and the total number of blinks
    COUNTER = 0
    TOTAL = 0

    # initialize dlib's face detector (HOG-based) and then create
    # the facial landmark predictor
    print("[INFO] loading facial landmark predictor...")
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(args["shape_predictor"])
 
    # grab the indexes of the facial landmarks for the left and
    # right eye, respectively
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
    
    # start the video stream thread
    print("[INFO] starting video stream thread...")
    print("[INFO] print q to quit...")
    
    #if args['video'] == "camera":
        #vs = VideoStream(src=0).start()
        #fileStream = False
    #else:
        #vs = FileVideoStream(args["video"]).start()
        #fileStream = True
    ret, frame = video_capture.read()
    time.sleep(1.0)
    
    # loop over frames from the video stream
    while True:
        # if this is a file video stream, then we need to check if
        # there any more frames left in the buffer to process
        #if fileStream and not vs.more():  #######
                #break          ##################
    
        # grab the frame from the threaded video file stream, resize
        # it, and convert it to grayscale
        # channels)

        ret, frame = video_capture.read()
        
        #frame = vs.read()
        frame = imutils.resize(frame, width=800)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
        # detect faces in the grayscale frame
        rects = detector(gray, 0)
    
        # loop over the face detections
        for rect in rects:
                # determine the facial landmarks for the face region, then
                # convert the facial landmark (x, y)-coordinates to a NumPy
                # array
                shape = predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)
    
                # extract the left and right eye coordinates, then use the
                # coordinates to compute the eye aspect ratio for both eyes
                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]
                leftEAR = eye_aspect_ratio(leftEye)
                rightEAR = eye_aspect_ratio(rightEye)
    
                # average the eye aspect ratio together for both eyes
                ear = (leftEAR + rightEAR) / 2.0
    
                # compute the convex hull for the left and right eye, then
                # visualize each of the eyes
                leftEyeHull = cv2.convexHull(leftEye)
                rightEyeHull = cv2.convexHull(rightEye)
                cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
    
                # check to see if the eye aspect ratio is below the blink
                # threshold, and if so, increment the blink frame counter
                start=0
                stop=0
                if ear < EYE_AR_THRESH:
                        COUNTER += 1
                        board.digital[13].write(1)
                        
                stop = time.time()
                
                        
    
                # otherwise, the eye aspect ratio is not below the blink
                # threshold
                if ear > EYE_AR_THRESH:
                        # if the eyes were closed for a sufficient number of
                        # then increment the total number of blinks
                        if COUNTER >= EYE_AR_CONSEC_FRAMES:
                                TOTAL += 1
                                board.digital[13].write(0)
                               
    
                        # reset the eye frame counter
                        COUNTER = 0
    
                # draw the total number of blinks on the frame along with
                # the computed eye aspect ratio for the frame
                cv2.putText(frame, "Blink of eye: {}".format(TOTAL), (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
     
        # show the frame
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
     
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
                break
    
    # do a bit of cleanup
    video_capture.release()
    cv2.destroyAllWindows()
    #board.digital[13].write(0)
    #vs.stop()
if __name__ == '__main__' :
    main()
