import cv2

def saveImage(image,index):
    filename='images/{:04d}.jpg'.format(index)
    cv2.imwrite(filename,image)
    print(filename)
cap=cv2.VideoCapture('videos/fateUBW02.mp4')
cv2.namedWindow('video',cv2.WINDOW_NORMAL)
# ratio=cap.get(cv2.CAP_PROP_FRAME_WIDTH)/cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

n=1
idx=1
max_idx=50000
# WIDTH=854
# HEIGHT=int(WIDTH/ratio)

while n>0:
    ret,frame=cap.read()
    # frame=cv2.resize(frame,(WIDTH,HEIGHT))
    if n%12==0:
        saveImage(frame,idx)
        idx+=1
        if idx>= max_idx:
            print('get training data done')
            n=-1
            break
    n+=1
    cv2.imshow('video',frame)
    cv2.waitKey(1)

