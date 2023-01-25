# Fall detection based on pose estimation
Detect falls in CCTV cameras using **[Openpose](https://github.com/CMU-Perceptual-Computing-Lab/openpose)**.

falls can be recognized by analyzing the acceleration and duration of certain human poses. Detection can be run over several cameras simultaneously.

## Fall Record Dataset

Deteced falls will be recorded, and can be reviewed by clicking the records on bottom-right window.

On the top-right side of the window, there is a search box that can be used to seach falls across the fall records database by specifying the location and the time of falls.


## Result

https://user-images.githubusercontent.com/41796656/213982817-4c97f43c-8700-4016-87ed-d39ae728061c.mp4

Bacause fall detection is based on 2D images (no depth information), some falls might be hard to identify at a single angle.
